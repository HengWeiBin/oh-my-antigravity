## Summary

<!-- Provide a concise description of the changes introduced in this PR and why they are necessary. -->

## Related Issues

<!-- Link relevant issues: Fixes #X, Resolves #X, or Part of #X -->
Fixes #

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (new subagent, skill, hook capability, or tooling)
- [ ] ♻️ Refactoring / Code cleanup
- [ ] 📝 Documentation update
- [ ] 🧪 Tests / CI / Tooling improvement
- [ ] ⚠️ Breaking change (fix or feature that causes existing behavior to change)

## Quality Checklist

### Testing & Code Health
- [ ] Automated tests pass: `uv run pytest scripts/tests/` (zero test failures).
- [ ] Linter checks pass: `uv run ruff check scripts/` (zero warnings/errors).
- [ ] Code is formatted cleanly via `uv run ruff format --check scripts/`.
- [ ] Any newly added tests are deterministic, in-memory, and contract-driven.

### Architectural Invariants (For Hook & Script changes)
- [ ] All code in `scripts/hooks/` and hook entry points uses **standard library only** (0 runtime pip dependencies).
- [ ] New hooks derive from `BaseHook` and are wired into `HookEngine` / `HookPipeline`.
- [ ] `hooks.json` updated if new tool matchers or lifecycle events are added.

### Subagents & Skills (If applicable)
- [ ] Subagents in `agents/` include complete YAML frontmatter (`name`, `description`, `mainAgent`, `subagent`, `model`, `commandExecutionPolicy`, `tools`).
- [ ] Subagent `tools` array is an **explicit whitelist** (not left empty).
- [ ] Skills in `skills/<name>/` include a well-structured `SKILL.md` with trigger keywords in `description`.
- [ ] Skill scripts use `uv run` for Python, `bun` or `node` for JS/TS (no `axios`).

### Attribution & Standards
- [ ] Preserved upstream attribution to `oh-my-openagent` and `code-yeongyu` where required.
- [ ] Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, etc.).

## Verification Details

<!-- Paste terminal output showing passing test runs or linting verification. -->
```shell
uv run pytest scripts/tests/
uv run ruff check scripts/
```
