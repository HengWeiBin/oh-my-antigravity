# #3: Skill Resolver Extraction & Prompt Ingestion Seam

**Labels**: `ready-for-agent`  
**Blocked by**: [#1](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/issues/01-typed-data-contracts-and-core-hook-engine-foundation.md)  
**Spec**: [0001-unified-hook-engine.md](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/docs/specs/0001-unified-hook-engine.md)

## What it delivers
Creates a standalone `SkillResolver` module that encapsulates directory search precedence (workspace `.agents/skills`, plugin `skills/`, user config `skills/`), skill markdown file loading, and XML instruction block generation. Decouples path traversal from invocation handlers.

## Key Files
- `[NEW]` [scripts/hooks/skill_resolver.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/hooks/skill_resolver.py)
- `[NEW]` [scripts/tests/test_skill_resolver.py](file:///C:/Users/WBSC1/.gemini/config/plugins/oh-my-antigravity/scripts/tests/test_skill_resolver.py)

## Acceptance Criteria
- [ ] `SkillResolver` accepts configurable search roots with proper precedence ordering.
- [ ] `SkillResolver.resolve_skill(skill_name: str) -> SkillDefinition | None` locates `SKILL.md` without leaking file paths to callers.
- [ ] `SkillResolver.format_instruction_block(skill_name: str) -> str | None` produces sanitized XML blocks (`<skill-instruction>`).
- [ ] In-memory caching prevents redundant file I/O for repeated lookups within the same invocation.
- [ ] Unit tests verify fallback behavior across multiple directories using temporary fixture directories.
