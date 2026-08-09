# #4: Migrate PreInvocation Lifecycle to HookEngine

**Labels**: `ready-for-agent`  
**Blocked by**: [#1](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/01-typed-data-contracts-and-core-hook-engine-foundation.md), [#3](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/03-skill-resolver-extraction-and-prompt-ingestion-seam.md)  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Converts all `PreInvocation` hooks into `BaseHook` implementations registered in `HookPipeline`. Updates `pre_invocation.py` to a 5-line runner delegating to `HookEngine.run(LifecycleEvent.PRE_INVOCATION, sys.stdin)`.

## Key Files
- `[MODIFY]` [scripts/pre_invocation.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/pre_invocation.py)
- `[MODIFY]` [scripts/hooks/rules_injector.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/rules_injector.py)
- `[MODIFY]` [scripts/hooks/directory_agents_injector.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/directory_agents_injector.py)
- `[MODIFY]` [scripts/hooks/compaction_todo_preserver.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/compaction_todo_preserver.py)
- `[MODIFY]` [scripts/hooks/todo_continuation_enforcer.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/todo_continuation_enforcer.py)
- `[MODIFY]` [scripts/hooks/agent_usage_reminder.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/agent_usage_reminder.py)
- `[MODIFY]` [scripts/hooks/keyword_detector.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/keyword_detector.py)
- `[MODIFY]` [scripts/hooks/init_project_dir_replacer.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/init_project_dir_replacer.py)
- `[MODIFY]` [scripts/tests/test_pre_invocation.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_pre_invocation.py)

## Acceptance Criteria
- [ ] All PreInvocation hooks implement the `BaseHook.execute(context: HookContext) -> HookResult` interface.
- [ ] Skill auto-loading utilizes `SkillResolver` to inject instructions for subagents when slash-commands are detected in prompts.
- [ ] `scripts/pre_invocation.py` contains only the top-level `HookEngine.run()` entrypoint delegation.
- [ ] `test_pre_invocation.py` tests individual hooks directly via `HookContext` without monkey-patching `builtins.open` or `os.path`.
