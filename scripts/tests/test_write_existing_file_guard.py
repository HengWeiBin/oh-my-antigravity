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

from scripts.hooks.engine import HookEngine
from scripts.hooks.models import HookContext, LifecycleEvent
from scripts.hooks.write_existing_file_guard import WriteExistingFileGuardHook


def test_blocks_unread_overwrite_of_existing_non_empty_file(tmp_path: Path) -> None:
    # Given: an existing non-empty file and an empty transcript
    target_file = tmp_path / "existing.py"
    target_file.write_text("print('original content')", encoding="utf-8")

    brain_dir = tmp_path / "brain"
    cid = "test-conv-001"
    logs_dir = brain_dir / cid / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"
    transcript_file.write_text("", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "print('overwritten')",
        },
        raw_payload={
            "conversationId": cid,
            "artifactDirectoryPath": str(brain_dir / cid),
        },
    )

    # When: executing the write existing file guard
    result = hook.execute(ctx)

    # Then: overwrite must be denied
    assert result.decision == "deny"
    assert "STOP. Overwriting an existing non-empty file without inspecting it first is prohibited" in (
        result.reason or ""
    )
    assert str(target_file) in (result.reason or "")


def test_allows_write_when_file_does_not_exist(tmp_path: Path) -> None:
    # Given: a file path that does not exist on disk
    target_file = tmp_path / "new_file.py"
    assert not target_file.exists()

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "print('hello')",
        },
        raw_payload={},
    )

    # When: executing the guard
    result = hook.execute(ctx)

    # Then: allow write
    assert result.decision == "allow"


def test_allows_write_when_file_is_empty(tmp_path: Path) -> None:
    # Given: an existing file of 0 bytes
    target_file = tmp_path / "empty.py"
    target_file.write_text("", encoding="utf-8")
    assert target_file.stat().st_size == 0

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "print('hello')",
        },
        raw_payload={},
    )

    # When: executing the guard
    result = hook.execute(ctx)

    # Then: allow write
    assert result.decision == "allow"


def test_allows_write_when_overwrite_is_false_or_missing(tmp_path: Path) -> None:
    # Given: an existing non-empty file, but Overwrite is False or omitted
    target_file = tmp_path / "existing.py"
    target_file.write_text("code", encoding="utf-8")

    hook = WriteExistingFileGuardHook()

    # Case 1: Overwrite is False
    ctx_false = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": False,
            "CodeContent": "append",
        },
        raw_payload={},
    )
    result_false = hook.execute(ctx_false)
    assert result_false.decision == "allow"

    # Case 2: Overwrite not set
    ctx_missing = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "CodeContent": "append",
        },
        raw_payload={},
    )
    result_missing = hook.execute(ctx_missing)
    assert result_missing.decision == "allow"


def test_allows_writes_to_exempted_paths_omo(tmp_path: Path) -> None:
    # Given: a non-empty file under .omo/
    omo_dir = tmp_path / ".omo" / "notepads"
    omo_dir.mkdir(parents=True)
    target_file = omo_dir / "notes.md"
    target_file.write_text("notes", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "updated notes",
        },
        raw_payload={},
    )

    # When: executing guard
    result = hook.execute(ctx)

    # Then: allow write to .omo path
    assert result.decision == "allow"


def test_allows_writes_to_exempted_paths_scratch(tmp_path: Path) -> None:
    # Given: a non-empty file under .scratch/
    scratch_dir = tmp_path / ".scratch" / "tasks"
    scratch_dir.mkdir(parents=True)
    target_file = scratch_dir / "task1.md"
    target_file.write_text("task spec", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "updated task spec",
        },
        raw_payload={},
    )

    # When: executing guard
    result = hook.execute(ctx)

    # Then: allow write to .scratch path
    assert result.decision == "allow"


def test_allows_writes_to_exempted_paths_artifact_dir(tmp_path: Path) -> None:
    # Given: a non-empty file under conversation artifactDirectoryPath
    artifact_dir = tmp_path / "brain" / "conv-art-001"
    artifact_dir.mkdir(parents=True)
    target_file = artifact_dir / "summary.md"
    target_file.write_text("previous summary", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-art-001",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "new summary",
        },
        raw_payload={
            "conversationId": "conv-art-001",
            "artifactDirectoryPath": str(artifact_dir),
        },
    )

    # When: executing guard
    result = hook.execute(ctx)

    # Then: allow write to artifact directory path
    assert result.decision == "allow"


def test_allows_overwrite_when_file_previously_viewed_via_view_file(tmp_path: Path) -> None:
    # Given: an existing file and transcript with a prior view_file call
    target_file = tmp_path / "inspected_code.py"
    target_file.write_text("def run(): pass", encoding="utf-8")

    brain_dir = tmp_path / "brain"
    cid = "conv-view-001"
    logs_dir = brain_dir / cid / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"

    view_file_step = {
        "step_index": 1,
        "type": "PLANNER_RESPONSE",
        "tool_calls": [
            {
                "name": "view_file",
                "args": {
                    "AbsolutePath": str(target_file),
                },
            }
        ],
    }
    transcript_file.write_text(json.dumps(view_file_step) + "\n", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "def run(): print('new')",
        },
        raw_payload={
            "conversationId": cid,
            "artifactDirectoryPath": str(brain_dir / cid),
        },
    )

    # When: executing guard
    result = hook.execute(ctx)

    # Then: allow write because file was inspected
    assert result.decision == "allow"


def test_allows_overwrite_when_file_previously_written_in_session(tmp_path: Path) -> None:
    # Given: an existing file created/modified earlier in this session
    target_file = tmp_path / "generated_code.py"
    target_file.write_text("def gen(): pass", encoding="utf-8")

    brain_dir = tmp_path / "brain"
    cid = "conv-write-001"
    logs_dir = brain_dir / cid / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"

    write_step = {
        "step_index": 2,
        "type": "PLANNER_RESPONSE",
        "tool_calls": [
            {
                "name": "write_to_file",
                "args": {
                    "TargetFile": str(target_file),
                    "CodeContent": "def gen(): pass",
                },
            }
        ],
    }
    transcript_file.write_text(json.dumps(write_step) + "\n", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id=cid,
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "def gen(): print('regenerated')",
        },
        raw_payload={
            "conversationId": cid,
            "artifactDirectoryPath": str(brain_dir / cid),
        },
    )

    # When: executing guard
    result = hook.execute(ctx)

    # Then: allow write because file was written earlier in this session
    assert result.decision == "allow"


def test_allows_non_write_to_file_tools(tmp_path: Path) -> None:
    # Given: a non-write_to_file tool like replace_file_content or run_command
    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-1",
        cwd=str(tmp_path),
        tool_name="replace_file_content",
        tool_input={"TargetFile": "something.py"},
        raw_payload={},
    )
    result = hook.execute(ctx)
    assert result.decision == "allow"


def test_blocks_case_insensitive_string_overwrite(tmp_path: Path) -> None:
    # Given: an existing file and Overwrite="true" string
    target_file = tmp_path / "test.txt"
    target_file.write_text("hello", encoding="utf-8")

    hook = WriteExistingFileGuardHook()
    ctx = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="conv-str",
        cwd=str(tmp_path),
        tool_name="write_to_file",
        tool_input={
            "TargetFile": str(target_file),
            "Overwrite": "True",
            "CodeContent": "overwritten",
        },
        raw_payload={},
    )
    result = hook.execute(ctx)
    assert result.decision == "deny"


def test_registered_in_engine_default_pipeline() -> None:
    # Given: default pipeline for PRE_TOOL_USE
    HookEngine.clear_pipelines()
    pipeline = HookEngine.create_default_pipeline(LifecycleEvent.PRE_TOOL_USE)

    # Then: WriteExistingFileGuardHook is registered
    hook_names = [h.name for h in pipeline.hooks]
    assert "write_existing_file_guard" in hook_names


def test_engine_run_denies_unread_overwrite_via_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given: an existing non-empty file
    target_file = tmp_path / "important.py"
    target_file.write_text("critical = True\n", encoding="utf-8")

    HookEngine.clear_pipelines()
    payload = {
        "conversationId": "engine-test-conv",
        "cwd": str(tmp_path),
        "tool_name": "write_to_file",
        "tool_input": {
            "TargetFile": str(target_file),
            "Overwrite": True,
            "CodeContent": "critical = False\n",
        },
    }
    input_stream = io.StringIO(json.dumps(payload))

    # When: running HookEngine.run
    exit_code = HookEngine.run(LifecycleEvent.PRE_TOOL_USE, input_stream)
    captured = capsys.readouterr()
    result = json.loads(captured.out)

    # Then: denied by write_existing_file_guard
    assert exit_code == 0
    assert result.get("decision") == "deny"
    assert "STOP. Overwriting an existing non-empty file without inspecting it first" in result.get(
        "reason", ""
    )

