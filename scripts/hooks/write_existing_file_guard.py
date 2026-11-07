from __future__ import annotations

import json
import os
from typing import Any

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


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
    if cwd and not (os.path.isabs(p) or (len(p) > 1 and p[1] == ":")):
        p = os.path.normpath(os.path.join(cwd, p)).replace("\\", "/")
    else:
        p = os.path.normpath(p).replace("\\", "/")

    return p.lower()


def is_overwrite_requested(tool_input: dict[str, Any]) -> bool:
    """Check if Overwrite is set to True (boolean, case-insensitive string, or number)."""
    val = tool_input.get("Overwrite")
    if val is None:
        val = tool_input.get("overwrite")
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes")
    return False


def is_exempt_path(norm_path: str, raw_payload: dict[str, Any]) -> bool:
    """Check if the given normalized path is exempt from unread overwrite guards."""
    if "/.omo/" in norm_path or norm_path.startswith(".omo/") or norm_path == ".omo":
        return True

    if (
        "/.scratch/" in norm_path
        or "/scratch/" in norm_path
        or norm_path.startswith((".scratch/", "scratch/"))
    ):
        return True

    artifact_dir = raw_payload.get("artifactDirectoryPath")
    brain_dir = raw_payload.get("brainDir") or raw_payload.get("brain_dir")
    exempt_roots = [
        artifact_dir,
        os.path.dirname(artifact_dir) if isinstance(artifact_dir, str) and artifact_dir else None,
        brain_dir,
    ]
    for root in exempt_roots:
        if isinstance(root, str) and root:
            norm_root = normalize_path(root)
            if norm_path == norm_root or norm_path.startswith(norm_root.rstrip("/") + "/"):
                return True

    return False


def find_transcript_paths(context: HookContext) -> list[str]:
    """Resolve candidate transcript.jsonl paths from the execution context."""
    payload = context.raw_payload
    conversation_id = context.conversation_id or payload.get("conversationId") or ""
    artifact_dir = payload.get("artifactDirectoryPath")
    brain_dir = (
        payload.get("brainDir")
        or payload.get("brain_dir")
        or (os.path.dirname(artifact_dir) if isinstance(artifact_dir, str) and artifact_dir else None)
    )

    candidates: list[Any] = [payload.get("transcriptPath")]
    if isinstance(artifact_dir, str) and artifact_dir:
        candidates.append(os.path.join(artifact_dir, ".system_generated", "logs", "transcript.jsonl"))
        if conversation_id:
            candidates.append(os.path.join(artifact_dir, conversation_id, ".system_generated", "logs", "transcript.jsonl"))
    if isinstance(brain_dir, str) and brain_dir and conversation_id:
        candidates.append(os.path.join(brain_dir, conversation_id, ".system_generated", "logs", "transcript.jsonl"))
    if conversation_id:
        home = os.path.expanduser("~")
        candidates.append(
            os.path.join(home, ".gemini", "antigravity", "brain", conversation_id, ".system_generated", "logs", "transcript.jsonl")
        )

    existing: list[str] = []
    for p in candidates:
        if isinstance(p, str) and p:
            norm = os.path.normpath(p)
            if norm not in existing and os.path.isfile(norm):
                existing.append(norm)
    return existing


def extract_tool_calls(obj: Any) -> list[tuple[str, dict[str, Any]]]:
    """Recursively extract (tool_name, tool_args) tuples from transcript JSON structures."""
    calls: list[tuple[str, dict[str, Any]]] = []
    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("toolName") or obj.get("tool_name") or obj.get("tool")
        args = obj.get("args") or obj.get("input") or obj.get("arguments") or obj.get("tool_input")
        if isinstance(name, str):
            if isinstance(args, dict):
                calls.append((name.lower(), args))
            elif isinstance(args, str):
                try:
                    parsed_args = json.loads(args)
                    if isinstance(parsed_args, dict):
                        calls.append((name.lower(), parsed_args))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        tool_calls = obj.get("tool_calls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                calls.extend(extract_tool_calls(tc))

        for k, v in obj.items():
            if k not in ("tool_calls", "args", "input", "arguments", "tool_input") and isinstance(v, (dict, list)):
                calls.extend(extract_tool_calls(v))

    elif isinstance(obj, list):
        for item in obj:
            calls.extend(extract_tool_calls(item))

    return calls


def was_file_inspected_or_written_in_transcript(
    transcript_path: str,
    target_norm: str,
    cwd: str,
) -> bool:
    """Scan transcript.jsonl to determine if target file was read or written earlier."""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except (json.JSONDecodeError, ValueError):
                    continue

                tool_calls = extract_tool_calls(entry)
                for tool_name, args in tool_calls:
                    if tool_name in ("view_file", "write_to_file"):
                        file_val = (
                            args.get("AbsolutePath")
                            or args.get("absolute_path")
                            or args.get("TargetFile")
                            or args.get("target_file")
                            or args.get("path")
                            or args.get("file_path")
                            or args.get("filePath")
                            or args.get("targetFile")
                        )
                        if isinstance(file_val, str) and file_val:
                            norm_called = normalize_path(file_val, cwd=cwd)
                            if norm_called == target_norm:
                                return True
    except OSError:
        pass
    return False


class WriteExistingFileGuardHook(BaseHook):
    """Pre-tool guard preventing blind overwrites of existing non-empty files without prior inspection."""

    @property
    def name(self) -> str:
        return "write_existing_file_guard"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name != "write_to_file":
            return HookResult(decision="allow")

        if not is_overwrite_requested(context.tool_input):
            return HookResult(decision="allow")

        target_file = (
            context.tool_input.get("TargetFile")
            or context.tool_input.get("target_file")
            or context.tool_input.get("path")
            or context.tool_input.get("file_path")
        )
        if not target_file or not isinstance(target_file, str):
            return HookResult(decision="allow")

        cwd = context.cwd or ""
        raw_target = target_file.strip().strip("'\"")
        if os.path.isabs(raw_target) or (len(raw_target) > 1 and raw_target[1] == ":"):
            resolved_target = os.path.normpath(raw_target)
        elif cwd:
            resolved_target = os.path.normpath(os.path.join(cwd, raw_target))
        else:
            resolved_target = os.path.normpath(os.path.abspath(raw_target))

        if not os.path.exists(resolved_target):
            return HookResult(decision="allow")

        try:
            if os.path.getsize(resolved_target) == 0:
                return HookResult(decision="allow")
        except OSError:
            return HookResult(decision="allow")

        norm_target = normalize_path(resolved_target)
        norm_raw = normalize_path(target_file)

        if is_exempt_path(norm_target, context.raw_payload) or is_exempt_path(norm_raw, context.raw_payload):
            return HookResult(decision="allow")

        # Inspect transcript.jsonl for prior view_file or write_to_file
        transcript_paths = find_transcript_paths(context)
        for t_path in transcript_paths:
            if was_file_inspected_or_written_in_transcript(t_path, norm_target, cwd):
                return HookResult(decision="allow")

        reason = (
            "STOP. Overwriting an existing non-empty file without inspecting it first is "
            "prohibited to prevent accidental code loss. Please view the file with 'view_file' "
            f"first, or use 'replace_file_content' for surgical edits. (File: {target_file})"
        )
        return HookResult(decision="deny", reason=reason)
