---
name: antigravity-subagents
description: Complete guide and best practices for defining, configuring, and prompting sub-agents in Antigravity 2.0. Covers YAML frontmatter fields (name, model, tools, skills, workspace), explicit tool whitelisting, dynamic vs static agent definitions, workspace isolation, and prompt structuring. Use this skill when creating new sub-agents, updating agent configuration files in agents/*.md, fixing sub-agent permission issues, or configuring sub-agent skills and tools.
---

# Antigravity Sub-Agent Configuration & Best Practices Guide

In Google Antigravity 2.0, sub-agents can be defined statically via Markdown files in a plugin's `agents/` directory or dynamically at runtime using `define_subagent`.

This guide covers all configuration fields, frontmatter parameters, tool whitelisting rules, skill pre-loading, workspace modes, and prompt structuring best practices.

---

## 1. Sub-Agent Definition Architecture

Sub-agents can be defined in two ways:

### Static Markdown Agent Definition (`agents/<name>.md`)
Static sub-agents reside in the `agents/` directory of a plugin (e.g., `agents/explore.md`, `agents/atlas.md`). They consist of:
1. **YAML Frontmatter**: Defines metadata, model tier, tool whitelists, pre-loaded skills, and workspace mode.
2. **Markdown Body**: System prompt containing persona `<identity>`, mandates, scope constraints, and execution workflow.

### Dynamic Sub-Agent Definition (`define_subagent`)
Sub-agents can also be registered at runtime using the `define_subagent` tool:
- `name`: Unique identifier.
- `description`: Human-readable summary of when and how to invoke the sub-agent.
- `system_prompt`: Detailed system prompt for the sub-agent.
- `enable_write_tools`, `enable_mcp_tools`, `enable_subagent_tools`: Capability flags.

---

## 2. YAML Frontmatter Specification

When defining static sub-agents in `agents/<name>.md`, the frontmatter supports the following configuration fields:

| Field | Type | Values / Examples | Description |
|---|---|---|---|
| `name` | string | `explore`, `hephaestus`, `atlas` | Unique identifier used when calling `invoke_subagent`. |
| `description` | string | Multiline or single-line text | Concise summary of role & triggers used by main agent router. |
| `mainAgent` | boolean | `true`, `false` | Specifies whether the agent can act as a primary entrypoint orchestrator. |
| `model` | string | `inherit`, `pro`, `flash`, `flash_lite` | LLM model selection. `inherit` (default) uses parent agent's model. |
| `enable_mcp_tools` | boolean | `true`, `false` | Enables access to registered Model Context Protocol (MCP) tools. |
| `inheritCustomizations` | boolean | `true`, `false` | Inherits parent workspace/plugin skills, rules, and customizations. |
| `tools` | list of strings | `- view_file`<br>`- grep_search`<br>`- run_command` | **Explicit whitelist of allowed tools.** (Required for file/command access!) |
| `skills` | list of strings | `- start-work`<br>`- ast-grep`<br>`- ultrawork` | Pre-loads specific skills into the sub-agent's session context. |
| `workspace` | string | `inherit`, `branch`, `share` | Execution workspace isolation mode. |

---

## 3. Tool Permissions & Critical Whitelisting Rules

### The Core Tool Pitfall
Antigravity **does NOT automatically grant default file system tools** (like `view_file` or `grep_search`) to sub-agents declared via Markdown files unless explicitly whitelisted in `tools:`.

- Omission of `tools:` results in a sub-agent with **zero** file tools (only base communication tools like `send_message`).
- Setting capability flags without explicit `tools:` may not grant full read/write access.

### Standard Tool Sets

#### A. Read-Only & Research Agents (e.g., `explore`, `librarian`)
```yaml
---
name: explore
description: Read-only codebase search specialist.
model: inherit
enable_mcp_tools: true
tools:
  - view_file
  - grep_search
  - list_dir
  - find_by_name
  - read_url_content
  - search_web
---
```

#### B. Execution & Orchestration Agents (e.g., `atlas`, `hephaestus`, `sisyphus-junior`)
```yaml
---
name: hephaestus
description: Autonomous deep worker for complex implementation tasks.
model: inherit
enable_mcp_tools: true
tools:
  - view_file
  - grep_search
  - list_dir
  - find_by_name
  - read_url_content
  - search_web
  - replace_file_content
  - multi_replace_file_content
  - write_to_file
  - run_command
  - invoke_subagent
  - manage_task
  - define_subagent
  - manage_subagents
skills:
  - programming
  - ast-grep
  - debugging
---
```

---

## 4. Pre-Loading Skills (`skills:`)

Sub-agents can have domain-specific skills pre-loaded automatically into their context using the `skills:` list:

```yaml
skills:
  - start-work
  - teammode
  - ultrawork
  - ast-grep
```

When the sub-agent is invoked via `invoke_subagent`, the specified skills will be available in its execution environment without requiring manual `/skill-name` invocation.

---

## 5. Workspace Isolation Modes (`workspace:`)

Antigravity supports 3 workspace modes for sub-agents:

1. `inherit` (Default): Uses the exact same working directory and workspace as the parent agent.
2. `branch`: Spawns the sub-agent in an isolated workspace copy/branch. Changes will not affect the main working tree until merged.
3. `share`: Creates a shared workspace (similar to git worktree), enabling parallel modifications without full repository duplication.

---

## 6. Active Workspace Dependency (Tool Stripping Warning)

If a sub-agent is initialized and fails to access file system tools despite having `tools:` correctly defined:

**Antigravity will purposefully strip all file system tools (both read and write) from sub-agents if the parent agent is not operating within an Active Workspace.**

Always ensure execution takes place inside a valid project workspace.

---

## 7. Sub-Agent System Prompt Structure

To maximize execution quality, sub-agent markdown bodies should use clear XML block formatting:

```markdown
<identity>
Define role, persona, and responsibility clearly.
</identity>

<TOOL_CALL_MANDATE>
Enforce tool execution. Sub-agents MUST use tools to inspect state instead of guessing.
</TOOL_CALL_MANDATE>

<mission>
Define primary goal and completion criteria.
</mission>

<scope_and_design_constraints>
Define strict boundaries: what to modify, what NOT to touch.
</scope_and_design_constraints>

<workflow>
Step-by-step procedure: Plan → Explore → Execute → Verify.
</workflow>
```
