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

    # PostInvocation and Stop enums
    assert LifecycleEvent.POST_INVOCATION.value == "PostInvocation"
    assert LifecycleEvent.STOP.value == "Stop"

    ctx_post = HookContext(
        lifecycle=LifecycleEvent.POST_INVOCATION,
        conversation_id="conv-post",
        cwd="/tmp",
        raw_payload={"response": {"text": "summary"}},
    )
    assert ctx_post.lifecycle == LifecycleEvent.POST_INVOCATION
    assert ctx_post.raw_payload == {"response": {"text": "summary"}}

    ctx_stop = HookContext(
        lifecycle=LifecycleEvent.STOP,
        conversation_id="conv-stop",
        cwd="/tmp",
        raw_payload={"stopReason": "completed"},
    )
    assert ctx_stop.lifecycle == LifecycleEvent.STOP
    assert ctx_stop.raw_payload == {"stopReason": "completed"}

    res = HookResult(
        decision="force_continue",
        injected_steps=[{"ephemeralMessage": "hello"}],
    )
    assert res.decision == "force_continue"
    assert res.injected_steps == [{"ephemeralMessage": "hello"}]


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


def test_hook_engine_default_pipelines() -> None:
    post_inv_pipeline = HookEngine.create_default_pipeline(LifecycleEvent.POST_INVOCATION)
    assert isinstance(post_inv_pipeline, HookPipeline)
    assert len(post_inv_pipeline.hooks) == 0

    stop_pipeline = HookEngine.create_default_pipeline(LifecycleEvent.STOP)
    assert isinstance(stop_pipeline, HookPipeline)
    assert len(stop_pipeline.hooks) == 0


def test_hook_engine_build_context_post_invocation_and_stop() -> None:
    post_payload = {
        "conversationId": "conv-post-1",
        "cwd": "/workspace",
        "invocationNum": 2,
        "response": {"text": "Model output", "toolCalls": []},
        "usage": {"promptTokens": 100, "completionTokens": 50},
    }
    ctx_post = HookEngine.build_context(LifecycleEvent.POST_INVOCATION, post_payload)
    assert ctx_post.lifecycle == LifecycleEvent.POST_INVOCATION
    assert ctx_post.conversation_id == "conv-post-1"
    assert ctx_post.cwd == "/workspace"
    assert ctx_post.raw_payload["response"] == {"text": "Model output", "toolCalls": []}

    stop_payload = {
        "conversationId": "conv-stop-1",
        "cwd": "/workspace",
        "stopReason": "completed",
        "transcriptPath": "/tmp/transcript.jsonl",
    }
    ctx_stop = HookEngine.build_context(LifecycleEvent.STOP, stop_payload)
    assert ctx_stop.lifecycle == LifecycleEvent.STOP
    assert ctx_stop.conversation_id == "conv-stop-1"
    assert ctx_stop.cwd == "/workspace"
    assert ctx_stop.raw_payload["stopReason"] == "completed"


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


def test_hook_engine_run_post_invocation_decision_and_steps(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    res1 = HookResult(decision="force_continue", injected_steps=[{"ephemeralMessage": "continue loop"}])
    res2 = HookResult(injected_steps=[{"ephemeralMessage": "additional step"}])

    pipeline = HookPipeline([DummyHook("h1", res1), DummyHook("h2", res2)])
    HookEngine.set_pipeline(LifecycleEvent.POST_INVOCATION, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-post-2",
        "cwd": "/workspace",
        "response": {"text": "Model output"},
    })

    exit_code = HookEngine.run(LifecycleEvent.POST_INVOCATION, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["decision"] == "force_continue"
    assert output["injectSteps"] == [
        {"ephemeralMessage": "continue loop"},
        {"ephemeralMessage": "additional step"},
    ]


def test_hook_engine_run_post_invocation_terminate(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    res = HookResult(decision="terminate")
    pipeline = HookPipeline([DummyHook("term_hook", res)])
    HookEngine.set_pipeline(LifecycleEvent.POST_INVOCATION, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-post-3",
        "cwd": "/workspace",
        "response": {"text": "Stopping here"},
    })

    exit_code = HookEngine.run(LifecycleEvent.POST_INVOCATION, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output == {"decision": "terminate"}


def test_hook_engine_run_post_invocation_empty(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    pipeline = HookPipeline([DummyHook("noop_hook", HookResult())])
    HookEngine.set_pipeline(LifecycleEvent.POST_INVOCATION, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-post-4",
        "cwd": "/workspace",
        "response": {"text": "Clean response"},
    })

    exit_code = HookEngine.run(LifecycleEvent.POST_INVOCATION, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output == {}


def test_hook_engine_run_stop(capsys: pytest.CaptureFixture[str]) -> None:
    HookEngine.clear_pipelines()

    pipeline = HookPipeline([DummyHook("stop_hook", HookResult())])
    HookEngine.set_pipeline(LifecycleEvent.STOP, pipeline)

    input_json = json.dumps({
        "conversationId": "conv-stop-2",
        "cwd": "/workspace",
        "stopReason": "completed",
    })

    exit_code = HookEngine.run(LifecycleEvent.STOP, io.StringIO(input_json))
    assert exit_code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output == {}


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
    HookEngine.set_pipeline(LifecycleEvent.POST_INVOCATION, HookPipeline([]))
    HookEngine.set_pipeline(LifecycleEvent.PRE_TOOL_USE, HookPipeline([]))
    HookEngine.set_pipeline(LifecycleEvent.STOP, HookPipeline([]))

    # Empty stream - PRE_INVOCATION
    exit_code = HookEngine.run(LifecycleEvent.PRE_INVOCATION, io.StringIO(""))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"injectSteps": []}

    # Empty stream - POST_INVOCATION
    exit_code = HookEngine.run(LifecycleEvent.POST_INVOCATION, io.StringIO(""))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {}

    # Empty stream - STOP
    exit_code = HookEngine.run(LifecycleEvent.STOP, io.StringIO(""))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {}

    # Malformed JSON - PRE_TOOL_USE
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO("{invalid json"))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"decision": "allow"}

