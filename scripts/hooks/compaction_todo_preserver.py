from __future__ import annotations

import os
import re

from scripts.hooks.boulder import get_bound_active_plans
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


def get_compaction_todo_messages(payload: dict, conversation_id: str = "") -> list[dict]:
    """
    On high invocation numbers (>= 15, suggesting context compaction),
    checks active plans bound via .omo/boulder.json for unchecked TODOs and returns
    ephemeral messages to re-inject them.
    Returns list of {'ephemeralMessage': str} dicts, or empty list.
    """
    invocation_num = payload.get("invocationNum", 0)
    if not isinstance(invocation_num, int) or invocation_num < 15:
        return []

    plan_files = get_bound_active_plans(payload, conversation_id=conversation_id)
    if not plan_files:
        return []

    messages = []
    files_processed = 0

    for fpath in plan_files:
        fname = os.path.basename(fpath)
        unchecked_items = []
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if re.match(r"^\s*[-*]\s*\[[\s~]\]", line):
                        unchecked_items.append(stripped)
                        if len(unchecked_items) >= 10:
                            break
        except Exception:  # noqa: BLE001, S112
            continue

        if unchecked_items:
            msg_lines = [
                "🔄 COMPACTION TODO PRESERVER: Active plan TODOs detected (context may have been compacted).",
                "Remaining unchecked items:",
                f"[{fname}]",
            ]
            msg_lines.extend(unchecked_items)
            msg_lines.append("Please ensure you continue working on these items.")
            messages.append({"ephemeralMessage": "\n".join(msg_lines)})

            files_processed += 1
            if files_processed >= 3:
                return messages

    return messages


run_compaction_todo_preserver = get_compaction_todo_messages


class CompactionTodoPreserverHook(BaseHook):
    @property
    def name(self) -> str:
        return "compaction_todo_preserver"

    def execute(self, context: HookContext) -> HookResult:
        messages = get_compaction_todo_messages(
            context.raw_payload, conversation_id=context.conversation_id
        )
        return HookResult(injected_steps=messages)
