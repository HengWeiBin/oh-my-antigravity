import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_INVOCATION = os.path.join(SCRIPT_DIR, "pre_invocation.py")
PRE_TOOL_USE = os.path.join(SCRIPT_DIR, "pre_tool_use.py")
POST_TOOL_USE = os.path.join(SCRIPT_DIR, "post_tool_use.py")

def run_script(script_path, payload):
    result = subprocess.run(
        [sys.executable, script_path],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        check=False
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {}

def test_pre_invocation_integration():
    payload = {
        "invocationNum": 15,
        "cwd": "/some/path",
        "workspacePaths": ["/some/path"]
    }
    result = run_script(PRE_INVOCATION, payload)
    assert "injectSteps" in result
    assert isinstance(result["injectSteps"], list)

def test_pre_tool_use_integration_run_command():
    payload = {
        "tool_name": "run_command",
        "tool_input": {
            "CommandLine": "rm -rf /"
        },
        "conversationId": "sys-123"
    }
    result = run_script(PRE_TOOL_USE, payload)
    assert result.get("decision") == "ask"
    assert "FSYNC WARNING" in result.get("reason", "")
    assert "permissionDecision" not in result
    
def test_pre_tool_use_integration_notepad():
    payload = {
        "tool_name": "write_to_file",
        "tool_input": {
            "TargetFile": "/.omo/notepads/test.md",
            "CodeContent": "short"
        },
        "conversationId": "sys-123"
    }
    result = run_script(PRE_TOOL_USE, payload)
    assert "decision" in result or not result
    
def test_post_tool_use_integration_invoke_subagent():
    payload = {
        "tool_name": "invoke_subagent",
        "tool_response": "done"
    }
    result = run_script(POST_TOOL_USE, payload)
    assert "additionalContext" in result
    assert "hookSpecificOutput" not in result
    assert "EMPTY SUBAGENT RESPONSE DETECTED" in result["additionalContext"]
    
def test_post_tool_use_integration_write_file():
    payload = {
        "tool_name": "write_to_file",
        "tool_input": {
            "TargetFile": "/.omo/plans/test.md",
            "CodeContent": "missing sections"
        },
        "tool_response": {}
    }
    result = run_script(POST_TOOL_USE, payload)
    assert "additionalContext" in result
    assert "hookSpecificOutput" not in result
    context = result["additionalContext"]
    assert "PLAN FORMAT VALIDATOR" in context or "COMMENT CHECKER" in context
