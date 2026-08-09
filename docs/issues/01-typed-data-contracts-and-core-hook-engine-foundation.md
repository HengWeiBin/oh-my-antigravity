# #1: Typed Data Contracts & Core HookEngine Foundation

**Labels**: `ready-for-agent`  
**Blocked by**: None  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Establishes the core data models (`LifecycleEvent`, `AgentRole`, `HookContext`, `HookResult`) and abstract `BaseHook` interface. Implements `HookEngine` and `HookPipeline` to manage hook lifecycle execution, JSON stream parsing, exception containment, and structured response serialization.

## Key Files
- `[NEW]` [scripts/hooks/models.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/models.py)
- `[NEW]` [scripts/hooks/engine.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/engine.py)
- `[NEW]` [scripts/tests/test_hook_engine.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_hook_engine.py)

## Acceptance Criteria
- [ ] `HookContext` dataclass encapsulates lifecycle event, conversation ID, tool metadata, user prompt, and parsed payload with immutable guarantees.
- [ ] `HookResult` dataclass encapsulates `injected_steps`, `decision`, `reason`, `additional_context`, and `metadata`.
- [ ] `BaseHook` abstract class defines `name` property and `execute(context: HookContext) -> HookResult`.
- [ ] `HookPipeline` handles registration and sequential execution of hooks with per-hook error containment (exceptions logged without stopping other hooks).
- [ ] `HookEngine.run(lifecycle, input_stream)` reads JSON from stream, initializes context, runs pipeline, and serializes aggregated output to stdout.
- [ ] Unit tests in `test_hook_engine.py` verify valid input, malformed JSON handling, exception isolation, and result aggregation with 100% pass rate.
