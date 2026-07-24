from __future__ import annotations
from hooks.fsync_skip_warning import check_fsync_skip_warning

def test_fsync_skip_warning_dangerous_patterns():
    tests = [
        ("git push --force", "force push"),
        ("git push -f origin main", "force push"),
        ("rm -rf /tmp/test", "destructive remove"),
        ("DROP TABLE users", "SQL destructive"),
        ("git commit --no-verify", "bypasses git hooks"),
        ("git reset --hard HEAD~1", "hard reset"),
        ("git clean -fd", "clean working dir"),
    ]
    
    for cmd, pattern_name in tests:
        result = check_fsync_skip_warning("run_command", {"CommandLine": cmd})
        assert result is not None, f"Expected warning for '{cmd}'"
        assert result["permissionDecision"] == "ask"
        assert pattern_name in result["permissionDecisionReason"]

def test_fsync_skip_warning_safe_patterns():
    tests = [
        "echo hello world",
        "python -m pytest tests/",
        "git push origin main",
    ]
    
    for cmd in tests:
        result = check_fsync_skip_warning("run_command", {"CommandLine": cmd})
        assert result is None, f"Expected no warning for '{cmd}'"

def test_fsync_skip_warning_wrong_tool():
    result = check_fsync_skip_warning("other_tool", {"CommandLine": "rm -rf /"})
    assert result is None

def test_fsync_skip_warning_empty_command():
    result = check_fsync_skip_warning("run_command", {"CommandLine": ""})
    assert result is None
