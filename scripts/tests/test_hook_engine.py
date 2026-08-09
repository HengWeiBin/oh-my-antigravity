from __future__ import annotations

import io
import json
import os
import sys

import pytest

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.engine import BaseHook, HookEngine, HookPipeline
from scripts.hooks.models import HookContext, HookResult, LifecycleEvent


class DummyHook(BaseHook):
    def __init__(self, hook_name: str, result: HookResult) -> None:
        self._name = hook_name
        self._result = result

    @property
    def name(self) -> str:
        return self._name

    def execute(self, context: HookContext) -> HookResult:
        return self._result


class ExceptionHook(BaseHook):
    @property
    def name(self) -> str:
        return "exception_hook"

    def execute(self, context: HookContext) -> HookResult:
        raise RuntimeError("Something failed in hook")


def test_hook_models() -> None:
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="conv-123",
        cwd="/tmp",
        user_prompt="test prompt",
    )
    assert ctx.lifecycle == LifecycleEvent.PRE_INVOCATION
    assert ctx.conversation_id == "conv-123"
    assert ctx.cwd == "/tmp"
    assert ctx.user_prompt == "test prompt"
    assert ctx.tool_name is None
    assert ctx.tool_input == {}

    with pytest.raises(AttributeError):
        ctx.conversation_id = "new-id"  # type: ignore[misc]

    res = HookResult(injected_steps=[{"ephemeralMessage": "hello"}])
    assert res.injected_steps == [{"ephemeralMessage": "hello"}]
    assert res.decision is None


def test_hook_pipeline_error_containment() -> None:
    res1 = HookResult(injected_steps=[{"step": 1}])
    res2 = HookResult(injected_steps=[{"step": 2}])

    h1 = DummyHook("h1", res1)
    h_err = ExceptionHook()
    h2 = DummyHook("h2", res2)

    pipeline = HookPipeline([h1, h_err, h2])
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_INVOCATION,
        conversation_id="c1",
        cwd="/app",
    )

    results = pipeline.run(ctx)
    assert len(results) == 2
    assert results[0] == res1
    assert results[1] == res2


def test_hook_engine_run_pre_invocation(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    res1 = HookResult(injected_steps=[{"ephemeralMessage": "step 1"}])
    res2 = HookResult(injected_steps=[{"ephemeralMessage": "step 2"}])

    pipeline = HookPipeline([DummyHook("h1", res1), DummyHook("h2", res2)])
    HookEngine.set_pipeline(LifecycleEvent.PRE_INVOCATION, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-456",
        "cwd": "/workspace",
        "prompt": "do something",
    })
    input_stream = io.StringIO(input_json)

    exit_code = HookEngine.run(LifecycleEvent.PRE_INVOCATION, input_stream)
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "injectSteps" in output
    assert len(output["injectSteps"]) == 2
    assert output["injectSteps"][0] == {"ephemeralMessage": "step 1"}
    assert output["injectSteps"][1] == {"ephemeralMessage": "step 2"}


def test_hook_engine_run_pre_tool_use_allow_and_deny(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    res_allow = HookResult(decision="allow")
    res_deny = HookResult(decision="deny", reason="Unauthorized file access")

    pipeline = HookPipeline([DummyHook("allow_hook", res_allow), DummyHook("deny_hook", res_deny)])
    HookEngine.set_pipeline(LifecycleEvent.PRE_TOOL_USE, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-789",
        "tool_name": "write_to_file",
        "tool_input": {"TargetFile": "rules.json"},
    })

    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["decision"] == "deny"
    assert output["reason"] == "Unauthorized file access"


def test_hook_engine_run_post_tool_use(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    res1 = HookResult(additional_context="Warning 1")
    res2 = HookResult(additional_context="Warning 2")

    pipeline = HookPipeline([DummyHook("h1", res1), DummyHook("h2", res2)])
    HookEngine.set_pipeline(LifecycleEvent.POST_TOOL_USE, pipeline)

    input_json = json.dumps({"tool_name": "invoke_subagent"})

    exit_code = HookEngine.run(LifecycleEvent.POST_TOOL_USE, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["additionalContext"] == "Warning 1\n\nWarning 2"


def test_hook_engine_empty_and_malformed_input(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()
    HookEngine.set_pipeline(LifecycleEvent.PRE_INVOCATION, HookPipeline([]))
    HookEngine.set_pipeline(LifecycleEvent.PRE_TOOL_USE, HookPipeline([]))

    # Empty stream
    exit_code = HookEngine.run(LifecycleEvent.PRE_INVOCATION, io.StringIO(""))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"injectSteps": []}

    # Malformed JSON
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO("{invalid json"))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"decision": "allow"}

