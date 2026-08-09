from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts import pre_invocation
from scripts.hooks.agent_usage_reminder import AgentUsageReminderHook
from scripts.hooks.compaction_todo_preserver import CompactionTodoPreserverHook
from scripts.hooks.directory_agents_injector import DirectoryAgentsInjectorHook
from scripts.hooks.engine import (
    CodegraphRecommendationHook,
    HookEngine,
    SubagentSkillAutoloaderHook,
)
from scripts.hooks.init_project_dir_replacer import InitProjectDirReplacerHook
from scripts.hooks.keyword_detector import KeywordDetectorHook
from scripts.hooks.models import HookContext, LifecycleEvent
from scripts.hooks.rules_injector import RulesInjectorHook
from scripts.hooks.skill_resolver import SkillResolver
from scripts.hooks.todo_continuation_enforcer import TodoContinuationEnforcerHook

EXPECTED_EPHEMERAL_MESSAGE = (
    "A `.codegraph` directory and the `codegraph` MCP server are active in this workspace. "
    "You should prioritize using `codegraph_explore` to explore symbols, find call paths, "
    "and understand the codebase architecture in a single round-trip instead of standard grep + read loops."
)


def test_codegraph_recommendation_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    ws_dir.mkdir()
    codegraph_dir = ws_dir / ".codegraph"
    codegraph_dir.mkdir()

    mcp_dir = ws_dir / ".gemini" / "antigravity" / "mcp" / "codegraph"
    mcp_dir.mkdir(parents=True)

    hook = CodegraphRecommendationHook()

    # invocation 0 -> recommends codegraph
    ctx0 = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        raw_payload={
            "invocationNum": 0,
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res0 = hook.execute(ctx0)
    assert len(res0.injected_steps) == 1
    assert res0.injected_steps[0]["ephemeralMessage"] == EXPECTED_EPHEMERAL_MESSAGE

    # invocation 1 -> no recommendation
    ctx1 = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        raw_payload={
            "invocationNum": 1,
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res1 = hook.execute(ctx1)
    assert len(res1.injected_steps) == 0


def test_subagent_skill_autoloader_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    skill_dir = ws_dir / ".agents" / "skills" / "my-test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("Do testing carefully.", encoding="utf-8")

    resolver = SkillResolver()
    hook = SubagentSkillAutoloaderHook(skill_resolver=resolver)

    ctx_sub = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="sub-1",
        cwd=str(ws_dir),
        user_prompt="Please execute /my-test-skill now",
        raw_payload={
            "isSubagent": True,
            "prompt": "Please execute /my-test-skill now",
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res_sub = hook.execute(ctx_sub)
    assert len(res_sub.injected_steps) == 1
    assert res_sub.injected_steps[0]["ephemeralMessage"] == (
        "<skill-instruction>\nDo testing carefully.\n</skill-instruction>"
    )

    # Main agent session should be ignored by subagent autoloader
    ctx_main = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="main-1",
        cwd=str(ws_dir),
        user_prompt="Please execute /my-test-skill now",
        raw_payload={
            "isSubagent": False,
            "prompt": "Please execute /my-test-skill now",
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res_main = hook.execute(ctx_main)
    assert len(res_main.injected_steps) == 0


def test_directory_agents_injector_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    ws_dir.mkdir()
    (ws_dir / "AGENTS.md").write_text("Instruction for workspace agent.", encoding="utf-8")

    hook = DirectoryAgentsInjectorHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        raw_payload={
            "cwd": str(ws_dir),
            "workspacePaths": [str(ws_dir)],
        },
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "Instruction for workspace agent." in res.injected_steps[0]["ephemeralMessage"]


def test_rules_injector_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    rules_dir = ws_dir / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "coding.md").write_text("Rule 1: No global state.", encoding="utf-8")

    hook = RulesInjectorHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        raw_payload={
            "context": {
                "workspaceUri": f"file:///{ws_dir.as_posix()}",
                "cwd": str(ws_dir),
            }
        },
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "Rule 1: No global state." in res.injected_steps[0]["ephemeralMessage"]


def test_compaction_todo_preserver_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    plans_dir = ws_dir / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "feature.md").write_text("- [ ] Implement feature\n- [x] Write spec", encoding="utf-8")

    hook = CompactionTodoPreserverHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        raw_payload={
            "invocationNum": 15,
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "COMPACTION TODO PRESERVER" in res.injected_steps[0]["ephemeralMessage"]
    assert "- [ ] Implement feature" in res.injected_steps[0]["ephemeralMessage"]


def test_todo_continuation_enforcer_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    plans_dir = ws_dir / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "todo.md").write_text("- [ ] Finish tests", encoding="utf-8")

    artifact_dir = tmp_path / "brain" / "conv-1"
    artifact_dir.mkdir(parents=True)

    hook = TodoContinuationEnforcerHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="conv-1",
        cwd=str(ws_dir),
        raw_payload={
            "invocationNum": 4,
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
            "artifactDirectoryPath": str(artifact_dir),
        },
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "TODO CONTINUATION ENFORCER" in res.injected_steps[0]["ephemeralMessage"]


def test_agent_usage_reminder_hook() -> None:
    hook = AgentUsageReminderHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd="/tmp",
        raw_payload={"invocationNum": 5, "isSubagent": False},
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "AGENT USAGE REMINDER" in res.injected_steps[0]["ephemeralMessage"]


def test_keyword_detector_hook() -> None:
    hook = KeywordDetectorHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd="/tmp",
        user_prompt="Let's start with $programming style",
        raw_payload={"prompt": "Let's start with $programming style"},
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "<skill-instruction>" in res.injected_steps[0]["ephemeralMessage"]


def test_init_project_dir_replacer_hook(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    ws_dir.mkdir()

    hook = InitProjectDirReplacerHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd=str(ws_dir),
        user_prompt="/init the project",
        raw_payload={
            "prompt": "/init the project",
            "workspacePaths": [str(ws_dir)],
            "cwd": str(ws_dir),
        },
    )
    res = hook.execute(ctx)
    assert len(res.injected_steps) == 1
    assert "<skill-instruction>" in res.injected_steps[0]["ephemeralMessage"]
    assert str(ws_dir) in res.injected_steps[0]["ephemeralMessage"]


def test_pre_invocation_runner_delegation(capsys) -> None:
    HookEngine.clear_pipelines()
    input_payload = json.dumps({
        "invocationNum": 5,
        "isSubagent": False,
        "cwd": "/tmp",
    })
    sys.stdin = io.StringIO(input_payload)
    pre_invocation.main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "injectSteps" in output
    assert len(output["injectSteps"]) >= 1
