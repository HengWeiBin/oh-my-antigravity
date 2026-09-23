# Contributing to oh-my-antigravity

Thank you for your interest in contributing to **oh-my-antigravity**! We welcome contributions from the community—whether bug fixes, new subagent profiles, specialized skills, or hook performance improvements.

This document outlines our development setup, testing standards, architectural guidelines, and submission workflow to ensure a smooth contribution process.

---

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Quality Gates: Testing & Linting](#quality-gates-testing--linting)
- [Architectural Rules for Lifecycle Hooks](#architectural-rules-for-lifecycle-hooks)
- [Contributing a New Subagent](#contributing-a-new-subagent)
- [Contributing a New Skill](#contributing-a-new-skill)
- [Pull Request Workflow & Branch Conventions](#pull-request-workflow--branch-conventions)
- [Code of Conduct & Attribution](#code-of-conduct--attribution)

---

## Development Environment Setup

`oh-my-antigravity` relies on modern Python 3.13 and [`uv`](https://github.com/astral-sh/uv) for fast, reproducible dependency management.

### Prerequisites

1. **Python 3.13+** (tracked in `.python-version`)
2. **`uv` package manager** (install via `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh` / `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`)
3. **Git**

### Installation

Clone the repository and install development dependencies into an isolated virtual environment:

```bash
git clone https://github.com/HengWeiBin/oh-my-antigravity.git
cd oh-my-antigravity
uv sync
```

`uv` automatically manages the virtual environment located at `.venv/`. All commands should be executed via `uv run`.

---

## Quality Gates: Testing & Linting

Before opening a pull request, all automated quality gates must pass cleanly.

### Running Tests

We use `pytest` for unit, contract, and integration tests located in `scripts/tests/`:

```bash
uv run pytest scripts/tests/
```

To run a specific test file or test pattern:

```bash
uv run pytest scripts/tests/test_hook_engine.py
uv run pytest scripts/tests/ -k "permission"
```

### Running Linters & Formatters

We use `ruff` for linting and code formatting:

```bash
# Check for lint violations
uv run ruff check scripts/

# Automatically fix fixable violations
uv run ruff check --fix scripts/

# Check formatting
uv run ruff format --check scripts/
```

### Testing Principles

- **Zero Mocks**: Tests should verify observable behaviors and concrete data contracts rather than internal monkey-patching or mocking where possible.
- **In-Memory Isolation**: Test hook components (`BaseHook`, `HookPipeline`, `HookEngine`) with isolated `HookContext` objects.
- **Fast Execution**: The test suite should execute in under 2 seconds.

---

## Architectural Rules for Lifecycle Hooks

The lifecycle hook engine in `scripts/hooks/` and its entrypoints (`scripts/pre_invocation.py`, `scripts/pre_tool_use.py`, `scripts/post_tool_use.py`) adhere to a **strict architectural constraint**:

> [!IMPORTANT]
> **Zero Runtime Pip Dependencies**: All code in `scripts/hooks/` and hook entry points MUST use the **Python standard library ONLY** (`sys`, `os`, `json`, `pathlib`, `re`, `typing`, `dataclasses`, `enum`, etc.).

### Rationale

- **Sub-millisecond Interception**: Hooks execute synchronously on every user turn (`PreInvocation`), before every tool call (`PreToolUse`), and after tool execution (`PostToolUse`). Any third-party import overhead degrades the agent's interactive responsiveness.
- **Zero Environment Conflicts**: The plugin must operate reliably across diverse host systems, global user profiles, and workspace environments without colliding with project dependencies.
- **Zero Cold-Start Lag**: Hooks do not require virtualenv activation or dependency resolution at runtime.

Development dependencies like `pytest` and `ruff` are strictly for testing and linting. They must **never** be imported in production hook code.

### Implementing a Hook

Hooks derive from `BaseHook` in `scripts/hooks/base.py`:

```python
from scripts.hooks.base import BaseHook, HookContext, HookResult

class MyCustomHook(BaseHook):
    def process(self, context: HookContext) -> HookResult:
        # Perform standard-library logic
        return HookResult.noop()
```

---

## Contributing a New Subagent

Subagents live in the `agents/` directory and define specialized AI workers or orchestrators.

### Subagent File Formats

Antigravity supports two subagent formats:
1. **Single-file format**: `agents/<name>.md` (recommended for self-contained agents).
2. **Directory format**: `agents/<name>/agent.md` (for agents with auxiliary templates or assets).

### Required YAML Frontmatter

Every subagent file MUST begin with a YAML frontmatter block:

```yaml
---
name: my-worker-agent
description: |
  Specialized worker for database migrations and SQL schema generation.
  Triggers on SQL, schema, migration, or database optimization tasks.
mainAgent: false
subagent: true
commandExecutionPolicy: auto
model: inherit
enable_mcp_tools: true
inheritCustomizations: true
tools:
  - view_file
  - grep_search
  - list_dir
  - find_by_name
  - write_to_file
  - replace_file_content
  - run_command
skills:
  - programming
---
```

### Frontmatter Field Specifications

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | **Required** | Unique identifier (lowercase alphanumeric with hyphens). |
| `description` | `string` | **Required** | Detailed description including role, triggers, and capabilities. Used by orchestrators for routing. |
| `tools` | `string[]` | `[]` | **Mandatory Whitelist**. If omitted, the agent has NO file or command execution capabilities. |
| `mainAgent` | `boolean` | `true` | `true` if selectable as primary chat agent; `false` for background/worker subagents. |
| `subagent` | `boolean` | `true` | `true` if callable via `invoke_subagent`. |
| `model` | `string` | `inherit` | `inherit`, `flash`, or `pro`. |
| `commandExecutionPolicy` | `string` | `sandbox` | `sandbox`, `auto`, `eager`, or `off`. |
| `skills` | `string[]` | `[]` | List of bundled skills preloaded into agent context. |

### Model Selection Guidelines

- **`inherit`** (Recommended): Keeps parent model consistency.
- **`flash`**: Fast, lightweight execution. Ideal for read-only exploration, linting, or grep searches (e.g., `explore`, `librarian`).
- **`pro`**: High reasoning capacity. Ideal for complex multi-step code generation, deep refactoring, or architectural review (e.g., `hephaestus`, `oracle`).
- *Note*: Avoid `flash_lite` for agents that execute multi-step tool calls or large file edits.

### Prompt Engineering Guidelines

Structure subagent instructions with explicit sections:
- `<identity>`: Define role, mindset, and seniority level.
- `<TOOL_CALL_MANDATE>`: Require tool calls over internal guessing.
- `<Behavior_Instructions>`: Clear rules on what the agent should and shouldn't do.
- `<VERIFICATION_OVERRIDE>`: Enforce tool verification (e.g., running tests) before completion.

**Role Boundary Enforcement**:
- **Orchestrators** (e.g., `sisyphus`, `atlas`, `prometheus`) must NOT write implementation code directly; they delegate via `invoke_subagent`.
- **Workers** (e.g., `hephaestus`, `sisyphus-junior`) must NOT modify plugin configuration (`plugin.json`, `hooks.json`, `rules/`, or `.omo/` task state).

---

## Contributing a New Skill

Skills live in `skills/<name>/` and provide procedural knowledge, scripts, and workflows.

### Skill Anatomy

```
skills/<skill-name>/
├── SKILL.md            # Required: Instruction entrypoint with YAML frontmatter
├── references/         # Optional: Deep reference docs, cheatsheets, or manuals
├── scripts/            # Optional: Executable automation scripts
└── examples/           # Optional: Usage patterns and sample files
```

### `SKILL.md` Specification

`SKILL.md` must start with YAML frontmatter:

```markdown
---
name: my-skill
description: Comprehensive workflow for generating API client SDKs. Triggers on "generate sdk", "api client", "openapi codegen".
---

# My Skill Title

## Quick start
...

## Workflow Instructions
...
```

### Skill Best Practices

- **Actionable Triggers**: The `description` field must contain concrete trigger keywords and phrases so the skill resolver can automatically load or recommend the skill.
- **Script Tooling**:
  - Python scripts must run with standard library or `uv run`.
  - TypeScript/JavaScript scripts must run with `bun` or `node`.
  - **`axios` is banned**: Use standard `fetch`, `ky`, or `undici`.

---

## Pull Request Workflow & Branch Conventions

### Branch Conventions

Branch names should reflect the type of change and ticket/issue number:

- `feat/<topic>`: New features, agent profiles, or skills (e.g., `feat/sql-agent`).
- `fix/<topic>`: Bug fixes (e.g., `fix/hook-timeout`).
- `docs/<topic>`: Documentation changes (e.g., `docs/install-guide`).
- `refactor/<topic>`: Code refactoring without behavior change.
- `test/<topic>`: Adding or improving tests.

### Commit Guidelines

We encourage Conventional Commits:
- `feat: add new database-specialist agent`
- `fix: resolve path escaping issue in pre_invocation hook`
- `docs: update troubleshooting guide for Windows`
- `test: add contract tests for hook engine error handling`

### PR Submission Checklist

1. [ ] Rebase onto the latest `main` branch.
2. [ ] Ensure `uv run pytest scripts/tests/` passes with 100% success.
3. [ ] Ensure `uv run ruff check scripts/` reports no warnings or errors.
4. [ ] Verify that hook code has **zero third-party pip imports**.
5. [ ] Provide a descriptive PR title and fill out the [PULL_REQUEST_TEMPLATE](.github/PULL_REQUEST_TEMPLATE.md).
6. [ ] Reference any corresponding GitHub issues (e.g., `Fixes #6` or `Part of #1`).

---

## Code of Conduct & Attribution

### Community Standards

We are committed to providing a friendly, safe, and welcoming environment for everyone, regardless of experience level, background, or identity. Please communicate with kindness and constructive feedback.

### Upstream Heritage

`oh-my-antigravity` is derived and adapted from [`oh-my-openagent`](https://github.com/code-yeongyu/oh-my-openagent) by `code-yeongyu`. All contributions must respect existing copyright notices and maintain appropriate attribution under the MIT License.
