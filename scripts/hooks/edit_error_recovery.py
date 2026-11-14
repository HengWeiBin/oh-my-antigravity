from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from typing import Any

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult, LifecycleEvent

DIAGNOSTIC_WARNING_TEMPLATE = (
    "[EditErrorRecovery] Surgical edit failed on '{target_file}'. "
    "STOP guessing line numbers or context strings. "
    "You MUST call 'view_file' (or 'read_file') on this file before attempting any further edits."
)

LOCK_DENIAL_REASON_TEMPLATE = (
    "STOP. A prior surgical edit on this file failed. "
    "Repeated blind edits or writes without inspecting the file are prohibited to prevent guessing loops. "
    "You MUST call 'view_file' on '{target_file}' (or 'read_file') to inspect its current content before attempting any further edits or writes."
)

TARGET_FILE_KEYS = (
    "TargetFile",
    "target_file",
    "Path",
    "path",
    "file_path",
    "filePath",
    "targetFile",
    "AbsolutePath",
    "absolute_path",
)


def extract_target_file(tool_input: dict[str, Any]) -> str | None:
    """Extract target file path from tool input dictionary across supported naming styles."""
    if not isinstance(tool_input, dict):
        return None
    for key in TARGET_FILE_KEYS:
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().strip("'\"")
    return None


def normalize_path(path: str, cwd: str | None = None) -> str:
    """Normalize file path for consistent cross-platform matching."""
    if not path:
        return ""
    p = path.strip().strip("'\"")
    if p.lower().startswith("file:///"):
        p = p[8:]
    elif p.lower().startswith("file://"):
        p = p[7:]

    p = p.replace("\\", "/")
    is_absolute = os.path.isabs(p) or (len(p) > 1 and p[1] == ":")
    if not is_absolute:
        base_dir = cwd if (cwd and cwd.strip()) else ""
        if base_dir:
            p = os.path.normpath(os.path.join(base_dir, p)).replace("\\", "/")
        else:
            p = os.path.normpath(p).replace("\\", "/")
    else:
        p = os.path.normpath(p).replace("\\", "/")

    return p.lower()


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session identifier for safe filename usage."""
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", session_id)
    return sanitized or "default_session"


class SessionEditState:
    """Persistent state tracking for files undergoing edit error locks in a session."""

    def __init__(self, state_dir: str | None = None) -> None:
        self.state_dir = state_dir

    def get_state_dir(self) -> str:
        if self.state_dir:
            os.makedirs(self.state_dir, exist_ok=True)
            return self.state_dir
        env_dir = os.environ.get("ANTIGRAVITY_EDIT_RECOVERY_DIR")
        if env_dir:
            os.makedirs(env_dir, exist_ok=True)
            return env_dir
        default_dir = os.path.join(tempfile.gettempdir(), "antigravity_edit_recovery")
        os.makedirs(default_dir, exist_ok=True)
        return default_dir

    def get_state_file(self, session_id: str) -> str:
        sdir = self.get_state_dir()
        fname = f"{sanitize_session_id(session_id)}.json"
        return os.path.join(sdir, fname)

    def load_state(self, session_id: str) -> dict[str, Any]:
        path = self.get_state_file(session_id)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save_state(self, session_id: str, state: dict[str, Any]) -> None:
        path = self.get_state_file(session_id)
        temp_path = f"{path}.tmp.{os.getpid()}"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)
        except OSError:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            except OSError:
                pass
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

    def lock_file(self, session_id: str, file_path: str, cwd: str | None = None) -> None:
        norm = normalize_path(file_path, cwd=cwd)
        if not norm:
            return
        state = self.load_state(session_id)
        state[norm] = {"raw_path": file_path, "locked": True}
        self.save_state(session_id, state)

    def unlock_file(self, session_id: str, file_path: str, cwd: str | None = None) -> bool:
        norm = normalize_path(file_path, cwd=cwd)
        if not norm:
            return False
        state = self.load_state(session_id)
        if norm in state:
            del state[norm]
            self.save_state(session_id, state)
            return True
        return False

    def is_locked(self, session_id: str, file_path: str, cwd: str | None = None) -> bool:
        norm = normalize_path(file_path, cwd=cwd)
        if not norm:
            return False
        state = self.load_state(session_id)
        entry = state.get(norm)
        if entry is None:
            return False
        if isinstance(entry, dict):
            return bool(entry.get("locked", True))
        return bool(entry)

    def clear(self, session_id: str) -> None:
        path = self.get_state_file(session_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


class EditErrorRecoveryHook(BaseHook):
    """
    Two-tier edit error recovery hook to arrest blind guessing loops:
    - Tier 1 (PostToolUse): Warns when surgical file edits fail and locks the file.
    - Tier 2 (PreToolUse): Blocks repeated blind edits or writes to locked files until viewed.
    """

    def __init__(
        self,
        state: SessionEditState | None = None,
        state_dir: str | None = None,
    ) -> None:
        self.state = state or SessionEditState(state_dir=state_dir)

    @property
    def name(self) -> str:
        return "edit_error_recovery"

    def _get_session_id(self, context: HookContext) -> str:
        cid = (
            context.conversation_id
            or context.raw_payload.get("conversationId")
            or context.raw_payload.get("conversation_id")
        )
        if isinstance(cid, str) and cid.strip():
            return cid.strip()
        if context.cwd:
            return hashlib.sha256(context.cwd.strip().encode("utf-8")).hexdigest()[:16]
        return "default_session"

    def execute(self, context: HookContext) -> HookResult:
        if context.lifecycle == LifecycleEvent.POST_TOOL_USE:
            return self._handle_post_tool_use(context)
        if context.lifecycle == LifecycleEvent.PRE_TOOL_USE:
            return self._handle_pre_tool_use(context)
        return HookResult()

    def _handle_post_tool_use(self, context: HookContext) -> HookResult:
        tool_name = (context.tool_name or "").lower()

        # If a file was successfully inspected via view_file / read_file, unlock it
        if tool_name in (
            "view_file",
            "view_file_outline",
            "view_code_item",
            "read_file",
        ) and not (context.tool_error and context.tool_error.strip()):
            viewed_file = extract_target_file(context.tool_input)
            if viewed_file:
                session_id = self._get_session_id(context)
                self.state.unlock_file(session_id, viewed_file, cwd=context.cwd)
            return HookResult()

        # Monitor surgical edits for failure
        if tool_name in ("replace_file_content", "multi_replace_file_content", "edit_file"):
            has_error = bool(context.tool_error and context.tool_error.strip())
            if has_error:
                target_file = extract_target_file(context.tool_input)
                if target_file:
                    session_id = self._get_session_id(context)
                    self.state.lock_file(session_id, target_file, cwd=context.cwd)
                    warning_msg = DIAGNOSTIC_WARNING_TEMPLATE.format(target_file=target_file)
                    return HookResult(additional_context=warning_msg)

        return HookResult()

    def _handle_pre_tool_use(self, context: HookContext) -> HookResult:
        tool_name = (context.tool_name or "").lower()

        # Unlock when file is inspected via view_file / read_file
        if tool_name in ("view_file", "view_file_outline", "view_code_item", "read_file"):
            viewed_file = extract_target_file(context.tool_input)
            if viewed_file:
                session_id = self._get_session_id(context)
                self.state.unlock_file(session_id, viewed_file, cwd=context.cwd)
            return HookResult(decision="allow")

        # Block repeat edits or writes on locked files
        if tool_name in (
            "replace_file_content",
            "multi_replace_file_content",
            "edit_file",
            "write_to_file",
            "write_file",
        ):
            target_file = extract_target_file(context.tool_input)
            if target_file:
                session_id = self._get_session_id(context)
                if self.state.is_locked(session_id, target_file, cwd=context.cwd):
                    reason = LOCK_DENIAL_REASON_TEMPLATE.format(target_file=target_file)
                    return HookResult(decision="deny", reason=reason)

        return HookResult(decision="allow")
