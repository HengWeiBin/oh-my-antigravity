# Oh-My-Antigravity — Agent Instructions

## What This Is

Google Antigravity plugin. Contains 11 agent profiles, 42 skills, and a hook-based lifecycle interceptor system (Python). All files are configuration/prompts/scripts — not a traditional application.

## Python Toolchain

- **Python 3.13** (`.python-version`). Use `uv run` for everything.
- **Test:** `uv run pytest scripts/tests/`
- **Lint:** `uv run ruff check scripts/`
- Dependencies live in `pyproject.toml`. Lockfile: `uv.lock`.

## Directory Layout

| Path | What |
|------|------|
| `agents/` | 11 agent profile `.md` files with YAML frontmatter. Orchestrators: sisyphus, atlas, prometheus, metis, momus. Workers: hephaestus, sisyphus-junior, explore, librarian, oracle, multimodal-looker. |
| `skills/` | 42 skill directories. Each has a `SKILL.md`. |
| `rules/` | `oh-my-openagent-rules.md` — injected into every session. |
| `scripts/` | Hook interceptors (Python). Entry points: `pre_invocation.py`, `pre_tool_use.py`, `post_tool_use.py`. Shared logic in `scripts/hooks/`. |
| `hooks.json` | Hook router config — which tools trigger `PreInvocation`, `PreToolUse`, `PostToolUse`. |
| `plugin.json` | Plugin metadata. |

## Hook System

Three hook phases, all Python scripts reading JSON from stdin and writing JSON to stdout:

- **PreInvocation** (`pre_invocation.py`) — Runs on every user turn. Injects: directory agents, rules, todo preservation/continuation, agent reminders, keyword detection, skill auto-loading for subagents, codegraph recommendation.
- **PreToolUse** (`pre_tool_use.py`) — Intercepts `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command`. Enforces role-based permissions: orchestrators can NOT write code (only `.md`, `.agents/`, `.omo/`), workers can NOT write plugin config or `.omo/` state.
- **PostToolUse** (`post_tool_use.py`) — Intercepts `invoke_subagent` and file writes. Injects 4-phase verification reminder, empty response detection, comment checker, plan format validator.

Hook paths in `hooks.json` use absolute paths (`C:/Users/...`). Do not hardcode user paths in new code.

## Agent Roles

- **Orchestrators** (no code edits): sisyphus, atlas, prometheus, metis, momus
- **Workers** (implement code): hephaestus, sisyphus-junior
- **Research**: explore, librarian, oracle, multimodal-looker

## Key Conventions

- Orchestrators must NOT edit source code. Use `invoke_subagent`.
- Workers must NOT edit `.agents/`, `rules/`, `hooks.json`, `plugin.json`, or `.omo/` plan/task state.
- After delegating to a subagent, verify all changes with tool calls — read files, run tests, run lsp. Do not trust subagent self-assessment.
- Skills use `uv run` for Python scripts. TypeScript/JS skills use `bun` or Node.
- `axios` is banned in TS/JS modules. Use `ky` or `undici`.

## Skill Auto-Loading

`pre_invocation.py` scans subagent prompts for slash-command syntax (e.g., `/debugging`) and auto-loads the corresponding `SKILL.md` from workspace, plugin, user config, or builtin skill directories. Skills are discovered under `skills/<name>/SKILL.md`.

## Agent skills

### Issue tracker

GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context (`CONTEXT.md` + `docs/adr/`). See `docs/agents/domain.md`.

