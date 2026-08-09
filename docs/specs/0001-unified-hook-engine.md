# Spec: Unified Hook Engine & Lifecycle Consolidation

## Problem Statement

As a plugin developer and maintainer for `oh-my-antigravity`, modifying or adding lifecycle hooks requires dealing with significant friction:
1. Entrypoint scripts (`pre_invocation.py`, `pre_tool_use.py`, `post_tool_use.py`) duplicate low-level stream handling, JSON decoding, error recovery, and stdout serialization.
2. Individual hook scripts receive raw, untyped `dict` payloads and return heterogeneous, unstructured data structures, requiring bespoke extraction code in every runner.
3. Unit testing hooks currently requires extensive global monkey-patching of OS and filesystem primitives (`os.listdir`, `os.path.isdir`, `os.path.isfile`, `builtins.open`), coupling test suites directly to implementation internals rather than clean behavioural seams.
4. Role resolution and permission policies are tightly coupled with transcript JSONL log traversal, creating testing fragility and leaking filesystem details across execution phases.

## Solution

Consolidate lifecycle parsing, hook dispatching, error containment, and result serialization behind a deep `HookEngine` module.
- Provide a single entrypoint seam (`HookEngine.run(lifecycle, stream)`) that reduces entrypoint runner scripts to 5-line delegations.
- Introduce strongly-typed data structures (`HookContext`, `HookResult`) and an abstract `BaseHook` interface so individual hooks only implement pure domain logic.
- Decouple session transcript discovery (`SessionResolver`) from tool permission evaluation (`PermissionPolicy`), making permission rules pure and testable without filesystem mocks.
- Provide a centralized `SkillResolver` to encapsulate search path probing and prompt block generation.

---

## User Stories

1. As a plugin developer, I want all hook entrypoint scripts to delegate to a single engine, so that lifecycle stream parsing and error handling logic are not duplicated across multiple files.
2. As a hook author, I want a strongly-typed `HookContext` object containing the parsed payload, session metadata, workspace paths, and tool details, so that I don't have to manually navigate nested dictionary keys or handle `KeyError` exceptions.
3. As a hook author, I want to return a structured `HookResult` (specifying injected steps, decision, reasoning, and context), so that result serialization is handled automatically and consistently.
4. As a plugin maintainer, I want unhandled exceptions in any single hook to be caught and logged safely without crashing the parent agent invocation or swallowing critical diagnostic details.
5. As a test author, I want to unit-test individual hooks by instantiating a `HookContext` dataclass in-memory, so that I don't have to mock `sys.stdin`, `sys.stdout`, or JSON string streams.
6. As a test author, I want to verify permission policy rules by passing pure role enums and file paths to `PermissionPolicy.evaluate()`, so that tests run without monkey-patching `os.listdir` or `open()`.
7. As an agent orchestrator, I want tool-use permissions (e.g., blocking orchestrators from editing code and workers from modifying plugin configs) to be evaluated consistently and transparently.
8. As a subagent executor, I want skill instructions requested via slash commands (e.g. `/debugging`) to be resolved reliably through a `SkillResolver` that prioritizes workspace-local skills over global plugin skills.
9. As a developer adding a new hook, I want to register a hook with the `HookPipeline` in one place without writing bespoke unpacking logic in runner scripts.
10. As a maintainer inspecting logs, I want standardized error telemetry when a hook encounters corrupt input or missing transcripts.

---

## Implementation Decisions

### 1. Unified Hook Engine (`scripts/hooks/engine.py`)
- **Seam & Interface**:
  - `HookEngine.run(lifecycle: LifecycleEvent, input_stream: TextIO) -> int`: The top-level interface called by entrypoint runners. Reads JSON, initializes context, runs the pipeline, writes serialized output, and returns an exit code.
  - `HookPipeline`: Manages registration and sequential execution of hooks for a given lifecycle phase (`PreInvocation`, `PreToolUse`, `PostToolUse`).
  - `BaseHook` abstract base class requiring:
    - `name: str`
    - `execute(context: HookContext) -> HookResult`

### 2. Typed Data Contracts (`scripts/hooks/models.py`)
- **Data Shapes**:
  ```python
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

### 3. Session & Permission Architecture (`scripts/hooks/session.py`, `scripts/hooks/permission.py`)
- `SessionResolver`: Responsible for discovering agent role from transcript logs in `brain_dir`.
- `PermissionPolicy`: Pure evaluation module. Given `(role: AgentRole, tool_name: str, target_path: str | None)`, returns `PermissionDecision(allowed: bool, reason: str | None)`.

### 4. Modular Skill Resolver (`scripts/hooks/skill_resolver.py`)
- `SkillResolver`: Configured with search roots (workspace `.agents/skills`, plugin `skills/`, user config `skills/`).
- Exposes `resolve_skill(name: str) -> SkillDefinition | None` and `format_instruction_block(name: str) -> str | None`.

### 5. Runner Simplification
- `scripts/pre_invocation.py`, `scripts/pre_tool_use.py`, and `scripts/post_tool_use.py` are reduced to:
  ```python
  import sys
  from scripts.hooks.engine import HookEngine, LifecycleEvent

  if __name__ == "__main__":
      sys.exit(HookEngine.run(LifecycleEvent.PRE_INVOCATION, sys.stdin))
  ```

---

## Testing Decisions

### Test Principles
- Tests must verify external behavior through defined interfaces rather than private implementation details.
- Avoid monkey-patching Python standard library file system modules (`builtins.open`, `os.listdir`, `os.path.*`).
- Use in-memory dataclass fixtures for unit tests and `tmp_path` fixtures for filesystem adapter tests.

### Test Coverage Areas
1. **Engine & Pipeline Suite (`test_hook_engine.py`)**:
   - Verify `HookEngine.run()` correctly handles valid JSON, malformed JSON, and empty input.
   - Verify error isolation: an exception raised by one hook does not prevent subsequent hooks in the pipeline from running.
   - Verify result aggregation: multiple hooks returning `injected_steps` and `additional_context` are merged deterministically.
2. **Permission Policy Suite (`test_permission_policy.py`)**:
   - Pure tests for orchestrator restrictions (denying code file edits, allowing Markdown and `.agents/` edits).
   - Pure tests for worker restrictions (denying plugin config edits, allowing code file edits).
   - Tests run instantaneously with zero mocks.
3. **Session Resolver Suite (`test_session_resolver.py`)**:
   - Uses `tmp_path` with real temporary JSONL log files to verify transcript scanning and role detection.
4. **Skill Resolver Suite (`test_skill_resolver.py`)**:
   - Uses `tmp_path` directory hierarchies to verify lookup precedence and fallback behaviors.
5. **Integration Sanity Suite (`test_runners_integration.py`)**:
   - Verifies end-to-end execution of `pre_invocation.py`, `pre_tool_use.py`, and `post_tool_use.py` as subprocesses with sample JSON payloads.

---

## Out of Scope

- Migrating hooks to another programming language (remains Python 3.13 with `uv`).
- Modifying the underlying Antigravity hook schema defined by Google Antigravity.
- Redesigning agent profile markdown instructions in `agents/*.md`.
- Modifying external skill scripts outside the `scripts/hooks` lifecycle.

---

## Further Notes

- Maintains full backwards compatibility with `hooks.json` registrations.
- Fully aligns with `/codebase-design` depth, leverage, and locality principles.
