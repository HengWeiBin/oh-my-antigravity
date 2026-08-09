from __future__ import annotations

import json
import os
import re

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


def resolve_path(path: str, cwd: str | None = None) -> str:
    """Helper to resolve paths"""
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    if path.startswith("~"):
        return os.path.expanduser(path)
    if cwd:
        return os.path.normpath(os.path.join(cwd, path))
    return os.path.normpath(os.path.abspath(path))


def get_todo_continuation_messages(payload: dict) -> list[dict]:
    """
    Detects stalled/abandoned work by checking .omo/plans/ for incomplete TODOs.
    On detection (invocationNum >= 3 and unchecked items exist), injects a continuation prompt.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    invocation_num = payload.get("invocationNum", 0)
    if not isinstance(invocation_num, int) or invocation_num < 3:
        return []

    artifact_dir = payload.get("artifactDirectoryPath", "")
    if not artifact_dir:
        return []

    # Get search directories
    workspace_paths_raw = payload.get("workspacePaths", [])
    workspace_paths = [wp for wp in workspace_paths_raw if isinstance(wp, str) and wp]
    cwd = payload.get("cwd", "")

    resolved_cwd = resolve_path(cwd) if cwd else ""
    resolved_workspaces = [
        resolve_path(wp, resolved_cwd if resolved_cwd else None)
        for wp in workspace_paths
    ]

    dirs_to_check = []
    for wp in resolved_workspaces:
        if wp and wp not in dirs_to_check:
            dirs_to_check.append(wp)
    if resolved_cwd and resolved_cwd not in dirs_to_check:
        dirs_to_check.append(resolved_cwd)

    # Scan .omo/plans/
    plan_files = []
    for d in dirs_to_check:
        plans_dir = os.path.join(d, ".omo", "plans")
        if os.path.isdir(plans_dir):
            for filename in os.listdir(plans_dir):
                if filename.endswith(".md"):
                    plan_files.append(os.path.join(plans_dir, filename))

    # Deduplicate based on absolute path
    plan_files = list({os.path.abspath(f) for f in plan_files})

    unchecked_by_file = {}
    total_unchecked = 0

    for plan_file in plan_files:
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                content = f.read()

            unchecked = []
            for line in content.splitlines():
                if re.search(r"^\s*-\s*\[\s\]", line):
                    unchecked.append(line.strip())

            if unchecked:
                unchecked_by_file[os.path.basename(plan_file)] = unchecked
                total_unchecked += len(unchecked)
        except OSError:
            pass

    if total_unchecked == 0:
        return []

    # Read state
    state_file = os.path.join(artifact_dir, "todo_continuation_state.json")
    last_injection_invocation = -1

    try:
        if os.path.isfile(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                last_injection_invocation = state.get("last_injection_invocation", -1)
    except Exception:  # noqa: BLE001
        last_injection_invocation = -1

    # Check throttling
    if last_injection_invocation != -1 and (invocation_num - last_injection_invocation) < 5:
        return []

    # Inject message
    msg_lines = [
        "🎯 TODO CONTINUATION ENFORCER: You have unchecked tasks in your active plans!",
        "",
    ]

    for filename, tasks in unchecked_by_file.items():
        msg_lines.append(f"[{filename}]")
        msg_lines.extend(tasks)
        msg_lines.append("")

    msg_lines.append("Please continue working on these tasks without asking for permission to proceed.")
    msg_lines.append("AUTO-CONTINUE: Do not ask the user 'should I continue?'")

    message = "\n".join(msg_lines).strip()

    # Update state
    try:
        os.makedirs(artifact_dir, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "last_injection_invocation": invocation_num,
                    "last_unchecked_count": total_unchecked,
                },
                f,
            )
    except OSError:
        pass

    return [{"ephemeralMessage": message}]


run_todo_continuation_enforcer = get_todo_continuation_messages


class TodoContinuationEnforcerHook(BaseHook):
    @property
    def name(self) -> str:
        return "todo_continuation_enforcer"

    def execute(self, context: HookContext) -> HookResult:
        messages = get_todo_continuation_messages(context.raw_payload)
        return HookResult(injected_steps=messages)
