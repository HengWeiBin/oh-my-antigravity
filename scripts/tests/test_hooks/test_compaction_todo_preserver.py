from hooks.compaction_todo_preserver import get_compaction_todo_messages

def test_invocation_num_less_than_15():
    assert get_compaction_todo_messages({"invocationNum": 14}) == []

def test_no_omo_plans(tmp_path):
    payload = {
        "invocationNum": 15,
        "workspacePaths": [str(tmp_path)]
    }
    assert get_compaction_todo_messages(payload) == []

def test_plan_with_unchecked_items(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    plan_file = plans_dir / "my_plan.md"
    plan_file.write_text("- [ ] task 1\n- [x] task 2\n- [ ] task 3\n", encoding="utf-8")

    payload = {
        "invocationNum": 15,
        "workspacePaths": [str(tmp_path)]
    }
    messages = get_compaction_todo_messages(payload)
    assert len(messages) == 1
    assert "🔄 COMPACTION TODO PRESERVER:" in messages[0]["ephemeralMessage"]
    assert "[my_plan.md]" in messages[0]["ephemeralMessage"]
    assert "- [ ] task 1" in messages[0]["ephemeralMessage"]
    assert "- [ ] task 3" in messages[0]["ephemeralMessage"]
    assert "- [x] task 2" not in messages[0]["ephemeralMessage"]

def test_plan_with_all_items_checked(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    plan_file = plans_dir / "my_plan.md"
    plan_file.write_text("- [x] task 1\n- [x] task 2\n", encoding="utf-8")

    payload = {
        "invocationNum": 15,
        "workspacePaths": [str(tmp_path)]
    }
    assert get_compaction_todo_messages(payload) == []

def test_multiple_plan_files(tmp_path):
    plans_dir = tmp_path / ".omo" / "plans"
    plans_dir.mkdir(parents=True)
    
    (plans_dir / "plan1.md").write_text("- [ ] task 1\n", encoding="utf-8")
    (plans_dir / "plan2.md").write_text("- [ ] task 2\n", encoding="utf-8")
    (plans_dir / "plan3.md").write_text("- [ ] task 3\n", encoding="utf-8")
    (plans_dir / "plan4.md").write_text("- [ ] task 4\n", encoding="utf-8")

    payload = {
        "invocationNum": 15,
        "cwd": str(tmp_path)
    }
    messages = get_compaction_todo_messages(payload)
    assert len(messages) == 3
