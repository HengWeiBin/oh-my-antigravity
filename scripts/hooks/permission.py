from __future__ import annotations

import os
from dataclasses import dataclass

from scripts.hooks.models import AgentRole


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    decision: str  # "allow" | "deny" | "ask"
    reason: str | None = None


WRITE_TOOLS = {
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
}


class PermissionPolicy:
    @staticmethod
    def evaluate(
        role: AgentRole,
        tool_name: str,
        target_path: str | None,
    ) -> PermissionDecision:
        if tool_name not in WRITE_TOOLS or not target_path:
            return PermissionDecision(allowed=True, decision="allow")

        normalized_path = target_path.replace("\\", "/").lower()
        basename = os.path.basename(normalized_path)

        if role == AgentRole.WORKER:
            # Subagent / Worker Constraints:
            # Cannot write to .agents/, or plugin config files (hooks.json, plugin.json, rules/)
            # For .omo/: writing to .omo/plans/ or files in .omo/ containing "plan", "task", or "draft"
            # in the path/filename is denied, but writing to .omo/notepads/ is allowed.
            is_omo = "/.omo/" in normalized_path or normalized_path.startswith(".omo/")
            deny_omo = False
            if is_omo:
                idx = normalized_path.find("/.omo/")
                if idx != -1:
                    subpath = normalized_path[idx + 1 :]
                elif normalized_path.startswith(".omo/"):
                    subpath = normalized_path
                else:
                    subpath = ""

                is_omo_notepads = subpath.startswith(".omo/notepads/")
                is_omo_plans = subpath.startswith(".omo/plans/")
                contains_deny_word = any(w in subpath for w in ["plan", "task", "draft"])

                if not is_omo_notepads and (is_omo_plans or contains_deny_word):
                    deny_omo = True

            is_agents = "/.agents/" in normalized_path or normalized_path.startswith(".agents/")
            is_plugin_config = (
                "hooks.json" in basename
                or "plugin.json" in basename
                or "/rules/" in normalized_path
                or normalized_path.startswith("rules/")
            )

            if deny_omo or is_agents or is_plugin_config:
                return PermissionDecision(
                    allowed=False,
                    decision="deny",
                    reason=(
                        f"STOP. Subagents (workers) are forbidden from modifying .omo/ state or "
                        f"plugin configuration files (Path: {target_path})."
                    ),
                )
            return PermissionDecision(allowed=True, decision="allow")
        else:
            # Orchestrator / Default / Unknown Constraints:
            # Cannot write to product files directly.
            # Allowed files for orchestrator:
            # - .md files
            # - plans/tasks files (filename contains 'plan' or 'task')
            # - .agents/ files
            # - .omo/ files
            is_plan = "plan" in basename or "task" in basename or normalized_path.endswith(".md")
            is_agents = "/.agents/" in normalized_path or normalized_path.startswith(".agents/")
            is_omo = "/.omo/" in normalized_path or normalized_path.startswith(".omo/")

            if not (is_plan or is_agents or is_omo):
                return PermissionDecision(
                    allowed=False,
                    decision="ask",
                    reason=(
                        f"STOP. Lead Orchestrator agents do not edit source code directly (Path: {target_path}).\n"
                        "Implementing yourself is forbidden. You are paid to ORCHESTRATE, not implement.\n"
                        "If this is a tiny verification fix (<= 2 lines) on subagent output, you may proceed. "
                        "Otherwise, please delegate it via invoke_subagent."
                    ),
                )
            return PermissionDecision(allowed=True, decision="allow")
