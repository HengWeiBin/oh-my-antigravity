import os
import sys

# Ensure the module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from hooks.notepad_write_guard import check_notepad_write_guard

def test_non_notepad_file():
    tool_input = {
        "TargetFile": "/path/to/normal/file.txt",
        "CodeContent": "short"
    }
    assert check_notepad_write_guard("write_to_file", tool_input) is None

def test_notepad_file_targeted_edit():
    tool_input = {
        "TargetFile": "/path/.omo/notepads/notes.md",
        "TargetContent": "old",
        "ReplacementContent": "new"
    }
    assert check_notepad_write_guard("replace_file_content", tool_input) is None

def test_notepad_file_does_not_exist(tmp_path):
    target = tmp_path / ".omo" / "notepads" / "notes.md"
    tool_input = {
        "TargetFile": str(target),
        "CodeContent": "new content"
    }
    assert check_notepad_write_guard("write_to_file", tool_input) is None

def test_notepad_file_empty_existing(tmp_path):
    target = tmp_path / ".omo" / "notepads" / "notes.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    
    tool_input = {
        "TargetFile": str(target),
        "CodeContent": "new content"
    }
    assert check_notepad_write_guard("write_to_file", tool_input) is None

def test_notepad_write_allow(tmp_path):
    target = tmp_path / ".omo" / "notepads" / "notes.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("a" * 100, encoding="utf-8")
    
    # 50 chars is >= 50%
    tool_input = {
        "TargetFile": str(target),
        "CodeContent": "b" * 50
    }
    assert check_notepad_write_guard("write_to_file", tool_input) is None

def test_notepad_write_deny(tmp_path):
    target = tmp_path / ".omo" / "notepads" / "notes.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("a" * 100, encoding="utf-8")
    
    # 49 chars is < 50%
    tool_input = {
        "TargetFile": str(target),
        "CodeContent": "b" * 49
    }
    
    result = check_notepad_write_guard("write_to_file", tool_input)
    assert result is not None
    assert result.get("permissionDecision") == "deny"
    assert "reduce the notepad content by >50%" in result.get("permissionDecisionReason")
