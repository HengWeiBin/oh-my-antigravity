from __future__ import annotations

import os

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult
from scripts.hooks.permission import PermissionPolicy
from scripts.hooks.session import SessionResolver


class PermissionHook(BaseHook):
    @property
    def name(self) -> str:
        return "permission_hook"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name not in [
            "write_to_file",
            "replace_file_content",
            "multi_replace_file_content",
        ]:
            return HookResult(decision="allow")

        target_file = context.tool_input.get("TargetFile") or context.tool_input.get("file_path")
        if not target_file:
            return HookResult(decision="allow")

        artifact_dir = context.raw_payload.get("artifactDirectoryPath", "")
        brain_dir = os.path.dirname(artifact_dir) if artifact_dir else ""

        role = SessionResolver.resolve_role(context.conversation_id, brain_dir)
        decision = PermissionPolicy.evaluate(role, context.tool_name, target_file)

        if not decision.allowed:
            return HookResult(decision=decision.decision, reason=decision.reason)

        return HookResult(decision="allow")
