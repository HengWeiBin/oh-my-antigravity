from __future__ import annotations

import re

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


def check_fsync_skip_warning(tool_name: str, tool_input: dict) -> dict | None:
    """
    Returns an 'ask' permission decision if run_command contains dangerous patterns.
    Returns None to allow.
    """
    if tool_name != "run_command":
        return None

    command = tool_input.get("CommandLine", "")
    if not command:
        return None

    patterns = [
        (r"\bgit\s+push\b.*?(?:\s-f\b|\s--force\b)", "force push"),
        (
            r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b|\brm\s+-rf\b|\brm\s+-r\s+-f\b",
            "destructive remove",
        ),
        (r"\bdrop\s+(?:table|database)\b", "SQL destructive"),
        (r"--no-verify\b", "bypasses git hooks"),
        (r"\bgit\s+reset\s+--hard\b", "hard reset"),
        (r"\bgit\s+clean\b.*?(?:\s-[a-zA-Z]*f[a-zA-Z]*\b)", "clean working dir"),
        (r"\bformat\s+[a-z]:", "format"),
    ]

    for pattern, pattern_name in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "decision": "ask",
                "reason": (
                    f"⚠️ FSYNC WARNING: The command contains a potentially dangerous operation: "
                    f"[{pattern_name}]. Please confirm this is intentional before proceeding.\nCommand: {command}"
                ),
            }

    return None


run_fsync_skip_warning = check_fsync_skip_warning


class FsyncSkipWarningHook(BaseHook):
    @property
    def name(self) -> str:
        return "fsync_skip_warning"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name != "run_command":
            return HookResult(decision="allow")
        res = check_fsync_skip_warning(context.tool_name, context.tool_input)
        if res:
            return HookResult(decision=res.get("decision", "ask"), reason=res.get("reason"))
        return HookResult(decision="allow")
