from __future__ import annotations

import os
import re

from scripts.hooks.boulder import get_bound_active_plans
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

UNCHECKED_RE = re.compile(r"^\s*[-*]\s*\[[\s~]\]")


def check_uncompleted_plans(
    payload: dict,
    cwd: str = "",
    conversation_id: str = "",
) -> tuple[bool, int, list[str]]:
    """Checks active plans bound via .omo/boulder.json for incomplete markdown tasks.

    Returns (has_uncompleted, total_unchecked, list_of_filenames).
    """
    plan_files = get_bound_active_plans(payload, cwd=cwd, conversation_id=conversation_id)

    unchecked_files: list[str] = []
    total_unchecked = 0

    for plan_file in plan_files:
        try:
            with open(plan_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            unchecked_count = 0
            for line in content.splitlines():
                if UNCHECKED_RE.search(line):
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

        if termination_reason not in ("model_stop", "NO_TOOL_CALL") or not fully_idle:
            return HookResult()

        if payload.get("continuationActive") is True or context.continuation_active:
            return HookResult()

        has_uncompleted, total_unchecked, unchecked_files = check_uncompleted_plans(
            payload, cwd=context.cwd, conversation_id=context.conversation_id
        )

        if has_uncompleted:
            files_str = ", ".join(unchecked_files)
            return HookResult(
                decision="continue",
                reason=(
                    f"Active plan has {total_unchecked} incomplete task(s) in [{files_str}]. "
                    f"Please complete all tasks before stopping. "
                    f"Note: If the user explicitly refused, canceled, or denied an operation or permission, "
                    f"treat that refusal as final and do not retry the refused action."
                ),
            )

        return HookResult()
