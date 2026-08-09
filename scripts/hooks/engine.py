from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from typing import ClassVar, TextIO

from scripts.hooks.models import HookContext, HookResult, LifecycleEvent
from scripts.hooks.skill_resolver import SkillResolver
from scripts.hooks.utils import (
    check_codegraph_dir_exists,
    check_mcp_active,
    extract_user_prompt,
    is_subagent_session,
    parse_skill_commands,
    resolve_path,
    setup_utf8_streams,
)


class BaseHook(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The human-readable name of the hook."""
        ...

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """Execute hook logic using typed context and return structured result."""
        ...


class CodegraphRecommendationHook(BaseHook):
    @property
    def name(self) -> str:
        return "codegraph_recommendation"

    def execute(self, context: HookContext) -> HookResult:
        payload = context.raw_payload
        invocation_num = payload.get("invocationNum", 0)
        if not isinstance(invocation_num, int):
            invocation_num = 0

        if invocation_num == 0:
            workspace_paths_raw = payload.get("workspacePaths", [])
            workspace_paths = [wp for wp in workspace_paths_raw if isinstance(wp, str) and wp]
            cwd = payload.get("cwd", "")
            resolved_cwd = resolve_path(cwd) if cwd else ""
            resolved_workspaces = [
                resolve_path(wp, resolved_cwd if resolved_cwd else None) for wp in workspace_paths
            ]
            codegraph_exists = check_codegraph_dir_exists(resolved_workspaces, resolved_cwd)
            mcp_active = check_mcp_active(resolved_workspaces)

            if codegraph_exists and mcp_active:
                msg = (
                    "A `.codegraph` directory and the `codegraph` MCP server are active in this workspace. "
                    "You should prioritize using `codegraph_explore` to explore symbols, find call paths, "
                    "and understand the codebase architecture in a single round-trip instead of standard grep + read loops."
                )
                return HookResult(injected_steps=[{"ephemeralMessage": msg}])
        return HookResult()


class SubagentSkillAutoloaderHook(BaseHook):
    def __init__(self, skill_resolver: SkillResolver | None = None) -> None:
        self.skill_resolver = skill_resolver or SkillResolver()

    @property
    def name(self) -> str:
        return "subagent_skill_autoloader"

    def execute(self, context: HookContext) -> HookResult:
        payload = context.raw_payload
        if is_subagent_session(payload):
            user_prompt = extract_user_prompt(payload)
            if user_prompt:
                workspace_paths_raw = payload.get("workspacePaths", [])
                workspace_paths = [wp for wp in workspace_paths_raw if isinstance(wp, str) and wp]
                cwd = payload.get("cwd", "")
                resolved_cwd = resolve_path(cwd) if cwd else ""
                resolved_workspaces = [
                    resolve_path(wp, resolved_cwd if resolved_cwd else None) for wp in workspace_paths
                ]

                skill_names = parse_skill_commands(user_prompt)
                steps: list[dict] = []
                for s_name in skill_names:
                    formatted = self.skill_resolver.format_instruction_block(
                        s_name, workspace_paths=resolved_workspaces, cwd=resolved_cwd
                    )
                    if formatted:
                        steps.append({"ephemeralMessage": formatted})
                if steps:
                    return HookResult(injected_steps=steps)
        return HookResult()


class HookPipeline:
    def __init__(self, hooks: list[BaseHook] | None = None) -> None:
        self.hooks: list[BaseHook] = list(hooks) if hooks else []

    def register(self, hook: BaseHook) -> None:
        self.hooks.append(hook)

    def run(self, context: HookContext) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in self.hooks:
            try:
                res = hook.execute(context)
                if res is not None:
                    results.append(res)
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"[HookEngine] Error in hook '{hook.name}': {e}\n")
        return results


class HookEngine:
    _pipelines: ClassVar[dict[LifecycleEvent, HookPipeline]] = {}


    @classmethod
    def register_hook(cls, lifecycle: LifecycleEvent, hook: BaseHook) -> None:
        if lifecycle not in cls._pipelines:
            cls._pipelines[lifecycle] = cls.create_default_pipeline(lifecycle)
        cls._pipelines[lifecycle].register(hook)

    @classmethod
    def set_pipeline(cls, lifecycle: LifecycleEvent, pipeline: HookPipeline) -> None:
        cls._pipelines[lifecycle] = pipeline

    @classmethod
    def get_pipeline(cls, lifecycle: LifecycleEvent) -> HookPipeline:
        if lifecycle not in cls._pipelines:
            cls._pipelines[lifecycle] = cls.create_default_pipeline(lifecycle)
        return cls._pipelines[lifecycle]

    @classmethod
    def create_default_pipeline(cls, lifecycle: LifecycleEvent) -> HookPipeline:
        pipeline = HookPipeline()
        if lifecycle == LifecycleEvent.PRE_INVOCATION:
            from scripts.hooks.agent_usage_reminder import AgentUsageReminderHook
            from scripts.hooks.compaction_todo_preserver import (
                CompactionTodoPreserverHook,
            )
            from scripts.hooks.directory_agents_injector import (
                DirectoryAgentsInjectorHook,
            )
            from scripts.hooks.init_project_dir_replacer import (
                InitProjectDirReplacerHook,
            )
            from scripts.hooks.keyword_detector import KeywordDetectorHook
            from scripts.hooks.rules_injector import RulesInjectorHook
            from scripts.hooks.todo_continuation_enforcer import (
                TodoContinuationEnforcerHook,
            )

            pipeline.register(DirectoryAgentsInjectorHook())
            pipeline.register(RulesInjectorHook())
            pipeline.register(CompactionTodoPreserverHook())
            pipeline.register(TodoContinuationEnforcerHook())
            pipeline.register(AgentUsageReminderHook())
            pipeline.register(KeywordDetectorHook())
            pipeline.register(InitProjectDirReplacerHook())
            pipeline.register(CodegraphRecommendationHook())
            pipeline.register(SubagentSkillAutoloaderHook())

        elif lifecycle == LifecycleEvent.PRE_TOOL_USE:
            from scripts.hooks.fsync_skip_warning import FsyncSkipWarningHook
            from scripts.hooks.notepad_write_guard import NotepadWriteGuardHook
            from scripts.hooks.permission_hook import PermissionHook

            pipeline.register(PermissionHook())
            pipeline.register(NotepadWriteGuardHook())
            pipeline.register(FsyncSkipWarningHook())

        elif lifecycle == LifecycleEvent.POST_TOOL_USE:
            from scripts.hooks.comment_checker import CommentCheckerHook
            from scripts.hooks.empty_task_response_detector import (
                EmptyTaskResponseDetectorHook,
            )
            from scripts.hooks.plan_format_validator import PlanFormatValidatorHook
            from scripts.hooks.subagent_verification_reminder import (
                SubagentVerificationReminderHook,
            )

            pipeline.register(SubagentVerificationReminderHook())
            pipeline.register(EmptyTaskResponseDetectorHook())
            pipeline.register(CommentCheckerHook())
            pipeline.register(PlanFormatValidatorHook())

        return pipeline

    @classmethod
    def clear_pipelines(cls) -> None:
        cls._pipelines.clear()

    @classmethod
    def parse_payload(cls, input_stream: TextIO) -> dict:
        try:
            raw_text = input_stream.read().strip()
            if not raw_text:
                return {}
            data = json.loads(raw_text)
            return data if isinstance(data, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    @classmethod
    def build_context(cls, lifecycle: LifecycleEvent, payload: dict) -> HookContext:
        conversation_id = payload.get("conversationId") or payload.get("conversation_id") or ""
        if not isinstance(conversation_id, str):
            conversation_id = ""

        cwd = payload.get("cwd") or ""
        if not isinstance(cwd, str):
            cwd = ""

        tool_name = payload.get("tool_name")
        if not tool_name and "toolCall" in payload and isinstance(payload["toolCall"], dict):
            tool_name = payload["toolCall"].get("name")
        if not isinstance(tool_name, str):
            tool_name = None

        tool_input = payload.get("tool_input")
        if not tool_input and "toolCall" in payload and isinstance(payload["toolCall"], dict):
            tool_input = payload["toolCall"].get("args", {})
        if not isinstance(tool_input, dict):
            tool_input = {}

        tool_output = payload.get("tool_response") or payload.get("tool_output") or payload.get("response")
        if tool_output is not None and not isinstance(tool_output, str):
            tool_output = str(tool_output)

        user_prompt = extract_user_prompt(payload)

        return HookContext(
            lifecycle=lifecycle,
            conversation_id=conversation_id,
            cwd=cwd,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            user_prompt=user_prompt if user_prompt else None,
            raw_payload=payload,
        )

    @classmethod
    def serialize_output(cls, lifecycle: LifecycleEvent, results: list[HookResult]) -> dict:
        if lifecycle == LifecycleEvent.PRE_INVOCATION:
            steps: list[dict] = []
            for res in results:
                if res.injected_steps:
                    steps.extend(res.injected_steps)
            return {"injectSteps": steps}

        elif lifecycle == LifecycleEvent.PRE_TOOL_USE:
            for res in results:
                if res.decision and res.decision.lower() in ("deny", "ask"):
                    out = {"decision": res.decision.lower()}
                    if res.reason:
                        out["reason"] = res.reason
                    return out
            return {"decision": "allow"}

        elif lifecycle == LifecycleEvent.POST_TOOL_USE:
            contexts: list[str] = []
            for res in results:
                if res.additional_context and res.additional_context.strip():
                    contexts.append(res.additional_context.strip())
            if contexts:
                return {"additionalContext": "\n\n".join(contexts)}
            return {}

        return {}

    @classmethod
    def run(cls, lifecycle: LifecycleEvent, input_stream: TextIO = sys.stdin) -> int:
        setup_utf8_streams()
        payload = cls.parse_payload(input_stream)
        context = cls.build_context(lifecycle, payload)

        pipeline = cls.get_pipeline(lifecycle)
        results = pipeline.run(context)

        output = cls.serialize_output(lifecycle, results)
        print(json.dumps(output, ensure_ascii=False))
        return 0
