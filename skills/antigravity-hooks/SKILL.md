---
name: antigravity-hooks
description: Guide and best practices for creating, configuring, and testing Google Antigravity Hooks (PreInvocation, PreToolUse, PostToolUse). Use this skill when asked to define, create, inspect, debug, or write hooks.json configurations and hook script files (e.g. pre_invocation.py, pre_tool_use.py, post_tool_use.py) in the plugin directory.
---

# Google Antigravity Hooks Guide

This skill provides the structure, payloads, configurations, and scripts for writing, testing, and debugging Antigravity Hooks.

## 1. Structure of hooks.json

Hooks are registered in `hooks.json` at the plugin root directory. The file maps hook lifecycle events to executable commands.

```json
{
  "hooks": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "python C:/path/to/your/scripts/pre_invocation.py",
        "timeout": 5
      }
    ],
    "PreToolUse": [
      {
        "matcher": "^(write_to_file|replace_file_content|multi_replace_file_content)$",
        "hooks": [
          {
            "type": "command",
            "command": "python C:/path/to/your/scripts/pre_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^invoke_subagent$",
        "hooks": [
          {
            "type": "command",
            "command": "python C:/path/to/your/scripts/post_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Lifecycle Hook Types
- **PreInvocation**: Triggered right before the agent calls the model. Can inject steps/messages.
- **PreToolUse**: Triggered right before a specific tool (matching `matcher` regex) is executed.
- **PostToolUse**: Triggered right after a specific tool (matching `matcher` regex) is executed.

---

## 2. PreInvocation Hook Logic

### Payload Format (stdin)
The hook receives a JSON payload on `stdin` containing:

```json
{
  "conversationId": "2974575c-742a-41af-b183-d497f0405a1f",
  "invocationNum": 0,
  "cwd": "C:/Users/.../workspace",
  "workspacePaths": ["C:/Users/.../workspace"],
  "artifactDirectoryPath": "C:/Users/.../brain/conversationId",
  "transcriptPath": "C:/Users/.../brain/conversationId/.system_generated/logs/transcript_full.jsonl"
}
```

### Expected Output Format (stdout)
The script must print a JSON string to `stdout` containing `injectSteps`. Any other standard print should be redirected or silenced.

```json
{
  "injectSteps": [
    {
      "ephemeralMessage": "Your custom injected text to prompt/system message."
    }
  ]
}
```

### Python Template for PreInvocation

Create the script `scripts/pre_invocation.py`:

```python
import json
import os
import sys

def main():
    try:
        # 1. Read input JSON
        input_data = sys.stdin.read().strip()
        payload = json.loads(input_data) if input_data else {}
        
        # 2. Extract context
        invocation_num = payload.get("invocationNum", 0)
        workspace_paths = payload.get("workspacePaths", [])
        transcript_path = payload.get("transcriptPath")
        
        steps = []
        
        # 3. Custom logic: E.g., read transcript to inspect user prompt
        if transcript_path and os.path.isfile(transcript_path):
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    # Parse line as JSON representing trajectory steps
                    pass
        
        # 4. Inject prompt to stdout
        steps.append({"ephemeralMessage": "Hello from PreInvocation!"})
        print(json.dumps({"injectSteps": steps}))
        
    except Exception:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
```

---

## 3. PreToolUse & PostToolUse Hook Logic

### Payload Format (stdin)
Passed right before/after tool execution:
- **PreToolUse**: Contains the tool name and arguments. If the script exits with non-zero code or outputs error, the tool run will be aborted or modified.
- **PostToolUse**: Contains tool status and result. Often used to perform post-execution verification or linters.

---

## 4. Best Practices & Pitfalls

1. **SubAgent Session Detection**: SubAgents do not carry explicit flags in all environments. Check for:
   - `isSubagent`, `parentConversationId`, `role` (`subagent`, `worker`) keys in payload.
   - Cross-check `conversationId` in all `transcript.jsonl` files in the brain directory to see if the session was spawned by another conversation using `invoke_subagent`.
2. **User Prompt Extraction**: Fallback to scanning `transcriptPath` or `transcript.jsonl` in the same logs directory for `USER_INPUT` / `USER_EXPLICIT` type steps if payload does not have a direct `prompt` key.
3. **Robust Paths**: Use `os.path.abspath(os.path.expanduser(os.path.expandvars(path)))` to resolve variables or home folders (~).
4. **Encoding**: Always open files with explicit `encoding="utf-8"` (especially on Windows) to prevent default UTF-16 or code page errors.
