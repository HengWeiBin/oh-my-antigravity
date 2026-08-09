from __future__ import annotations

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

VERIFICATION_REMINDER_MSG = (
    "**THE SUBAGENT HAS FINISHED. THEIR WORK IS EXTREMELY SUSPICIOUS. YOU MUST VERIFY WITH ACTUAL TOOL CALLS. NOT REASONING. TOOL CALLS.**\n\n"
    "Subagents ROUTINELY produce broken, incomplete, wrong code and then claim it is done. "
    "Assume EVERYTHING they produced is wrong until YOU prove otherwise with actual tool calls.\n\n"
    "4-Phase Protocol (every delegation, no exceptions):\n"
    "1. **READ CODE** - Read every changed file, trace logic, check scope.\n"
    "2. **RUN CHECKS** - Run build, tests, lint diagnostics using run_command.\n"
    "3. **HANDS-ON QA** - Actually run/open/interact with the deliverable using browser_subagent (/browser) or curl.\n"
    "4. **GATE DECISION** - Can you explain every line? Did you see it work? Confident nothing broke?\n\n"
    "On failure: Resume the SAME session conversation ID with the SPECIFIC failure message using send_message."
)


class SubagentVerificationReminderHook(BaseHook):
    @property
    def name(self) -> str:
        return "subagent_verification_reminder"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name == "invoke_subagent":
            return HookResult(additional_context=VERIFICATION_REMINDER_MSG)
        return HookResult()
