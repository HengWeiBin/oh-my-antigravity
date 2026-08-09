# #2: Pure Permission Policy & Session Resolver Extraction

**Labels**: `ready-for-agent`  
**Blocked by**: [#1](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/01-typed-data-contracts-and-core-hook-engine-foundation.md)  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Extracts permission rules from `scripts/pre_tool_use.py` and `scripts/hooks/utils.py` into a pure `PermissionPolicy` module with no filesystem dependencies, and separates transcript JSONL file scanning into a dedicated `SessionResolver` adapter. Converts permission testing into pure, fast unit tests.

## Key Files
- `[NEW]` [scripts/hooks/permission.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/permission.py)
- `[NEW]` [scripts/hooks/session.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/session.py)
- `[MODIFY]` [scripts/tests/test_permission.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_permission.py)
- `[NEW]` [scripts/tests/test_session_resolver.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_session_resolver.py)

## Acceptance Criteria
- [ ] `PermissionPolicy.evaluate(role: AgentRole, tool_name: str, target_path: str | None) -> PermissionDecision` evaluates tool authorization purely.
- [ ] Orchestrators (`sisyphus`, `atlas`, `prometheus`, `metis`, `momus`) are denied code edits and allowed markdown / `.agents/` / `.omo/` writes.
- [ ] Workers (`hephaestus`, `sisyphus-junior`) are denied plugin configs / `.omo/` writes and allowed code file edits.
- [ ] `SessionResolver.resolve_role(conversation_id: str, brain_dir: str) -> AgentRole` parses transcript JSONL logs to determine agent role.
- [ ] `test_permission.py` tests `PermissionPolicy.evaluate()` with pure role inputs and zero mocks.
- [ ] `test_session_resolver.py` tests transcript scanning using `tmp_path` fixtures without monkey-patching standard library functions.
