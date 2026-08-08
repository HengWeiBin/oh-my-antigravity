import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from hooks.comment_checker import check_comment_preservation


def test_python_with_comments():
    code = "\n".join([f"line {i}" for i in range(25)] + ["# a comment"])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.py", "CodeContent": code}, None)
    assert res is None

def test_python_no_comments():
    code = "\n".join([f"line {i}" for i in range(25)])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.py", "CodeContent": code}, None)
    assert res is not None
    assert "⚠️ COMMENT CHECKER" in res

def test_short_file():
    code = "\n".join([f"line {i}" for i in range(15)])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.py", "CodeContent": code}, None)
    assert res is None

def test_non_code_file():
    code = "\n".join([f"line {i}" for i in range(25)])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.md", "CodeContent": code}, None)
    assert res is None

def test_js_with_comments():
    code = "\n".join([f"line {i}" for i in range(25)] + ["// comment"])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.js", "CodeContent": code}, None)
    assert res is None

def test_js_no_comments():
    code = "\n".join([f"line {i}" for i in range(25)])
    res = check_comment_preservation("write_to_file", {"TargetFile": "test.js", "CodeContent": code}, None)
    assert res is not None
    assert "⚠️ COMMENT CHECKER" in res

def test_replace_file_content_with_comments():
    code = "\n".join([f"line {i}" for i in range(25)] + ["/* comment */"])
    res = check_comment_preservation("replace_file_content", {"TargetFile": "test.ts", "ReplacementContent": code}, None)
    assert res is None

def test_multi_replace_file_content_no_comments():
    code1 = "\n".join([f"line {i}" for i in range(15)])
    code2 = "\n".join([f"line {i}" for i in range(10)])
    res = check_comment_preservation(
        "multi_replace_file_content", 
        {"TargetFile": "test.py", "ReplacementChunks": [{"ReplacementContent": code1}, {"ReplacementContent": code2}]}, 
        None
    )
    assert res is not None
    assert "⚠️ COMMENT CHECKER" in res
