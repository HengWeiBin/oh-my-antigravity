---
name: antigravity-hooks
description: Guide and best practices for creating, configuring, and testing Google Antigravity Hooks (PreInvocation, PostInvocation, PreToolUse, PostToolUse, Stop). Use this skill when asked to define, create, inspect, debug, or write hooks.json configurations and hook script files.
---

# Google Antigravity Hooks Guide

Google Antigravity Hooks provide a powerful event-driven mechanism to intercept, evaluate, modify, gate, or inject behaviors into agent lifecycles. This guide details hook configuration, event payloads, response contracts, matcher rules, the Unified Hook Engine architecture (`HookEngine`, `HookPipeline`, `BaseHook`), pure permission & session resolution patterns, skill resolution, modern entrypoint runner scripts, zero-mock testing strategies, and troubleshooting matrix.

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
  {
    "additionalContext": "Verification check passed cleanly."
  }
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

## 3. Unified Hook Engine & Architecture

The **Unified Hook Engine** replaces fragmented, repetitive script runners with a modular, pipeline-driven framework. Instead of each script parsing raw stdin streams and formatting JSON output, entrypoints delegate to `HookEngine`, which manages payload parsing, strongly-typed context construction, pipeline execution with error containment, and output serialization.

```
                  +-----------------------------------+
                  |         Antigravity Loop          |
                  +-----------------------------------+
                                    | (JSON via stdin)
                                    v
                  +-----------------------------------+
                  |  Entrypoint (e.g. pre_tool_use.py)|
                  +-----------------------------------+
                                    | 5-line delegation
                                    v
                  +-----------------------------------+
                  |           HookEngine              |
                  +-----------------------------------+
                    |               |               |
         parse_payload()     build_context()   serialize_output()
                    |               |               ^
                    v               v               |
            +-----------------------------------------------+
            |            HookPipeline                       |
            |  +---------------+     +---------------+      |
            |  | BaseHook 1    | --> | BaseHook 2    | ...  |
            |  +---------------+     +---------------+      |
            +-----------------------------------------------+
```

### 3.1 HookEngine, HookPipeline & BaseHook Abstraction

- **`BaseHook`**: The abstract base class that every hook implements. It defines a `name` property and an `execute(context: HookContext) -> HookResult` method.
- **`HookPipeline`**: A container for an ordered list of `BaseHook` instances. When `pipeline.run(context)` is called, hooks execute sequentially. If an exception occurs within a hook, it is caught and logged to `sys.stderr` without breaking remaining hooks (error containment).
- **`HookEngine`**: The main orchestrator class. It parses raw JSON from `sys.stdin`, builds a `HookContext`, executes the registered pipeline for the lifecycle event, and prints serialized JSON results to `sys.stdout`.

#### Strongly-Typed Data Contracts (`scripts/hooks/models.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class LifecycleEvent(Enum):
    PRE_INVOCATION = "PreInvocation"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"

class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    RESEARCH = "research"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class HookContext:
    lifecycle: LifecycleEvent
    conversation_id: str
    cwd: str
    tool_name: str | None = None
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_output: str | None = None
    user_prompt: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

@dataclass
class HookResult:
    injected_steps: list[dict[str, Any]] = field(default_factory=list)
    decision: str | None = None  # "allow" | "deny" | "ask"
    reason: str | None = None
    additional_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### Implementing a Custom Lifecycle Hook

To add a custom hook, inherit from `BaseHook` and implement `execute`:

```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class CustomSecurityGateHook(BaseHook):
    @property
    def name(self) -> str:
        return "custom_security_gate"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name == "run_command":
            cmd = context.tool_input.get("CommandLine", "")
            if "sudo" in cmd or "chmod 777" in cmd:
                return HookResult(
                    decision="deny",
                    reason=f"Security policy block: Disallowed command pattern in '{cmd}'."
                )
        return HookResult(decision="allow")
```

---

### 3.2 Pure Permission & Session Resolution Pattern

Role-based access control and file protection are decoupled into two distinct layers:

1. **`SessionResolver` (I/O & Log Traversal Layer)**:
   - Discovers agent roles by inspecting session transcript logs (`transcript.jsonl` / `transcript_full.jsonl`) under the brain directory (`.system_generated/logs`).
   - Identifies subagent `TypeName` from `invoke_subagent` calls.
   - Maps agent types into `AgentRole.ORCHESTRATOR` (e.g. Sisyphus, Atlas, Prometheus, Metis, Momus) or `AgentRole.WORKER` (e.g. Hephaestus, Sisyphus-Junior, Explore, Librarian).

2. **`PermissionPolicy` (Pure Evaluation Seam)**:
   - Contains zero filesystem side-effects or log reading logic.
   - Accepts pure parameters: `evaluate(role: AgentRole, tool_name: str, target_path: str | None) -> PermissionDecision`.
   - Enforces role constraints:
     - **Orchestrator Rules**: Block direct editing of product source code (`.py`, `.ts`, `.js`, etc.). Require editing through `invoke_subagent` or allow only non-code files (`.md`, `plans/`, `.omo/`, `.agents/`).
     - **Worker Rules**: Block workers from modifying `.agents/` configurations, plugin files (`hooks.json`, `plugin.json`, `rules/`), and `.omo/plans/` or draft state files, while permitting source code edits and `.omo/notepads/`.

```python
from scripts.hooks.models import AgentRole
from scripts.hooks.permission import PermissionPolicy, PermissionDecision

# Pure evaluation without standard library file system mocks
decision: PermissionDecision = PermissionPolicy.evaluate(
    role=AgentRole.ORCHESTRATOR,
    tool_name="write_to_file",
    target_path="src/main.py"
)

# Output: decision.allowed == False, decision.decision == "ask", decision.reason contains explanation
```

---

### 3.3 Modular Skill Resolver

The `SkillResolver` (`scripts/hooks/skill_resolver.py`) centralizes skill instruction discovery and prompt block formatting.

#### Directory Precedence

When resolving a skill (e.g. `/debugging` or `debugging`), `SkillResolver` searches across the following path hierarchy in order of priority:

1. **Workspace Local Skills**:
   - `<workspace>/skills/<name>/SKILL.md`
   - `<workspace>/.agents/skills/<name>/SKILL.md`
   - `<workspace>/.gemini/skills/<name>/SKILL.md`
2. **Plugin Bundled Skills**:
   - `<plugin_root>/skills/<name>/SKILL.md`
3. **Sibling Plugin Directories**:
   - `<plugins_dir>/*/skills/<name>/SKILL.md`
4. **User Config Skills**:
   - `~/.gemini/config/skills/<name>/SKILL.md`
5. **Builtin Skills**:
   - `~/.gemini/antigravity/builtin/skills/<name>/SKILL.md`

#### Instruction Formatting

`SkillResolver.format_instruction_block(skill_name, workspace_paths, cwd)` retrieves the matching `SKILL.md` content and wraps it in a standard XML block for LLM prompt injection:

```xml
<skill-instruction>
... contents of SKILL.md ...
</skill-instruction>
```

---

### 3.4 Modern Entrypoint Runner Scripts & Delegation

With the Unified Hook Engine, all top-level entrypoint runner scripts (`pre_invocation.py`, `pre_tool_use.py`, `post_tool_use.py`) are reduced to clean 5-line delegation wrappers:

#### `scripts/pre_invocation.py`
```python
import sys
from scripts.hooks.engine import HookEngine, LifecycleEvent

def main() -> int:
    return HookEngine.run(LifecycleEvent.PRE_INVOCATION, sys.stdin)

if __name__ == "__main__":
    sys.exit(main())
```

#### `scripts/pre_tool_use.py`
```python
import sys
from scripts.hooks.engine import HookEngine, LifecycleEvent

def main() -> int:
    return HookEngine.run(LifecycleEvent.PRE_TOOL_USE, sys.stdin)

if __name__ == "__main__":
    sys.exit(main())
```

#### `scripts/post_tool_use.py`
```python
import sys
from scripts.hooks.engine import HookEngine, LifecycleEvent

def main() -> int:
    return HookEngine.run(LifecycleEvent.POST_TOOL_USE, sys.stdin)

if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. Custom Hook Implementations & Script Patterns

The recommended approach for creating new hooks is extending `BaseHook` and registering it with `HookEngine`. Below are examples for common lifecycle hooks:

### 1. PreInvocation Hook (Context & Skill Injector)

```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class WorkspaceRulesInjectorHook(BaseHook):
    @property
    def name(self) -> str:
        return "workspace_rules_injector"

    def execute(self, context: HookContext) -> HookResult:
        payload = context.raw_payload
        invocation_num = payload.get("invocationNum", 0)
        
        # Inject rules on session startup
        if invocation_num == 0:
            return HookResult(injected_steps=[
                {"ephemeralMessage": f"Session active in: {context.cwd}. Enforcing strict type safety and modular design rules."}
            ])
        return HookResult()
```

### 2. PreToolUse Hook (Command & File Guard)

```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class CommandSanitizerHook(BaseHook):
    @property
    def name(self) -> str:
        return "command_sanitizer"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name == "run_command":
            cmd = context.tool_input.get("CommandLine", "")
            if "rm -rf /" in cmd or "mkfs" in cmd:
                return HookResult(
                    decision="deny",
                    reason="Execution denied: Dangerous command detected."
                )
        return HookResult(decision="allow")
```

### 3. PostToolUse Hook (Post-Execution Verification)

```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class CodeEditVerifierHook(BaseHook):
    @property
    def name(self) -> str:
        return "code_edit_verifier"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
            return HookResult(
                additional_context="Reminder: Run project linter or test suite to verify code edits."
            )
        return HookResult()
```

---

## 5. Testing Best Practices & Zero-Mock Seams

A primary goal of the Unified Hook Engine architecture is enabling **zero-mock testing**. Unit tests no longer need to monkey-patch `sys.stdin`, `sys.stdout`, `builtins.open`, or `os.listdir`.

### 1. Direct Unit Testing with In-Memory `HookContext`

Test individual hook classes by instantiating `HookContext` dataclasses directly in Python:

```python
from scripts.hooks.models import HookContext, LifecycleEvent
from my_hooks import CustomSecurityGateHook

def test_custom_security_gate_denies_sudo():
    hook = CustomSecurityGateHook()
    context = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="test-conv-123",
        cwd="/workspace",
        tool_name="run_command",
        tool_input={"CommandLine": "sudo rm -rf /var/log"}
    )
    
    result = hook.execute(context)
    
    assert result.decision == "deny"
    assert "Security policy block" in result.reason
```

### 2. Testing `PermissionPolicy` Pure Seam

`PermissionPolicy.evaluate()` can be tested deterministically across roles and target file paths without any filesystem access:

```python
from scripts.hooks.models import AgentRole
from scripts.hooks.permission import PermissionPolicy

def test_orchestrator_cannot_edit_source_code():
    decision = PermissionPolicy.evaluate(
        role=AgentRole.ORCHESTRATOR,
        tool_name="write_to_file",
        target_path="src/index.js"
    )
    assert not decision.allowed
    assert decision.decision == "ask"

def test_worker_can_edit_source_code():
    decision = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path="src/index.js"
    )
    assert decision.allowed
    assert decision.decision == "allow"
```

### 3. Pipeline Error Containment Testing

Verify that exceptions in one hook do not halt execution of remaining pipeline hooks:

```python
from scripts.hooks.engine import BaseHook, HookPipeline
from scripts.hooks.models import HookContext, HookResult, LifecycleEvent

class FaultyHook(BaseHook):
    @property
    def name(self) -> str:
        return "faulty_hook"
        
    def execute(self, context: HookContext) -> HookResult:
        raise RuntimeError("Unexpected failure")

class NormalHook(BaseHook):
    @property
    def name(self) -> str:
        return "normal_hook"
        
    def execute(self, context: HookContext) -> HookResult:
        return HookResult(injected_steps=[{"ephemeralMessage": "ok"}])

def test_pipeline_error_containment():
    pipeline = HookPipeline([FaultyHook(), NormalHook()])
    context = HookContext(lifecycle=LifecycleEvent.PRE_INVOCATION, conversation_id="c1", cwd="/app")
    
    results = pipeline.run(context)
    
    # FaultyHook error was logged to stderr and contained; NormalHook executed cleanly
    assert len(results) == 1
    assert results[0].injected_steps == [{"ephemeralMessage": "ok"}]
```

---

## 6. Best Practices & Troubleshooting

### 1. Standard Output (`stdout`) Cleanliness
- **Only output valid JSON on `stdout`.** Any non-JSON text printed to `stdout` will cause JSON parsing errors in the agent runtime.
- Direct all diagnostic prints, warnings, and log messages to `sys.stderr`.

### 2. Cross-Platform UTF-8 Streams
- Windows terminals and default Python stream wrappers may use system code pages (e.g. CP1252/CP950).
- Always use `sys.stdin.reconfigure(encoding='utf-8')` and `sys.stdout.reconfigure(encoding='utf-8')`, or use the engine's built-in `setup_utf8_streams()`.

### 3. Execution Timeouts
- Hooks must complete quickly to prevent agent loop latency.
- Set conservative `timeout` values in `hooks.json` (e.g. 3-8 seconds) and ensure hook scripts do not block on remote I/O indefinitely.

### 4. Path Normalization
- Use `pathlib.Path` or `os.path.normpath` for cross-platform path handling.
- Use forward slashes (`/`) or escaped backslashes (`\\\\`) in Windows paths within `hooks.json`.

### 5. Subagent Awareness
- Check `is_subagent_session(payload)` or evaluate `context.raw_payload` to distinguish top-level orchestrator sessions from subagent worker invocations.

### 6. Troubleshooting Matrix

| Issue | Cause | Action |
|---|---|---|
| Hook not firing | Path wrong, matcher misconfigured, or `"enabled": false` | Verify path accuracy, matcher regex test, and ensure `"enabled": true`. |
| Agent runtime JSON error | Non-JSON printed to `stdout` by hook script | Ensure all print/debug statements log to `sys.stderr` only. |
| Timeout abort | Script waiting on input or blocked on network/disk | Use fast non-blocking reads (`sys.stdin.read()`) and avoid slow network operations. |
| Role resolution error | Corrupt log files or missing `.system_generated/logs` | Check brain directory transcript existence; `SessionResolver` defaults safely to `AgentRole.ORCHESTRATOR`. |
| Skill instruction not loading | File path outside search roots or missing `SKILL.md` | Verify file path placement matches `SkillResolver` directory precedence order. |
