---
name: antigravity-hooks
description: Guide and best practices for creating, configuring, and testing Google Antigravity Hooks (PreInvocation, PostInvocation, PreToolUse, PostToolUse, Stop). Use this skill when asked to define, create, inspect, debug, or write hooks.json configurations and hook script files.
---

# Google Antigravity Hooks Guide

Google Antigravity Hooks provide a powerful event-driven mechanism to intercept, evaluate, modify, gate, or inject behaviors into agent lifecycles. This guide details hook configuration, event payloads, response contracts, matcher rules, production-ready Python script templates, and troubleshooting strategies.

---

## 1. Configuration & Scope

Hooks are configured in `hooks.json` files and resolution occurs across three scope levels:

| Scope | Location | Purpose |
|---|---|---|
| **Global** | `~/.gemini/config/hooks.json` | Applies across all projects and sessions for the user. |
| **Workspace** | `.agents/hooks.json` | Scoped specifically to the current workspace repository. |
| **Plugin** | `hooks.json` (Plugin root directory) | Bundled inside a plugin to extend agent lifecycle capabilities. |

### `hooks.json` Structure & Configuration Blocks

Hook definitions are grouped by event name (`PreInvocation`, `PostInvocation`, `PreToolUse`, `PostToolUse`, `Stop`). Individual hook entries support explicit `"enabled"` boolean toggles:

```json
{
  "hooks": {
    "PreInvocation": [
      {
        "name": "context_injector",
        "enabled": true,
        "type": "command",
        "command": "python C:/path/to/scripts/pre_invocation.py",
        "timeout": 8
      }
    ],
    "PostInvocation": [
      {
        "name": "loop_evaluator",
        "enabled": true,
        "type": "command",
        "command": "python C:/path/to/scripts/post_invocation.py",
        "timeout": 10
      }
    ],
    "PreToolUse": [
      {
        "name": "tool_security_gate",
        "enabled": true,
        "matcher": "^(run_command|write_to_file|replace_file_content|multi_replace_file_content)$",
        "hooks": [
          {
            "enabled": true,
            "type": "command",
            "command": "python C:/path/to/scripts/pre_tool_use.py",
            "timeout": 5
          }
        ]
      },
      {
        "name": "browser_guard",
        "enabled": true,
        "matcher": "browser_.*",
        "hooks": [
          {
            "enabled": true,
            "type": "command",
            "command": "python C:/path/to/scripts/browser_guard.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "name": "post_tool_verifier",
        "enabled": true,
        "matcher": "*",
        "hooks": [
          {
            "enabled": true,
            "type": "command",
            "command": "python C:/path/to/scripts/post_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "name": "session_cleanup",
        "enabled": true,
        "type": "command",
        "command": "python C:/path/to/scripts/stop.py",
        "timeout": 5
      }
    ]
  }
}
```

### Matcher Rules (`PreToolUse` & `PostToolUse`)

For tool-specific hooks (`PreToolUse`, `PostToolUse`), the `matcher` property defines target tool matching via Regular Expressions:

- **Wildcard Matcher (`*` or `.*`)**: Matches every tool call.
- **Exact / Group Matching (`run_command|write_to_file`)**: Matches designated tool names.
- **Prefix / Pattern Matching (`browser_.*`)**: Matches tool families sharing a common prefix (e.g. `browser_click`, `browser_navigate`).

---

## 2. Complete Lifecycle Hooks & Specifications

### A. `PreInvocation`
- **Trigger**: Executed immediately before sending the prompt payload to the LLM model.
- **Stdin Payload**:
  ```json
  {
    "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "invocationNum": 1,
    "cwd": "C:/Users/WBSC1/project",
    "workspacePaths": ["C:/Users/WBSC1/project"],
    "artifactDirectoryPath": "C:/Users/WBSC1/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "transcriptPath": "C:/Users/WBSC1/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript_full.jsonl",
    "isSubagent": false
  }
  ```
- **Stdout Response Contract**:
  ```json
  {
    "injectSteps": [
      {
        "ephemeralMessage": "System context injected for this invocation."
      },
      {
        "userMessage": "Synthetic user prompt step."
      },
      {
        "toolCall": {
          "name": "view_file",
          "args": { "AbsolutePath": "C:/project/README.md" }
        }
      }
    ]
  }
  ```

### B. `PostInvocation`
- **Trigger**: Executed directly after the model returns a response, prior to executing emitted tool calls.
- **Stdin Payload**:
  ```json
  {
    "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "invocationNum": 1,
    "cwd": "C:/Users/WBSC1/project",
    "transcriptPath": "C:/Users/WBSC1/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript_full.jsonl",
    "response": {
      "text": "Model generated response summary",
      "toolCalls": [
        { "name": "run_command", "args": { "CommandLine": "npm test" } }
      ]
    },
    "usage": { "promptTokens": 1200, "completionTokens": 350 }
  }
  ```
- **Stdout Response Contract**:
  ```json
  {
    "decision": "force_continue",
    "injectSteps": [
      {
        "ephemeralMessage": "Notice: Further verification step required."
      }
    ]
  }
  ```
  - **Loop Control `decision` Values**:
    - `"force_continue"`: Forces another iteration loop even if no tool call was emitted.
    - `"terminate"`: Immediately halts execution loop.

### C. `PreToolUse`
- **Trigger**: Executed before running a requested tool call. Used for permission gating, validation, and argument safety.
- **Stdin Payload**:
  ```json
  {
    "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "invocationNum": 1,
    "cwd": "C:/Users/WBSC1/project",
    "toolCall": {
      "name": "run_command",
      "args": {
        "CommandLine": "rm -rf /",
        "Cwd": "C:/Users/WBSC1/project"
      }
    }
  }
  ```
- **Stdout Response Contract**:
  ```json
  {
    "decision": "deny",
    "reason": "Destructive command pattern detected.",
    "permissionOverrides": {}
  }
  ```
  - **Tool Gating `decision` Enum Values**:
    - `"allow"`: Permitted to proceed.
    - `"deny"`: Aborts tool execution and returns reason to model.
    - `"ask"`: Prompts user for approval before running.
    - `"force_ask"`: Forces manual confirmation regardless of automated rules.
    - `"deny_unless_prior_grant"`: Denies unless prior explicit permission exists.

### D. `PostToolUse`
- **Trigger**: Executed immediately after tool execution completes.
- **Stdin Payload**:
  ```json
  {
    "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "stepIndex": 3,
    "toolCall": {
      "name": "write_to_file",
      "args": { "TargetFile": "C:/Users/WBSC1/project/src/index.js" }
    },
    "result": { "status": "success" },
    "error": "Runtime failure error message if applicable, otherwise null or empty string"
  }
  ```
- **Stdout Response Contract**:
  ```json
  {}
  ```

### E. `Stop`
- **Trigger**: Executed when the agent session or loop terminates.
- **Stdin Payload**:
  ```json
  {
    "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
    "stopReason": "completed",
    "cwd": "C:/Users/WBSC1/project",
    "transcriptPath": "C:/Users/WBSC1/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript_full.jsonl"
  }
  ```
- **Stdout Response Contract**:
  ```json
  {}
  ```

---

## 3. Production-Ready Python Script Templates

All script templates include explicit UTF-8 stream handling, cross-platform path normalization, defensive JSON processing, and standard error handling.

### 1. `pre_invocation.py`

```python
#!/usr/bin/env python3
"""
PreInvocation Hook Script Template
Injects context or steps prior to LLM invocation.
"""

import json
import os
import sys
from pathlib import Path

def setup_utf8():
    """Ensure standard IO streams use UTF-8 encoding across platforms."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

def main():
    setup_utf8()
    output = {"injectSteps": []}
    
    try:
        raw_input = sys.stdin.read().strip()
        payload = json.loads(raw_input) if raw_input else {}
        
        conversation_id = payload.get("conversationId", "")
        invocation_num = payload.get("invocationNum", 0)
        cwd = Path(payload.get("cwd", "")).resolve() if payload.get("cwd") else None
        
        # Example logic: Inject initialization step on first invocation
        if invocation_num == 0:
            output["injectSteps"].append({
                "ephemeralMessage": f"Session initialized in workspace: {cwd}"
            })
            
    except Exception as err:
        # Diagnostic logs to stderr only
        sys.stderr.write(f"[pre_invocation.py] Error: {err}\n")
        output = {"injectSteps": []}
        
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 2. `pre_tool_use.py`

```python
#!/usr/bin/env python3
"""
PreToolUse Hook Script Template
Inspects tool invocations and evaluates tool gating decisions.
"""

import json
import re
import sys

BLOCKED_COMMAND_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"mkfs",
    r"dd\s+if=",
    r">:?\s*/dev/sd"
]

def setup_utf8():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

def main():
    setup_utf8()
    response = {"decision": "allow"}
    
    try:
        raw_input = sys.stdin.read().strip()
        payload = json.loads(raw_input) if raw_input else {}
        
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            for pattern in BLOCKED_COMMAND_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    response = {
                        "decision": "deny",
                        "reason": f"Execution blocked: Command matches dangerous pattern '{pattern}'."
                    }
                    break
                    
    except Exception as err:
        sys.stderr.write(f"[pre_tool_use.py] Error: {err}\n")
        response = {"decision": "allow"}  # Safe fallback
        
    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 3. `post_tool_use.py`

```python
#!/usr/bin/env python3
"""
PostToolUse Hook Script Template
Processes tool execution outcomes or performs post-run audits.
"""

import json
import sys

def setup_utf8():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

def main():
    setup_utf8()
    response = {}
    
    try:
        raw_input = sys.stdin.read().strip()
        payload = json.loads(raw_input) if raw_input else {}
        
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        error = payload.get("error")
        
        if error:
            sys.stderr.write(f"[post_tool_use.py] Tool '{tool_name}' failed with error: {error}\n")
        else:
            # Custom post-tool audit or cleanup
            pass
            
    except Exception as err:
        sys.stderr.write(f"[post_tool_use.py] Error: {err}\n")
        response = {}
        
    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 4. `post_invocation.py`

```python
#!/usr/bin/env python3
"""
PostInvocation Hook Script Template
Evaluates LLM response content and specifies loop control decisions.
"""

import json
import sys

def setup_utf8():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

def main():
    setup_utf8()
    response = {}
    
    try:
        raw_input = sys.stdin.read().strip()
        payload = json.loads(raw_input) if raw_input else {}
        
        model_response = payload.get("response", {})
        text_content = model_response.get("text", "")
        tool_calls = model_response.get("toolCalls", [])
        
        # Example condition: force loop continuation if model flagged a retry requirement
        if "RETRY_NEEDED" in text_content and not tool_calls:
            response = {
                "decision": "force_continue",
                "injectSteps": [
                    {
                        "ephemeralMessage": "Automatic continuation triggered by PostInvocation hook."
                    }
                ]
            }
            
    except Exception as err:
        sys.stderr.write(f"[post_invocation.py] Error: {err}\n")
        response = {}
        
    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 5. `stop.py`

```python
#!/usr/bin/env python3
"""
Stop Hook Script Template
Handles clean-up and notification when an agent session ends.
"""

import json
import sys

def setup_utf8():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

def main():
    setup_utf8()
    response = {}
    
    try:
        raw_input = sys.stdin.read().strip()
        payload = json.loads(raw_input) if raw_input else {}
        
        conversation_id = payload.get("conversationId", "")
        stop_reason = payload.get("stopReason", "unknown")
        
        sys.stderr.write(f"[stop.py] Session {conversation_id} stopped: {stop_reason}\n")
        
    except Exception as err:
        sys.stderr.write(f"[stop.py] Error: {err}\n")
        response = {}
        
    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

---

## 4. Best Practices & Troubleshooting

### 1. Standard Output (`stdout`) Cleanliness
- **Only output valid JSON on `stdout`.** Any non-JSON text printed to `stdout` will cause JSON parsing errors in the agent runtime.
- Direct all diagnostic prints, warnings, and log messages to `sys.stderr`.

### 2. Cross-Platform UTF-8 Streams
- Windows terminals and default Python stream wrappers may use system code pages (e.g. CP1252/CP950).
- Always use `sys.stdin.reconfigure(encoding='utf-8')` and `sys.stdout.reconfigure(encoding='utf-8')`, or explicitly set `encoding='utf-8'` on file reads/writes.

### 3. Execution Timeouts
- Hooks must complete quickly to prevent agent loop latency.
- Set conservative `timeout` values in `hooks.json` (e.g. 3-8 seconds) and ensure hook scripts do not block on remote I/O indefinitely.

### 4. Path Normalization
- Use `pathlib.Path` or `os.path.normpath` for cross-platform path handling.
- Use forward slashes (`/`) or escaped backslashes (`\\\\`) in Windows paths within `hooks.json`.

### 5. Subagent Awareness
- Check for `isSubagent` or `parentConversationId` fields in the stdin payload to distinguish top-level sessions from subagent invocations.

### 6. Troubleshooting Matrix

| Issue | Cause | Action |
|---|---|---|
| Hook not firing | Path wrong, matcher misconfigured, or `"enabled": false` | Verify path accuracy, matcher regex test, and ensure `"enabled": true`. |
| Agent runtime JSON error | Non-JSON printed to `stdout` by hook script | Ensure all print/debug statements log to `sys.stderr` only. |
| Timeout abort | Script waiting on input or blocked on network/disk | Use fast non-blocking reads (`sys.stdin.read()`) and avoid slow network operations. |
