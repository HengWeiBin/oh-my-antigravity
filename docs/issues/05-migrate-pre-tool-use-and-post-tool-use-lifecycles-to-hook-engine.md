# #5: Migrate PreToolUse & PostToolUse Lifecycles to HookEngine

**Labels**: `ready-for-agent`  
**Blocked by**: [#2](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/02-pure-permission-policy-and-session-resolver-extraction.md), [#4](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/04-migrate-pre-invocation-lifecycle-to-hook-engine.md)  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Converts all `PreToolUse` and `PostToolUse` hooks into `BaseHook` implementations. Integrates `PermissionPolicy` and `SessionResolver` into `PreToolUse` execution. Reduces `scripts/pre_tool_use.py` and `scripts/post_tool_use.py` to 5-line runners delegating to `HookEngine.run()`.

## Key Files
- `[MODIFY]` [scripts/pre_tool_use.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/pre_tool_use.py)
- `[MODIFY]` [scripts/post_tool_use.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/post_tool_use.py)
- `[MODIFY]` [scripts/hooks/notepad_write_guard.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/notepad_write_guard.py)
- `[MODIFY]` [scripts/hooks/comment_checker.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/comment_checker.py)
- `[MODIFY]` [scripts/hooks/plan_format_validator.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/plan_format_validator.py)
- `[MODIFY]` [scripts/hooks/empty_task_response_detector.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/empty_task_response_detector.py)
- `[MODIFY]` [scripts/hooks/fsync_skip_warning.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/fsync_skip_warning.py)

## Acceptance Criteria
- [ ] `PreToolUse` pipeline executes permission checks via `PermissionPolicy` and `notepad_write_guard` as typed `BaseHook`s.
- [ ] `PostToolUse` pipeline executes comment checking, plan validation, and response warnings as typed `BaseHook`s.
- [ ] `pre_tool_use.py` and `post_tool_use.py` contain only 5-line `HookEngine.run()` entrypoints.
- [ ] Unit tests verify tool interception, `allow`/`deny` decisions, and feedback message formatting without stream mocking.
