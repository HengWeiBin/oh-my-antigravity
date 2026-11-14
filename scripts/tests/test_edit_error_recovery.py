from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.edit_error_recovery import (
    DIAGNOSTIC_WARNING_TEMPLATE,
    LOCK_DENIAL_REASON_TEMPLATE,
    EditErrorRecoveryHook,
    SessionEditState,
)
from scripts.hooks.engine import HookEngine
from scripts.hooks.models import HookContext, LifecycleEvent


@pytest.fixture
def isolated_state(tmp_path: Path) -> SessionEditState:
    state_dir = tmp_path / "edit_recovery_state"
    return SessionEditState(state_dir=str(state_dir))


def test_post_tool_use_emits_diagnostic_warning_when_edit_fails_with_tool_error(
    isolated_state: SessionEditState,
) -> None:
    # Given: replace_file_content failed with a non-empty tool_error
    cid = "conv-test-01"
    target_file = "src/calculator.py"
    hook = EditErrorRecoveryHook(state=isolated_state)

    ctx = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file, "TargetContent": "def add"},
        tool_error="TargetContent not found in file",
    )

    # When: executing the hook in PostToolUse
    result = hook.execute(ctx)

    # Then: diagnostic warning must be emitted in additional_context
    expected_msg = DIAGNOSTIC_WARNING_TEMPLATE.format(target_file=target_file)
    assert result.additional_context == expected_msg
    assert "[EditErrorRecovery]" in result.additional_context
    assert "STOP guessing line numbers or context strings" in result.additional_context
    assert "view_file" in result.additional_context
    assert target_file in result.additional_context

    # And the file must now be locked in the session state
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is True


def test_post_tool_use_emits_warning_for_multi_replace_file_content(
    isolated_state: SessionEditState,
) -> None:
    # Given: multi_replace_file_content failed with an error
    cid = "conv-test-02"
    target_file = "app/models.py"
    hook = EditErrorRecoveryHook(state=isolated_state)

    ctx = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="multi_replace_file_content",
        tool_input={"TargetFile": target_file},
        tool_error="Failed to find replacement chunk 1",
    )

    # When: executing the hook in PostToolUse
    result = hook.execute(ctx)

    # Then: diagnostic warning is emitted and file is locked
    expected_msg = DIAGNOSTIC_WARNING_TEMPLATE.format(target_file=target_file)
    assert result.additional_context == expected_msg
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is True


def test_post_tool_use_emits_to_stderr_via_hook_engine_serialization(
    isolated_state: SessionEditState, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: a post-tool hook result with additional_context
    target_file = "service/auth.py"
    hook = EditErrorRecoveryHook(state=isolated_state)

    ctx = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id="conv-test-stderr",
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file},
        tool_error="Edit mismatch error",
    )
    result = hook.execute(ctx)

    # When: serializing output for PostToolUse
    mock_stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", mock_stderr)
    output = HookEngine.serialize_output(LifecycleEvent.POST_TOOL_USE, [result])

    # Then: stdout dictionary is strictly {} and stderr receives the diagnostic warning
    assert output == {}
    assert (
        f"[EditErrorRecovery] Surgical edit failed on '{target_file}'"
        in mock_stderr.getvalue()
    )


def test_post_tool_use_no_warning_when_edit_succeeds(
    isolated_state: SessionEditState,
) -> None:
    # Given: replace_file_content succeeded (tool_error is None or empty)
    cid = "conv-test-03"
    target_file = "src/calculator.py"
    hook = EditErrorRecoveryHook(state=isolated_state)

    ctx = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file},
        tool_output="Successfully replaced 1 occurrence",
        tool_error=None,
    )

    # When: executing PostToolUse
    result = hook.execute(ctx)

    # Then: no warning and file is not locked
    assert result.additional_context is None
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is False


def test_pre_tool_use_allows_normal_edit_when_no_prior_error(
    isolated_state: SessionEditState,
) -> None:
    # Given: a file with no prior edit error
    cid = "conv-test-04"
    target_file = "src/clean.py"
    hook = EditErrorRecoveryHook(state=isolated_state)

    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file},
    )

    # When: executing PreToolUse
    result = hook.execute(ctx)

    # Then: decision is allow with no denial reason
    assert result.decision == "allow"
    assert result.reason is None


def test_pre_tool_use_denies_repeat_edit_or_write_on_file_that_failed_edit(
    isolated_state: SessionEditState,
) -> None:
    # Given: an edit failed on test.py earlier in the session
    cid = "conv-test-05"
    target_file = "src/failing.py"
    isolated_state.lock_file(cid, target_file, cwd="C:/test_project")
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is True

    hook = EditErrorRecoveryHook(state=isolated_state)
    expected_reason = LOCK_DENIAL_REASON_TEMPLATE.format(target_file=target_file)

    # When 1: agent attempts replace_file_content on the locked file
    ctx_replace = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file},
    )
    res_replace = hook.execute(ctx_replace)

    # Then 1: must be denied with the exact required reason
    assert res_replace.decision == "deny"
    assert res_replace.reason == expected_reason
    assert "STOP. A prior surgical edit on this file failed" in (res_replace.reason or "")
    assert f"You MUST call 'view_file' on '{target_file}'" in (res_replace.reason or "")

    # When 2: agent attempts multi_replace_file_content on the locked file
    ctx_multi = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="multi_replace_file_content",
        tool_input={"TargetFile": target_file},
    )
    res_multi = hook.execute(ctx_multi)

    # Then 2: must also be denied
    assert res_multi.decision == "deny"
    assert res_multi.reason == expected_reason

    # When 3: agent attempts write_to_file on the locked file
    ctx_write = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="write_to_file",
        tool_input={"TargetFile": target_file, "Overwrite": True},
    )
    res_write = hook.execute(ctx_write)

    # Then 3: must also be denied
    assert res_write.decision == "deny"
    assert res_write.reason == expected_reason


def test_pre_tool_use_clears_lock_after_view_file_executed(
    isolated_state: SessionEditState,
) -> None:
    # Given: a file is currently locked due to prior failed edit
    cid = "conv-test-06"
    target_file = "src/locked.py"
    isolated_state.lock_file(cid, target_file, cwd="C:/test_project")
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is True

    hook = EditErrorRecoveryHook(state=isolated_state)

    # When 1: agent calls view_file on the locked file
    ctx_view = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="view_file",
        tool_input={"AbsolutePath": target_file},
    )
    res_view = hook.execute(ctx_view)

    # Then 1: view_file is allowed and lock is cleared
    assert res_view.decision == "allow"
    assert isolated_state.is_locked(cid, target_file, cwd="C:/test_project") is False

    # When 2: agent attempts a subsequent edit on the now-unlocked file
    ctx_edit = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": target_file},
    )
    res_edit = hook.execute(ctx_edit)

    # Then 2: subsequent edit is allowed!
    assert res_edit.decision == "allow"
    assert res_edit.reason is None


def test_distinct_files_do_not_block_each_other(
    isolated_state: SessionEditState,
) -> None:
    # Given: file_a failed edit and is locked
    cid = "conv-test-07"
    file_a = "src/file_a.py"
    file_b = "src/file_b.py"
    isolated_state.lock_file(cid, file_a, cwd="C:/test_project")

    hook = EditErrorRecoveryHook(state=isolated_state)

    # When: editing file_b
    ctx_b = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": file_b},
    )
    res_b = hook.execute(ctx_b)

    # Then: file_b is allowed
    assert res_b.decision == "allow"
    assert res_b.reason is None

    # And file_a remains locked
    assert isolated_state.is_locked(cid, file_a, cwd="C:/test_project") is True
    ctx_a = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": file_a},
    )
    res_a = hook.execute(ctx_a)
    assert res_a.decision == "deny"


def test_path_normalization_relative_and_absolute(
    isolated_state: SessionEditState,
) -> None:
    # Given: file locked via relative path under cwd
    cid = "conv-test-08"
    cwd = "C:/test_project"
    rel_path = "pkg/sub/module.py"
    abs_path = "C:/test_project/pkg/sub/module.py"
    isolated_state.lock_file(cid, rel_path, cwd=cwd)

    hook = EditErrorRecoveryHook(state=isolated_state)

    # When: checking edit with absolute path and backslashes
    ctx_abs = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd=cwd,
        tool_name="replace_file_content",
        tool_input={"TargetFile": "C:\\test_project\\pkg\\sub\\module.py"},
    )
    res_abs = hook.execute(ctx_abs)

    # Then: denied because normalized paths match
    assert res_abs.decision == "deny"

    # When: viewing the file with relative path
    ctx_view = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd=cwd,
        tool_name="view_file",
        tool_input={"AbsolutePath": rel_path},
    )
    res_view = hook.execute(ctx_view)
    assert res_view.decision == "allow"

    # Then: lock cleared for absolute path query as well
    assert isolated_state.is_locked(cid, abs_path, cwd=cwd) is False


def test_sessions_are_isolated(isolated_state: SessionEditState) -> None:
    # Given: file locked in session 1
    file_path = "src/shared.py"
    isolated_state.lock_file("session-1", file_path, cwd="C:/test_project")

    hook = EditErrorRecoveryHook(state=isolated_state)

    # When: session 2 tries to edit the same file
    ctx_session2 = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="session-2",
        cwd="C:/test_project",
        tool_name="replace_file_content",
        tool_input={"TargetFile": file_path},
    )
    res = hook.execute(ctx_session2)

    # Then: session 2 is allowed
    assert res.decision == "allow"
    assert res.reason is None


def test_ignores_unrelated_tools(isolated_state: SessionEditState) -> None:
    # Given: an error on a file
    cid = "conv-test-09"
    hook = EditErrorRecoveryHook(state=isolated_state)

    # When: running an unrelated tool like run_command
    ctx_pre = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="run_command",
        tool_input={"CommandLine": "dir"},
    )
    res_pre = hook.execute(ctx_pre)
    assert res_pre.decision == "allow"

    ctx_post = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id=cid,
        cwd="C:/test_project",
        tool_name="run_command",
        tool_input={"CommandLine": "dir"},
        tool_error="Command exited with 1",
    )
    res_post = hook.execute(ctx_post)
    assert res_post.additional_context is None


def test_registered_in_engine_default_pipeline() -> None:
    # Given: default pipelines
    HookEngine.clear_pipelines()
    pre_pipeline = HookEngine.create_default_pipeline(LifecycleEvent.PRE_TOOL_USE)
    post_pipeline = HookEngine.create_default_pipeline(LifecycleEvent.POST_TOOL_USE)

    # Then: EditErrorRecoveryHook is registered in both PRE_TOOL_USE and POST_TOOL_USE
    pre_names = [h.name for h in pre_pipeline.hooks]
    post_names = [h.name for h in post_pipeline.hooks]

    assert "edit_error_recovery" in pre_names
    assert "edit_error_recovery" in post_names


def test_engine_run_post_and_pre_tool_use_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given: temporary directory as state directory to isolate end-to-end run
    monkeypatch.setenv("ANTIGRAVITY_EDIT_RECOVERY_DIR", str(tmp_path / "state"))
    HookEngine.clear_pipelines()

    cid = "conv-e2e-edit-recovery"
    scratch_dir = tmp_path / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    target_file = str(scratch_dir / "code.py")

    # Step 1: POST_TOOL_USE with edit error
    post_payload = {
        "conversationId": cid,
        "cwd": str(tmp_path),
        "tool_name": "replace_file_content",
        "tool_input": {"TargetFile": target_file},
        "error": "Target chunk not found in code.py",
    }
    mock_stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", mock_stderr)
    exit_code = HookEngine.run(LifecycleEvent.POST_TOOL_USE, io.StringIO(json.dumps(post_payload)))
    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {}
    assert f"[EditErrorRecovery] Surgical edit failed on '{target_file}'" in mock_stderr.getvalue()

    # Step 2: PRE_TOOL_USE trying to write/edit the locked file without viewing
    pre_payload = {
        "conversationId": cid,
        "cwd": str(tmp_path),
        "tool_name": "replace_file_content",
        "tool_input": {"TargetFile": target_file},
    }
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO(json.dumps(pre_payload)))
    assert exit_code == 0
    captured_pre = capsys.readouterr()
    res_json = json.loads(captured_pre.out)
    assert res_json["decision"] == "deny"
    assert "STOP. A prior surgical edit on this file failed" in res_json["reason"]
    assert f"You MUST call 'view_file' on '{target_file}'" in res_json["reason"]

    # Step 3: PRE_TOOL_USE viewing the locked file
    view_payload = {
        "conversationId": cid,
        "cwd": str(tmp_path),
        "tool_name": "view_file",
        "tool_input": {"AbsolutePath": target_file},
    }
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO(json.dumps(view_payload)))
    assert exit_code == 0
    captured_view = capsys.readouterr()
    view_res = json.loads(captured_view.out)
    assert view_res["decision"] == "allow"

    # Step 4: PRE_TOOL_USE editing the now-unlocked file
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, io.StringIO(json.dumps(pre_payload)))
    assert exit_code == 0
    captured_post_view = capsys.readouterr()
    allow_res = json.loads(captured_post_view.out)
    assert allow_res["decision"] == "allow"


def test_edit_file_locks_on_error_and_read_file_unlocks(
    isolated_state: SessionEditState,
) -> None:
    cid = "conv-edit-file-flow"
    target = "src/payment.ts"
    hook = EditErrorRecoveryHook(state=isolated_state)

    # 1. edit_file with error locks the file
    ctx_edit = HookContext(
        lifecycle=LifecycleEvent.POST_TOOL_USE,
        conversation_id=cid,
        cwd="C:/project",
        tool_name="edit_file",
        tool_input={"Path": target, "Target": "old", "Replacement": "new"},
        tool_error="Target string not found",
    )
    res_edit = hook.execute(ctx_edit)
    assert res_edit.additional_context is not None
    assert "read_file" in res_edit.additional_context
    assert isolated_state.is_locked(cid, target, cwd="C:/project") is True

    # 2. pre_tool_use blocks write_file on locked file
    ctx_write = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/project",
        tool_name="write_file",
        tool_input={"Path": target, "Content": "new content"},
    )
    res_write = hook.execute(ctx_write)
    assert res_write.decision == "deny"
    assert "read_file" in (res_write.reason or "")

    # 3. read_file unlocks the file
    ctx_read = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd="C:/project",
        tool_name="read_file",
        tool_input={"Path": target},
    )
    res_read = hook.execute(ctx_read)
    assert res_read.decision == "allow"
    assert isolated_state.is_locked(cid, target, cwd="C:/project") is False

