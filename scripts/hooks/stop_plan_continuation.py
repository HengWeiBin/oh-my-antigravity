from __future__ import annotations

import os
import re

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult
from scripts.hooks.utils import resolve_path


def check_uncompleted_plans(payload: dict, cwd: str = "") -> tuple[bool, int, list[str]]:
    """Checks .omo/plans/ in workspace paths and cwd for incomplete markdown plans.

    Returns (has_uncompleted, total_unchecked, list_of_filenames).
    """
    workspace_paths_raw = payload.get("workspacePaths", [])
    workspace_paths = [wp for wp in workspace_paths_raw if isinstance(wp, str) and wp]
    payload_cwd = payload.get("cwd") or cwd or ""

    resolved_cwd = resolve_path(payload_cwd) if payload_cwd else ""
    resolved_workspaces = [
        resolve_path(wp, resolved_cwd if resolved_cwd else None)
        for wp in workspace_paths
    ]

    dirs_to_check: list[str] = []
    for wp in resolved_workspaces:
        if wp and wp not in dirs_to_check:
            dirs_to_check.append(wp)
    if resolved_cwd and resolved_cwd not in dirs_to_check:
        dirs_to_check.append(resolved_cwd)

    if not dirs_to_check:
        dirs_to_check.append(os.getcwd())

    plan_files: list[str] = []
    for d in dirs_to_check:
        plans_dir = os.path.join(d, ".omo", "plans")
        if os.path.isdir(plans_dir):
            for filename in os.listdir(plans_dir):
                if filename.endswith(".md"):
                    plan_files.append(os.path.join(plans_dir, filename))

    plan_files = list({os.path.abspath(f) for f in plan_files})

    unchecked_files: list[str] = []
    total_unchecked = 0

    for plan_file in plan_files:
        try:
            with open(plan_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            unchecked_count = 0
            for line in content.splitlines():
                if re.search(r"^\s*[-*]\s*\[\s\]", line):
                    unchecked_count += 1

            if unchecked_count > 0:
                unchecked_files.append(os.path.basename(plan_file))
                total_unchecked += unchecked_count
        except OSError:
            pass

    return (total_unchecked > 0, total_unchecked, unchecked_files)


class StopPlanContinuationHook(BaseHook):
    @property
    def name(self) -> str:
        return "stop_plan_continuation"

    def execute(self, context: HookContext) -> HookResult:
        payload = context.raw_payload
        termination_reason = payload.get("terminationReason")
        fully_idle = payload.get("fullyIdle", True)

        if termination_reason != "model_stop" or not fully_idle:
            return HookResult()

        has_uncompleted, total_unchecked, unchecked_files = check_uncompleted_plans(
            payload, cwd=context.cwd
        )

        if has_uncompleted:
            files_str = ", ".join(unchecked_files)
            return HookResult(
                decision="continue",
                reason=f"Active plan has {total_unchecked} incomplete task(s) in [{files_str}]. Please complete all tasks before stopping.",
            )

        return HookResult()
