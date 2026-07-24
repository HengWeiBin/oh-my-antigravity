# coding-agent-sessions

## OVERVIEW
Local search and indexing utility for multi-platform coding agent session logs and databases.

## WHERE TO LOOK
| File / Path | Purpose / Description |
|---|---|
| [SKILL.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/SKILL.md) | Entry point specifying platform router routing rules and tool usage constraints. |
| [pyrightconfig.json](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/pyrightconfig.json) | Pyright configuration defining script include paths and path resolutions for typechecking. |
| [agents/openai.yaml](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/agents/openai.yaml) | YAML configuration file defining the OpenAI agent template. |
| [references/](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/references) | Platform-specific reference details for Codex, Claude, Senpi, and OpenCode. |
| [scripts/find-agent-sessions.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/find-agent-sessions.py) | Main executable CLI entrypoint invoking the underlying session indexer. |
| [scripts/agent_sessions/cli.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/cli.py) | Command line parser and output formatter for the session search tool. |
| [scripts/agent_sessions/scanners.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/scanners.py) | Conductor mapping platform keys to target scanner tasks. |
| [scripts/agent_sessions/file_scanners.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/file_scanners.py) | Scanner functions for various JSONL/file-based agents (Aider, Roo, Cline, Gemini, etc.). |
| [scripts/agent_sessions/sqlite_scanners.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/sqlite_scanners.py) | Scanners parsing local SQLite databases such as Kodu Azad.db and Cursor-CLI store.db. |
| [scripts/agent_sessions/sqlite_optional_scanners.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/sqlite_optional_scanners.py) | Scanners parsing optional SQLite databases such as Goose, Crush, Hermes, and Zed. |
| [scripts/agent_sessions/jsonio.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/jsonio.py) | Core utility functions for parsing JSON and JSONL records efficiently. |
| [scripts/agent_sessions/timeparse.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/timeparse.py) | Parses multi-format timestamps, date boundaries, and relative intervals (e.g. 7d). |
| [scripts/agent_sessions/transcript.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/transcript.py) | Parallel file parsers managing thread-pool file reading and JSONL event extraction. |
| [scripts/agent_sessions/types.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/types.py) | Shared type definitions and Pydantic/dataclass interfaces for sessions. |
| [scripts/tests/](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/tests) | Test suites verifying CLI contracts, indexers, and SQLite/JSONL scanner behaviors. |

## CONVENTIONS
- **Thread-Pool Scan Architecture**: Platform scans are executed concurrently in [scanners.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/scanners.py#L62-L72), and target log files or database connections are parsed concurrently in [transcript.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/coding-agent-sessions/scripts/agent_sessions/transcript.py#L16-L35).
- **PEP 723 Metadata Syntax**: Python scripts intended to run standalone must declare dependencies and python version requirements in inline script metadata blocks using the `# /// script` format.
- **Pytest PEP 723 Configs**: Test scripts must declare `pytest` under `dependencies` in their script block to enable running via `uv run --with pytest pytest <test_file>`.
- **Deduplication with Linkage Score**: When multiple scanners yield the same platform/id combination, standardise and select the one with a higher linkage score based on parent ID and agent metadata presence.

## ANTI-PATTERNS
- **Blocking File I/O in Platform Loop**: Avoid scanning file contents sequentially inside the platform router loop. Always delegate to thread-pool runners `jsonl_parallel` or `flat_parallel`.
- **Database Locks**: Do not open persistent write connections during scanning. Always use read-only SQLite connections and immediately close them after fetching the metadata.
- **Hardcoded Absolute User Paths**: Never use hardcoded absolute system paths (e.g. `C:\Users\name`) directly for scanning. Use `Path.home()` or `env_path()` to ensure cross-user and cross-OS portability.
