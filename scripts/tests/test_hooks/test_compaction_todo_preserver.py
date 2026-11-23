import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from hooks.compaction_todo_preserver import get_compaction_todo_messages


def _write_boulder(workspace, data):
    omo_dir = workspace / ".omo"
    omo_dir.mkdir(parents=True, exist_ok=True)
    (omo_dir / "boulder.json").write_text(json.dumps(data), encoding="utf-8")


def test_invocation_num_less_than_15():
    assert get_compaction_todo_messages({"invocationNum": 14}) == []


def test_no_omo_plans(tmp_path):
    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    assert get_compaction_todo_messages(payload) == []


def test_plan_with_unchecked_items(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    plan_file = plans_dir / "my_plan.md"
    plan_file.write_text("- [ ] task 1\n- [x] task 2\n- [ ] task 3\n", encoding="utf-8")
    _write_boulder(
        tmp_path,
        {
            "active_plan": ".omo/plans/my_plan.md",
            "session_ids": ["c1"],
        },
    )

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    messages = get_compaction_todo_messages(payload)
    assert len(messages) == 1
    assert "🔄 COMPACTION TODO PRESERVER:" in messages[0]["systemMessage"]["systemMessage"]
    assert "[my_plan.md]" in messages[0]["systemMessage"]["systemMessage"]
    assert "- [ ] task 1" in messages[0]["systemMessage"]["systemMessage"]
    assert "- [ ] task 3" in messages[0]["systemMessage"]["systemMessage"]
    assert "- [x] task 2" not in messages[0]["systemMessage"]["systemMessage"]


def test_plan_with_in_progress_items(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    plan_file = plans_dir / "wip_plan.md"
    plan_file.write_text("- [~] task in progress\n* [~] star in progress\n", encoding="utf-8")
    _write_boulder(
        tmp_path,
        {
            "schema_version": 2,
            "works": {
                "w1": {
                    "active_plan": ".omo/plans/wip_plan.md",
                    "session_ids": ["codex:c1"],
                    "status": "active",
                }
            },
        },
    )

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    messages = get_compaction_todo_messages(payload)
    assert len(messages) == 1
    assert "- [~] task in progress" in messages[0]["systemMessage"]["systemMessage"]
    assert "* [~] star in progress" in messages[0]["systemMessage"]["systemMessage"]


def test_skip_review_files(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "plan-review.md").write_text("- [ ] unchecked review item\n", encoding="utf-8")
    (plans_dir / "code.review.md").write_text("- [ ] unchecked review item 2\n", encoding="utf-8")
    _write_boulder(
        tmp_path,
        {
            "schema_version": 2,
            "works": {
                "w1": {"active_plan": ".omo/plans/plan-review.md", "session_ids": ["c1"]},
                "w2": {"active_plan": ".omo/plans/code.review.md", "session_ids": ["c1"]},
            },
        },
    )

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    assert get_compaction_todo_messages(payload) == []


def test_plan_with_all_items_checked(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    plan_file = plans_dir / "my_plan.md"
    plan_file.write_text("- [x] task 1\n- [x] task 2\n", encoding="utf-8")
    _write_boulder(
        tmp_path,
        {
            "active_plan": ".omo/plans/my_plan.md",
            "session_ids": ["c1"],
        },
    )

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    assert get_compaction_todo_messages(payload) == []


def test_multiple_plan_files(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)

    (plans_dir / "plan1.md").write_text("- [ ] task 1\n", encoding="utf-8")
    (plans_dir / "plan2.md").write_text("- [ ] task 2\n", encoding="utf-8")
    (plans_dir / "plan3.md").write_text("- [ ] task 3\n", encoding="utf-8")
    (plans_dir / "plan4.md").write_text("- [ ] task 4\n", encoding="utf-8")
    _write_boulder(
        tmp_path,
        {
            "schema_version": 2,
            "works": {
                "w1": {"active_plan": ".omo/plans/plan1.md", "session_ids": ["c1"]},
                "w2": {"active_plan": ".omo/plans/plan2.md", "session_ids": ["c1"]},
                "w3": {"active_plan": ".omo/plans/plan3.md", "session_ids": ["c1"]},
                "w4": {"active_plan": ".omo/plans/plan4.md", "session_ids": ["c1"]},
            },
        },
    )

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "cwd": str(tmp_path),
    }
    messages = get_compaction_todo_messages(payload)
    assert len(messages) == 3


def test_ignores_missing_boulder_or_different_session(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "my_plan.md").write_text("- [ ] task 1\n", encoding="utf-8")

    payload = {
        "invocationNum": 15,
        "conversationId": "c1",
        "workspacePaths": [str(tmp_path)],
    }
    assert get_compaction_todo_messages(payload) == []

    _write_boulder(
        tmp_path,
        {
            "active_plan": ".omo/plans/my_plan.md",
            "session_ids": ["other-session"],
        },
    )
    assert get_compaction_todo_messages(payload) == []
