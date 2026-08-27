---
name: antigravity-hooks
description: Guide and best practices for creating, configuring, and testing Google Antigravity Hooks (PreInvocation, PostInvocation, PreToolUse, PostToolUse, Stop). Use this skill when asked to define, create, inspect, debug, or write hooks.json configurations and hook script files.
---

# Google Antigravity Hooks Guide

Google Antigravity Hooks provide a high-performance, event-driven interception mechanism across the agent lifecycle. They enable developers to observe, validate, mutate, gate, or inject behaviors into agent turns, tool invocations, and termination sequences.

This guide details official hook configurations, named hook groups, event contracts, input/output schemas, supported tools catalog, the Unified Hook Engine architecture (`HookEngine`, `HookPipeline`, `BaseHook`), pure permission and session resolution, skill resolution, modern entrypoint runner scripts, zero-mock testing strategies, and a troubleshooting matrix.

---

## 1. Configuration & Scope

Hooks are configured via `hooks.json` files and evaluated across three hierarchical scopes:

| Scope | Location | Description |
|---|---|---|
| **Global** | `~/.gemini/config/hooks.json` | Applies globally across all workspaces and agent sessions for the user. |
| **Workspace** | `<workspace>/.agents/hooks.json` | Scoped exclusively to the repository/workspace directory. |
| **Plugin** | `<plugin_root>/hooks.json` | Bundled within an Antigravity plugin to deliver modular agent capabilities. |

### Configuration Schemes

Antigravity supports two configuration structures in `hooks.json`:

#### A. Named Hook Groups (Workspace & Global Configuration)

Named hook groups organize hook handlers into logical, self-contained units (e.g., security gates, linters, observability monitors) that can be individually enabled, disabled, or shared:

```json
{
  "my-linter-hook": {
    "PostToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "command": "./scripts/lint.sh",
            "timeout": 10
          }
        ]
      }
    ]
  },
  "safety-gate": {
    "enabled": false,
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "command": "./scripts/safety-check.sh"
          }
        ]
      }
    ]
  }
}
```

#### B. Plugin Root Hooks Format

Plugins bundle hooks using the standard `"hooks"` root object containing lifecycle event arrays:

```json
{
  "hooks": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "python scripts/pre_invocation.py",
        "timeout": 8
      }
    ],
    "PreToolUse": [
      {
        "matcher": "^(write_to_file|replace_file_content|multi_replace_file_content|run_command)$",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/pre_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/post_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostInvocation": [
      {
        "type": "command",
        "command": "python scripts/post_invocation.py",
        "timeout": 10
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python scripts/stop.py",
        "timeout": 5
      }
    ]
  }
}
```

### Handler Properties & Defaults

Within any hook definition list:
- **`type`**: Execution handler type. Defaults to `"command"`. (May be omitted if using standard shell execution).
- **`command`**: Command line string executed as a child process. Hook inputs are passed via standard input (`stdin`), and hook responses are captured from standard output (`stdout`).
- **`timeout`**: Maximum execution time in seconds. Defaults to `30` seconds if not specified.
- **`enabled`**: Boolean flag indicating if the hook or group is active. Defaults to `true`.

### Matcher Rules (`PreToolUse` & `PostToolUse`)

For tool-related lifecycle events, the `matcher` property defines which tool calls trigger the hook using Regular Expressions:

- **Wildcard Matcher (`*` or `.*`)**: Intercepts every tool call.
- **Alternation / Exact Group (`^(run_command|write_to_file)$`)**: Matches designated tools precisely.
- **Prefix Matching (`browser_.*`)**: Matches all tools starting with a prefix (e.g., `browser_click`, `browser_navigate`).

---

## 2. Lifecycle Events & Input/Output Contracts

Every hook handler communicates with Antigravity via JSON over standard I/O:
- **Input (`stdin`)**: Clean JSON payload containing execution context and event details.
- **Output (`stdout`)**: Structured JSON contract returned by the handler. Diagnostic logs and debugging messages MUST be sent to standard error (`stderr`).

### Common Input Fields (Standard on all events)

All lifecycle events provide the following base context fields on `stdin`:

| Field | Type | Description |
|---|---|---|
| `conversationId` | `string` | Unique UUID identifying the active agent conversation session. |
| `workspacePaths` | `string[]` | Array of absolute paths to currently opened workspace folders. |
| `cwd` | `string` | Current working directory where the agent process is executing. |
| `transcriptPath` | `string` | Absolute path to the transcript JSONL log file: `<app_data_dir>/brain/<conversationId>/.system_generated/logs/transcript.jsonl`. |
| `artifactDirectoryPath` | `string` | Absolute path to the conversation artifacts directory: `<app_data_dir>/brain/<conversationId>`. |
| `modelName` | `string` | Identifier of the active language model (e.g. `gemini-3.6-flash-medium`, `gemini-2.5-pro`). |

---

### A. `PreInvocation`

- **Trigger**: Executed immediately prior to dispatching user input or conversation steps to the model.
- **Purpose**: System prompt augmentation, dynamic skill loading, rules injection, and context preservation.

#### `PreInvocation` Stdin Payload
```json
{
  "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "invocationNum": 0,
  "initialNumSteps": 1,
  "workspacePaths": ["C:/Users/user/project"],
  "cwd": "C:/Users/user/project",
  "transcriptPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript.jsonl",
  "artifactDirectoryPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "modelName": "gemini-3.6-flash-medium"
}
```

#### `PreInvocation` Stdout Response Contract
```json
{
  "injectSteps": [
    {
      "ephemeralMessage": "Ephemeral guideline: Adhere to strict linting rules and verify all code changes."
    },
    {
      "userMessage": "Synthetic prompt addition for the current turn."
    },
    {
      "toolCall": {
        "name": "view_file",
        "args": {
          "AbsolutePath": "C:/Users/user/project/package.json"
        }
      }
    }
  ]
}
```

- **`injectSteps` (array)**:
  - `ephemeralMessage` (`string`): Temporary context injected into the active prompt without persisting into the saved transcript.
  - `userMessage` (`string`): Synthesized user prompt appended to the session.
  - `toolCall` (`object`): Synthetic tool step pre-queued for execution.

---

### B. `PostInvocation`

- **Trigger**: Executed immediately after the model returns its response, before any emitted tool calls are executed.
- **Purpose**: Evaluates completion criteria, controls turn continuation, or halts runaway execution.

> [!NOTE]
> In the official Antigravity contract, `PostInvocation` receives the standard invocation context (`invocationNum`, `initialNumSteps`, common fields). It does not pass raw response body tokens or completion usage objects on `stdin`.

#### `PostInvocation` Stdin Payload
```json
{
  "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "invocationNum": 1,
  "initialNumSteps": 3,
  "workspacePaths": ["C:/Users/user/project"],
  "cwd": "C:/Users/user/project",
  "transcriptPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript.jsonl",
  "artifactDirectoryPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "modelName": "gemini-3.6-flash-medium"
}
```

#### `PostInvocation` Stdout Response Contract
```json
{
  "terminationBehavior": "force_continue",
  "injectSteps": [
    {
      "ephemeralMessage": "Task incomplete: You still have pending verification tests to execute."
    }
  ]
}
```

- **`terminationBehavior` (`string`)**:
  - `"force_continue"`: Re-engages the model for another invocation loop even if no tool calls were emitted.
  - `"terminate"`: Immediately halts execution for this turn.
  - `""` (empty or omitted): Normal lifecycle progression.
- **`injectSteps` (`array`)**: Additional steps to inject before the next invocation.

---

### C. `PreToolUse`

- **Trigger**: Executed immediately before running a tool call matching the configured `matcher`.
- **Purpose**: Security evaluation, parameter validation, role-based access control, and dynamic permission overrides.

#### `PreToolUse` Stdin Payload
```json
{
  "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "stepIdx": 2,
  "toolCall": {
    "name": "run_command",
    "args": {
      "CommandLine": "npm test",
      "Cwd": "C:/Users/user/project",
      "WaitMsBeforeAsync": 5000
    }
  },
  "workspacePaths": ["C:/Users/user/project"],
  "cwd": "C:/Users/user/project",
  "transcriptPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript.jsonl",
  "artifactDirectoryPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "modelName": "gemini-3.6-flash-medium"
}
```

#### `PreToolUse` Stdout Response Contract
```json
{
  "decision": "allow",
  "reason": "Test suite verified by security policy.",
  "permissionOverrides": [
    "command(npm test)",
    "read_file(C:/Users/user/project/*)"
  ]
}
```

- **`decision` (`string`)**:
  - `"allow"`: Tool execution proceeds immediately without prompting the user.
  - `"deny"`: Tool execution is blocked; the `reason` is returned to the model as the tool error.
  - `"ask"`: Prompts the user for interactive approval before running.
  - `"force_ask"`: Forces a confirmation prompt even if prior automated rules allowed it.
  - `"deny_unless_prior_grant"`: Denies execution unless an explicit permission grant was previously given.
- **`reason` (`string`, optional)**: Explanation displayed to the user or passed back to the model.
- **`permissionOverrides` (`string[]`)**: Array of permission strings granted for subsequent actions (e.g. `["command(npm test)", "read_file(/path/*)"]`).

---

### D. `PostToolUse`

- **Trigger**: Executed immediately after a tool call completes execution.
- **Purpose**: Output auditing, post-action linter verification, comment checking, and artifact validations.

#### `PostToolUse` Stdin Payload
```json
{
  "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "stepIdx": 2,
  "toolCall": {
    "name": "write_to_file",
    "args": {
      "TargetFile": "C:/Users/user/project/src/index.ts",
      "CodeContent": "console.log('hello');",
      "Overwrite": true
    }
  },
  "error": "",
  "workspacePaths": ["C:/Users/user/project"],
  "cwd": "C:/Users/user/project",
  "transcriptPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript.jsonl",
  "artifactDirectoryPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "modelName": "gemini-3.6-flash-medium"
}
```

- **`error` (`string`)**: Empty string `""` if the tool succeeded; contains the failure message if execution failed.
- **`stepIdx` (`int`)**: 0-based index of the tool step within the current turn.

#### `PostToolUse` Stdout Response Contract
```json
{}
```

> [!IMPORTANT]
> The official Antigravity standard response contract for `PostToolUse` is an empty JSON object `{}`.
> Internal plugin engines (including `oh-my-antigravity`) may return `{"additionalContext": "..."}` as an internal engine extension to provide feedback directly into the prompt context. Official tool runners expect `{}`.

---

### E. `Stop`

- **Trigger**: Executed when the agent session or execution loop is preparing to terminate.
- **Purpose**: Verifies task completion, enforces verification steps, cleans up background processes, and permits loop re-entry.

#### `Stop` Stdin Payload
```json
{
  "conversationId": "b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "executionNum": 4,
  "terminationReason": "model_stop",
  "error": "",
  "fullyIdle": true,
  "workspacePaths": ["C:/Users/user/project"],
  "cwd": "C:/Users/user/project",
  "transcriptPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa/.system_generated/logs/transcript.jsonl",
  "artifactDirectoryPath": "C:/Users/user/.gemini/antigravity/brain/b67d4ce2-1b29-4e25-8598-e6636a3171aa",
  "modelName": "gemini-3.6-flash-medium"
}
```

- **`executionNum` (`int`)**: Turn/execution counter.
- **`terminationReason` (`string`)**: Cause of termination (e.g. `"model_stop"`, `"max_steps"`, `"user_cancelled"`).
- **`error` (`string`)**: Error description if termination was caused by a fault; empty string otherwise.
- **`fullyIdle` (`boolean`)**: `true` if both the main agent and all background tasks/subagents have completed; `false` if background tasks remain active.

#### `Stop` Stdout Response Contract
```json
{
  "decision": "continue",
  "reason": "Tests have not yet been executed. You must run 'npm test' before ending this session."
}
```

> [!TIP]
> **Continuation & Loop Re-entry**: Returning `"decision": "continue"` cancels the shutdown sequence and forces the agent back into the execution loop. The `reason` string is injected into the context as an advisory prompt, ensuring the agent finishes pending verifications or corrective tasks.

---

## 3. Supported Antigravity Tools Catalog

Antigravity provides standard tools organized into five functional categories:

### 1. File & Directory Tools
- **[`view_file`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Reads file content (supports text and binary media).
  - *Args*: `AbsolutePath` (string, required), `StartLine` (int), `EndLine` (int), `ContentOffset` (int).
- **[`write_to_file`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Creates or overwrites files.
  - *Args*: `TargetFile` (string, required), `CodeContent` (string, required), `Overwrite` (bool, required), `Description` (string, required), `ArtifactMetadata` (object).
- **[`replace_file_content`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Replaces a single contiguous code block.
  - *Args*: `TargetFile` (string, required), `StartLine` (int, required), `EndLine` (int, required), `TargetContent` (string, required), `ReplacementContent` (string, required), `AllowMultiple` (bool, required), `Description` (string, required), `Instruction` (string, required).
- **[`multi_replace_file_content`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Replaces multiple non-contiguous blocks in a single file.
  - *Args*: `TargetFile` (string, required), `Replacements` (array of objects: `StartLine`, `EndLine`, `TargetContent`, `ReplacementContent`), `Description` (string, required).
- **[`list_dir`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Lists directory entries and metadata.
  - *Args*: `DirectoryPath` (string, required).
- **[`find_by_name`](file:///skills/antigravity-hooks/SKILL.md#1-file--directory-tools)**: Fast file/directory search via glob patterns.
  - *Args*: `SearchDirectory` (string, required), `Pattern` (string, required), `Type` (`"file" | "directory" | "any"`), `Extensions` (array), `Excludes` (array), `FullPath` (bool), `MaxDepth` (int).

### 2. Search Tools
- **[`grep_search`](file:///skills/antigravity-hooks/SKILL.md#2-search-tools)**: Pattern search across files using ripgrep.
  - *Args*: `SearchPath` (string, required), `Query` (string, required), `IsRegex` (bool), `CaseInsensitive` (bool), `MatchPerLine` (bool), `Includes` (array).
- **[`search_web`](file:///skills/antigravity-hooks/SKILL.md#2-search-tools)**: Web search returning summaries and citations.
  - *Args*: `query` (string, required), `domain` (string).
- **[`read_url_content`](file:///skills/antigravity-hooks/SKILL.md#2-search-tools)**: Fetches and converts static HTTP URLs to markdown.
  - *Args*: `Url` (string, required).

### 3. System & Execution Tools
- **[`run_command`](file:///skills/antigravity-hooks/SKILL.md#3-system--execution-tools)**: Runs a shell command on the host machine.
  - *Args*: `CommandLine` (string, required), `Cwd` (string, required), `WaitMsBeforeAsync` (int, required), `IsDaemon` (bool).
- **[`manage_task`](file:///skills/antigravity-hooks/SKILL.md#3-system--execution-tools)**: Interacts with background tasks.
  - *Args*: `Action` (`"list" | "kill" | "status" | "send_input"`, required), `TaskId` (string), `Input` (string).
- **[`schedule`](file:///skills/antigravity-hooks/SKILL.md#3-system--execution-tools)**: Schedules one-shot timers or recurring cron tasks.
  - *Args*: `Prompt` (string, required), `DurationSeconds` (int), `CronExpression` (string), `TimerCondition` (`"never" | "any" | <sender-id>`), `MaxIterations` (int), `IsDaemon` (bool).
- **[`list_permissions`](file:///skills/antigravity-hooks/SKILL.md#3-system--execution-tools)**: Lists active permissions granted for the current session.
  - *Args*: None or optional filter arguments.
- **[`ask_permission`](file:///skills/antigravity-hooks/SKILL.md#3-system--execution-tools)**: Programmatically requests approval for protected resources.
  - *Args*: `Permission` (string, required), `Reason` (string).

### 4. Collaboration & Subagent Tools
- **[`invoke_subagent`](file:///skills/antigravity-hooks/SKILL.md#4-collaboration--subagent-tools)**: Spawns a specialized subagent persona to execute a task.
  - *Args*: `Prompt` (string, required), `TypeName` (string), `Description` (string), `AutoContinue` (bool).
- **[`define_subagent`](file:///skills/antigravity-hooks/SKILL.md#4-collaboration--subagent-tools)**: Defines dynamic subagent personas with dedicated prompts and tools.
  - *Args*: `Name` (string, required), `SystemPrompt` (string, required), `Description` (string), `Tools` (array).
- **[`send_message`](file:///skills/antigravity-hooks/SKILL.md#4-collaboration--subagent-tools)**: Sends inter-agent messages between parent and subagents.
  - *Args*: `Recipient` (string, required), `Message` (string, required).
- **[`manage_subagents`](file:///skills/antigravity-hooks/SKILL.md#4-collaboration--subagent-tools)**: Lists, inspects, or terminates active subagents.
  - *Args*: `Action` (`"list" | "terminate" | "inspect"`, required), `SubagentId` (string).

### 5. Interaction & Asset Tools
- **[`ask_question`](file:///skills/antigravity-hooks/SKILL.md#5-interaction--asset-tools)**: Asks the user an interactive question with optional choices.
  - *Args*: `Question` (string, required), `Options` (array of strings).
- **[`generate_image`](file:///skills/antigravity-hooks/SKILL.md#5-interaction--asset-tools)**: Generates UI designs or visual assets from text prompts.
  - *Args*: `Prompt` (string, required), `ImageName` (string, required), `AspectRatio` (string), `ImagePaths` (array).

---

## 4. Unified Hook Engine Architecture

The **Unified Hook Engine** provides a modular pipeline architecture replacing fragmented standalone scripts. It handles stream configuration, strongly typed context parsing, sequential pipeline execution with error containment, and schema-compliant serialization.

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
            |                 HookPipeline                  |
            |  +---------------+     +---------------+      |
            |  | BaseHook 1    | --> | BaseHook 2    | ...  |
            |  +---------------+     +---------------+      |
            +-----------------------------------------------+
```

### 4.1 Core Abstractions & Data Contracts

Located in [`scripts/hooks/models.py`](file:///scripts/hooks/models.py) and [`scripts/hooks/engine.py`](file:///scripts/hooks/engine.py):

#### Data Contracts (`models.py`)
```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class LifecycleEvent(Enum):
    PRE_INVOCATION = "PreInvocation"
    POST_INVOCATION = "PostInvocation"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    STOP = "Stop"

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
    workspace_paths: list[str] = field(default_factory=list)
    transcript_path: str | None = None
    artifact_directory_path: str | None = None
    model_name: str | None = None
    step_idx: int | None = None
    invocation_num: int | None = None
    execution_num: int | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_error: str | None = None
    user_prompt: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

@dataclass
class HookResult:
    injected_steps: list[dict[str, Any]] = field(default_factory=list)
    decision: str | None = None  # "allow" | "deny" | "ask" | "force_ask" | "continue"
    reason: str | None = None
    permission_overrides: list[str] = field(default_factory=list)
    termination_behavior: str | None = None  # "force_continue" | "terminate" | ""
    additional_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### Base Hook & Pipeline (`engine.py`)
```python
from abc import ABC, abstractmethod
import sys
from scripts.hooks.models import HookContext, HookResult

class BaseHook(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique descriptive name for the hook."""
        ...

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult | None:
        """Executes logic against strongly typed context."""
        ...

class HookPipeline:
    def __init__(self, hooks: list[BaseHook] | None = None) -> None:
        self.hooks: list[BaseHook] = list(hooks) if hooks else []

    def register(self, hook: BaseHook) -> None:
        self.hooks.append(hook)

    def run(self, context: HookContext) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in self.hooks:
            try:
                res = hook.execute(context)
                if res is not None:
                    results.append(res)
            except Exception as e:
                # Error containment: isolate failure to stderr, prevent crashing agent
                sys.stderr.write(f"[HookEngine] Error in hook '{hook.name}': {e}\n")
        return results
```

---

### 4.2 Custom Hook Implementations

#### 1. Security Gate Hook (`PreToolUse`)
```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class DestructiveCommandGateHook(BaseHook):
    @property
    def name(self) -> str:
        return "destructive_command_gate"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name == "run_command":
            cmd = context.tool_input.get("CommandLine", "")
            if any(danger in cmd for danger in ["rm -rf /", "drop database", "mkfs"]):
                return HookResult(
                    decision="deny",
                    reason=f"Blocked dangerous command: '{cmd}'",
                )
            if "npm test" in cmd:
                return HookResult(
                    decision="allow",
                    permission_overrides=["command(npm test)"]
                )
        return HookResult(decision="allow")
```

#### 2. Continuation Enforcer Hook (`Stop`)
```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class StopVerificationGuardHook(BaseHook):
    @property
    def name(self) -> str:
        return "stop_verification_guard"

    def execute(self, context: HookContext) -> HookResult:
        # Prevent stopping if tests have not been executed
        if context.execution_num and context.execution_num < 3:
            return HookResult(
                decision="continue",
                reason="Verification required: Please run the test suite before ending the session."
            )
        return HookResult()
```

#### 3. Context Injector Hook (`PreInvocation`)
```python
from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult

class ProjectGuidelineInjectorHook(BaseHook):
    @property
    def name(self) -> str:
        return "project_guideline_injector"

    def execute(self, context: HookContext) -> HookResult:
        if context.invocation_num == 0:
            return HookResult(injected_steps=[
                {"ephemeralMessage": f"Active in: {context.cwd}. Adhere to strict type-safety."}
            ])
        return HookResult()
```

---

### 4.3 Pure Permission & Session Resolution

Access control is decoupled into an I/O discovery seam and a pure policy evaluation engine:

1. **[`SessionResolver`](file:///scripts/hooks/session.py)**:
   - Reads `.system_generated/logs/transcript.jsonl` under `<app_data_dir>/brain/<conversationId>`.
   - Resolves subagent `TypeName` from prior `invoke_subagent` calls.
   - Maps agent types to [`AgentRole.ORCHESTRATOR`](file:///scripts/hooks/models.py) (e.g. Sisyphus, Atlas, Prometheus) or [`AgentRole.WORKER`](file:///scripts/hooks/models.py) (e.g. Hephaestus, Explore, Librarian).

2. **[`PermissionPolicy`](file:///scripts/hooks/permission.py)**:
   - Contains zero filesystem access or log parsing.
   - Pure function: `evaluate(role: AgentRole, tool_name: str, target_path: str | None) -> PermissionDecision`.
   - **Orchestrator Rules**: Cannot directly edit source files (`.py`, `.ts`, `.js`); must delegate via `invoke_subagent` or limit edits to documentation and plans.
   - **Worker Rules**: Allowed to edit source files; barred from modifying `.agents/` configurations and plugin root definitions.

```python
from scripts.hooks.models import AgentRole
from scripts.hooks.permission import PermissionPolicy

# Deterministic pure evaluation
decision = PermissionPolicy.evaluate(
    role=AgentRole.ORCHESTRATOR,
    tool_name="write_to_file",
    target_path="src/index.ts"
)
# Result: decision.allowed == False, decision.decision == "ask"
```

---

### 4.4 Modular Skill Resolution

The [`SkillResolver`](file:///scripts/hooks/skill_resolver.py) resolves skill directories in strict precedence order:
1. Workspace Local: `<workspace>/skills/<name>/SKILL.md`, `<workspace>/.agents/skills/...`
2. Plugin Bundled: `<plugin_root>/skills/<name>/SKILL.md`
3. Sibling Plugins: `<plugins_dir>/*/skills/<name>/SKILL.md`
4. User Config: `~/.gemini/config/skills/<name>/SKILL.md`
5. Builtin Skills: `~/.gemini/antigravity/builtin/skills/<name>/SKILL.md`

Discovered skill documentation is wrapped into standard XML injection blocks:
```xml
<skill-instruction>
... SKILL.md contents ...
</skill-instruction>
```

---

### 4.5 Modern Entrypoint Runner Scripts

Each entrypoint script is a concise 5-line delegation wrapper around `HookEngine`:

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

#### `scripts/stop.py`
```python
import sys
from scripts.hooks.engine import HookEngine, LifecycleEvent

def main() -> int:
    return HookEngine.run(LifecycleEvent.STOP, sys.stdin)

if __name__ == "__main__":
    sys.exit(main())
```

---

## 5. Testing Best Practices & Zero-Mock Seams

The Unified Hook Engine allows direct, in-memory testing without patching standard library modules (`builtins.open`, `sys.stdin`, `sys.stdout`):

### 1. In-Memory `HookContext` Testing
```python
from scripts.hooks.models import HookContext, LifecycleEvent
from my_hooks import DestructiveCommandGateHook

def test_command_gate_denies_rm_rf():
    hook = DestructiveCommandGateHook()
    context = HookContext(
        lifecycle=LifecycleEvent.PRE_TOOL_USE,
        conversation_id="test-conv-uuid",
        cwd="/workspace",
        step_idx=0,
        tool_name="run_command",
        tool_input={"CommandLine": "rm -rf /"}
    )
    result = hook.execute(context)
    assert result.decision == "deny"
    assert "Blocked dangerous command" in result.reason
```

### 2. Pure Permission Testing
```python
from scripts.hooks.models import AgentRole
from scripts.hooks.permission import PermissionPolicy

def test_orchestrator_denied_source_code_edit():
    decision = PermissionPolicy.evaluate(
        role=AgentRole.ORCHESTRATOR,
        tool_name="write_to_file",
        target_path="src/app.py"
    )
    assert not decision.allowed
    assert decision.decision == "ask"
```

### 3. Pipeline Error Containment Testing
```python
from scripts.hooks.engine import BaseHook, HookPipeline
from scripts.hooks.models import HookContext, HookResult, LifecycleEvent

class FaultyHook(BaseHook):
    @property
    def name(self) -> str:
        return "faulty_hook"
    def execute(self, context: HookContext) -> HookResult:
        raise RuntimeError("Disk failure")

class GoodHook(BaseHook):
    @property
    def name(self) -> str:
        return "good_hook"
    def execute(self, context: HookContext) -> HookResult:
        return HookResult(decision="allow")

def test_pipeline_isolates_fault():
    pipeline = HookPipeline([FaultyHook(), GoodHook()])
    context = HookContext(lifecycle=LifecycleEvent.PRE_TOOL_USE, conversation_id="c1", cwd="/app")
    results = pipeline.run(context)
    assert len(results) == 1
    assert results[0].decision == "allow"
```

---

## 6. Production Best Practices & Troubleshooting Matrix

### Best Practices

1. **Standard Output Cleanliness**:
   - Only write valid JSON to `stdout`.
   - Direct all debugging, diagnostics, and stack traces to `sys.stderr`.
2. **Cross-Platform UTF-8 Streams**:
   - Ensure streams use UTF-8: `sys.stdin.reconfigure(encoding='utf-8')` and `sys.stdout.reconfigure(encoding='utf-8')`.
3. **Execution Timeouts**:
   - Keep hook execution fast (< 5s). Avoid blocking network requests or expensive operations.
4. **Subagent Awareness**:
   - Inspect `conversationId` and parent session transcripts to adapt behaviors between orchestrators and workers.
5. **Path Formatting**:
   - In `hooks.json`, use forward slashes (`/`) or relative paths (`python scripts/pre_invocation.py`) to avoid Windows backslash escape errors.

### Troubleshooting Matrix

| Symptom | Probable Cause | Corrective Action |
|---|---|---|
| Hook does not execute | Incorrect matcher regex, file path error, or `"enabled": false` | Verify regex with test strings, ensure script exists at relative path, and check `enabled: true`. |
| Agent runtime JSON error | Non-JSON text printed to `stdout` by hook script | Redirect all `print(...)` and diagnostic logging statements to `sys.stderr`. |
| Hook execution timeout | Script blocked on stdin reading or hanging subprocess | Read full stdin synchronously (`sys.stdin.read()`), ensure subprocess timeouts, and keep operations lightweight. |
| Permission overrides ignored | `permissionOverrides` passed as `{}` instead of `string[]` | Return a string array format, e.g. `["command(npm test)", "read_file(/path/*)"]`. |
| PostInvocation loop not forcing continue | Returned `"decision": "force_continue"` instead of `terminationBehavior` | Update return payload to use `"terminationBehavior": "force_continue"`. |
| Stop loop repeating infinitely | Stop hook unconditionally returning `"decision": "continue"` | Track turn/execution counter (`executionNum`) and allow shutdown when verifications complete or after max retries. |
| Role resolution returns ORCHESTRATOR | Transcript missing from brain logs directory | Ensure path `<app_data_dir>/brain/<conversationId>/.system_generated/logs/transcript.jsonl` exists; fallback to default is expected behavior. |
| Skill instructions not loading | `SKILL.md` missing or outside resolution directories | Check directory precedence order (workspace -> plugin -> user config -> builtin). |
