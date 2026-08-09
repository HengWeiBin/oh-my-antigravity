# #6: End-to-End Integration Verification & Deprecation Cleanup

**Labels**: `ready-for-agent`  
**Blocked by**: [#5](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/05-migrate-pre-tool-use-and-post-tool-use-lifecycles-to-hook-engine.md)  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Updates and runs full subprocess integration tests against `scripts/pre_invocation.py`, `scripts/pre_tool_use.py`, and `scripts/post_tool_use.py`. Removes deprecated untyped dictionary utility helpers in `scripts/hooks/utils.py` and verifies full test pass rate and ruff compliance across the repo.

## Key Files
- `[MODIFY]` [scripts/tests/test_integration.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_integration.py)
- `[MODIFY]` [scripts/hooks/utils.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/utils.py)
- `[MODIFY]` [scripts/tests/test_hooks_config.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_hooks_config.py)

## Acceptance Criteria
- [ ] `test_integration.py` executes subprocess runs of `pre_invocation.py`, `pre_tool_use.py`, and `post_tool_use.py` with valid and invalid payloads.
- [ ] Deprecated helper functions in `scripts/hooks/utils.py` that were replaced by `SessionResolver`, `SkillResolver`, or `HookEngine` are cleaned up.
- [ ] `uv run pytest scripts/tests/` passes 100% with zero regressions.
- [ ] `uv run ruff check scripts/` passes with zero lint violations.
