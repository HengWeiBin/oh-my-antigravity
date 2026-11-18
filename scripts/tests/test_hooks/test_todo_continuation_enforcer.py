import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from hooks.todo_continuation_enforcer import get_todo_continuation_messages


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as td:
        yield td

@pytest.fixture
def temp_artifact_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td

def create_plan_file(workspace: str, filename: str, content: str):
    plans_dir = os.path.join(workspace, ".omo", "plans")
    os.makedirs(plans_dir, exist_ok=True)
    filepath = os.path.join(plans_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def write_boulder(workspace: str, plan_filename: str, session_id: str = "conv-1", status: str = "active"):
    omo_dir = os.path.join(workspace, ".omo")
    os.makedirs(omo_dir, exist_ok=True)
    with open(os.path.join(omo_dir, "boulder.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": 2,
                "active_work_id": "w1",
                "works": {
                    "w1": {
                        "active_plan": f".omo/plans/{plan_filename}",
                        "session_ids": [session_id],
                        "status": status,
                    }
                },
            },
            f,
        )


def write_state(artifact_dir: str, state: dict):
    state_file = os.path.join(artifact_dir, "todo_continuation_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f)

def test_invocation_num_less_than_3(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 2,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "plan.md", "- [ ] task 1")
    write_boulder(temp_workspace, "plan.md", "conv-1")
    
    result = get_todo_continuation_messages(payload)
    assert result == []

def test_no_plan_files(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    
    result = get_todo_continuation_messages(payload)
    assert result == []

def test_plan_file_all_checked(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "plan.md", "- [x] task 1\n- [x] task 2")
    write_boulder(temp_workspace, "plan.md", "conv-1")
    
    result = get_todo_continuation_messages(payload)
    assert result == []

def test_plan_file_with_unchecked_first_time(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "plan.md", "- [ ] task 1\n- [x] task 2\n- [ ] task 3")
    write_boulder(temp_workspace, "plan.md", "conv-1")
    
    result = get_todo_continuation_messages(payload)
    assert len(result) == 1
    assert "🎯 TODO CONTINUATION ENFORCER" in result[0]["ephemeralMessage"]
    assert "[plan.md]" in result[0]["ephemeralMessage"]
    assert "- [ ] task 1" in result[0]["ephemeralMessage"]
    assert "- [ ] task 3" in result[0]["ephemeralMessage"]
    assert "- [x] task 2" not in result[0]["ephemeralMessage"]
    assert "AUTO-CONTINUE" in result[0]["ephemeralMessage"]
    assert "treat that refusal as final" in result[0]["ephemeralMessage"]

    # Check state file
    state_file = os.path.join(temp_artifact_dir, "todo_continuation_state.json")
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
        assert state["last_injection_invocation"] == 3
        assert state["last_unchecked_count"] == 2

def test_plan_file_with_in_progress_checkbox(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "wip.md", "- [~] in-progress task 1")
    write_boulder(temp_workspace, "wip.md", "codex:conv-1")
    result = get_todo_continuation_messages(payload)
    assert len(result) == 1
    assert "- [~] in-progress task 1" in result[0]["ephemeralMessage"]

def test_skip_review_files(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "feature-review.md", "- [ ] review comment")
    create_plan_file(temp_workspace, "code.review.md", "- [ ] another comment")
    write_boulder(temp_workspace, "feature-review.md", "conv-1")
    result = get_todo_continuation_messages(payload)
    assert result == []

def test_throttling_last_injection_recent(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 6,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "plan.md", "- [ ] task 1")
    write_boulder(temp_workspace, "plan.md", "conv-1")
    write_state(temp_artifact_dir, {"last_injection_invocation": 3, "last_unchecked_count": 1})
    
    result = get_todo_continuation_messages(payload)
    assert result == []

def test_throttling_past_5_invocations(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 8,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace]
    }
    create_plan_file(temp_workspace, "plan.md", "- [ ] task 1")
    write_boulder(temp_workspace, "plan.md", "conv-1")
    write_state(temp_artifact_dir, {"last_injection_invocation": 3, "last_unchecked_count": 1})
    
    result = get_todo_continuation_messages(payload)
    assert len(result) == 1
    
    # State should be updated
    state_file = os.path.join(temp_artifact_dir, "todo_continuation_state.json")
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
        assert state["last_injection_invocation"] == 8


def test_ignores_missing_or_unbound_boulder(temp_workspace, temp_artifact_dir):
    payload = {
        "invocationNum": 3,
        "conversationId": "conv-1",
        "artifactDirectoryPath": temp_artifact_dir,
        "workspacePaths": [temp_workspace],
    }
    create_plan_file(temp_workspace, "plan.md", "- [ ] task 1")

    # Missing boulder.json
    assert get_todo_continuation_messages(payload) == []

    # Different session
    write_boulder(temp_workspace, "plan.md", "other-conv")
    assert get_todo_continuation_messages(payload) == []

    # Completed status
    write_boulder(temp_workspace, "plan.md", "conv-1", status="completed")
    assert get_todo_continuation_messages(payload) == []
