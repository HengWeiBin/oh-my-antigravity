---
name: antigravity-subagent-tools
description: Guide and best practices for configuring sub-agent tools in Antigravity 2.0 Markdown plugins. Use this skill when users encounter issues with sub-agents lacking read or write tools (e.g., view_file, grep_search), or when users want to know how to properly define a sub-agent's tool permissions in agent definition files.
---

# Antigravity Sub-Agent Tool Configuration Guide

When defining sub-agents in Antigravity 2.0 via Markdown files (e.g., in a plugin's `agents/` directory), tool permissions must be carefully configured. 

**Critical Rule**: Antigravity **does not automatically grant default file system tools** (like read or write) to sub-agents loaded from Markdown files unless explicitly declared.

This guide outlines the best practices for configuring tools to avoid the common pitfall of sub-agents being instantiated with only basic conversational tools (`send_message`, `schedule`).

## The Core Pitfall

Developers often assume that adding `enable_write_tools: true` will implicitly grant read tools, or that read tools are provided by default. **This is incorrect.** The environment strictly adheres to explicit whitelisting.

If a sub-agent is meant to be "Read-Only" (e.g., a codebase researcher) and you omit `enable_write_tools: true` for safety, that agent will end up with **zero** file system tools unless you explicitly define a `tools:` array.

## Best Practice: Explicit Tool Whitelisting

The most robust and secure way to configure sub-agent tools is to abandon vague capability flags (like `enable_write_tools`) and instead use an explicit `tools:` array to declare an exact whitelist of required tools.

### 1. Read-Only & Research Agents
For agents that only need to search and read the codebase (e.g., an `explore` or `librarian` agent), use the following configuration. This safely grants them codebase exploration capabilities without risking unauthorized modifications.

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

### 2. Execution & Orchestration Agents
For agents that need full access to modify files, run terminal commands, and spawn other sub-agents (e.g., `atlas`, `hephaestus`), explicitly list all required read, write, and orchestration tools.

```yaml
---
name: atlas
description: Master orchestrator that executes plans.
model: inherit
enable_mcp_tools: true
tools:
  - view_file
  - grep_search
  - list_dir
  - find_by_name
  - read_url_content
  - search_web
  - multi_replace_file_content
  - replace_file_content
  - write_to_file
  - run_command
  - invoke_subagent
  - manage_subagents
  - manage_task
  - define_subagent
---
```

## Important Note on Active Workspaces

If you test an agent via `invoke_subagent` and it still reports missing tools despite a correct `tools:` configuration, check your environment:

**Antigravity will purposefully strip all file system tools (both read and write) from a sub-agent if the parent agent is not operating within an Active Workspace.** 

Always ensure you are testing sub-agent tool configurations within a valid project workspace.
