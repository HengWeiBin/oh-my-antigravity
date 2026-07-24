#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run pre_invocation.py
# ──────────────────

from __future__ import annotations

import json
import os
import sys


def get_home_dir() -> str:
    """Get the user's home directory from environment variables or expanduser."""
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not home:
        home = os.path.expanduser("~")
    return os.path.abspath(home)


def resolve_path(path_str: str, base_dir: str | None = None) -> str:
    """Resolve environment variables, home directory (~), and relative paths."""
    if not path_str:
        return ""
    expanded = os.path.expandvars(path_str)
    expanded = os.path.expanduser(expanded)
    if not os.path.isabs(expanded):
        if base_dir:
            expanded = os.path.join(base_dir, expanded)
        else:
            expanded = os.path.abspath(expanded)
    return os.path.abspath(expanded)


def is_mcp_configured_in_file(file_path: str) -> bool:
    """Check if 'codegraph' is defined in 'mcpServers' in the given JSON file."""
    if not os.path.isfile(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return False
            data = json.loads(content)
            if isinstance(data, dict):
                mcp_servers = data.get("mcpServers")
                if isinstance(mcp_servers, dict) and "codegraph" in mcp_servers:
                    return True
    except (json.JSONDecodeError, OSError):
        return False
    return False


def check_mcp_active(workspace_paths: list[str]) -> bool:
    """Check if codegraph MCP is configured in any of the standard locations."""
    home = get_home_dir()

    # 1. ~/.gemini/config/mcp_config.json
    p1 = os.path.join(home, ".gemini", "config", "mcp_config.json")
    if is_mcp_configured_in_file(p1):
        return True

    # 2. ~/.gemini/antigravity/mcp_config.json
    p2 = os.path.join(home, ".gemini", "antigravity", "mcp_config.json")
    if is_mcp_configured_in_file(p2):
        return True

    # 3. .agents/mcp_config.json (inside any of the workspace paths)
    for wp in workspace_paths:
        p3 = os.path.join(wp, ".agents", "mcp_config.json")
        if is_mcp_configured_in_file(p3):
            return True

    # 4. Check if directory ~/.gemini/antigravity/mcp/codegraph exists
    p4 = os.path.join(home, ".gemini", "antigravity", "mcp", "codegraph")
    if os.path.isdir(p4):
        return True

    return False


def check_codegraph_dir_exists(workspace_paths: list[str], cwd: str) -> bool:
    """Check if '.codegraph' directory exists in workspace_paths or cwd."""
    paths_to_check = list(workspace_paths)
    if cwd:
        paths_to_check.append(cwd)

    for p in paths_to_check:
        if not p:
            continue
        codegraph_path = os.path.join(p, ".codegraph")
        if os.path.isdir(codegraph_path):
            return True
    return False


def main() -> None:
    try:
        # Read JSON payload from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            payload = {}
        else:
            payload = json.loads(input_data)

        if not isinstance(payload, dict):
            payload = {}

        invocation_num = payload.get("invocationNum", 0)
        if not isinstance(invocation_num, int):
            invocation_num = 0

        workspace_paths_raw = payload.get("workspacePaths")
        workspace_paths = []
        if isinstance(workspace_paths_raw, list):
            for wp in workspace_paths_raw:
                if isinstance(wp, str) and wp:
                    workspace_paths.append(wp)

        cwd = payload.get("cwd", "")
        if not isinstance(cwd, str):
            cwd = ""

        # Only run hook logic on invocationNum == 0
        if invocation_num == 0:
            resolved_cwd = resolve_path(cwd) if cwd else ""
            resolved_workspaces = [
                resolve_path(wp, resolved_cwd if resolved_cwd else None)
                for wp in workspace_paths
            ]

            codegraph_exists = check_codegraph_dir_exists(resolved_workspaces, resolved_cwd)
            mcp_active = check_mcp_active(resolved_workspaces)

            if codegraph_exists and mcp_active:
                msg = (
                    "A `.codegraph` directory and the `codegraph` MCP server are active in this workspace. "
                    "You should prioritize using `codegraph_explore` to explore symbols, find call paths, "
                    "and understand the codebase architecture in a single round-trip instead of standard grep + read loops."
                )
                print(json.dumps({"injectSteps": [{"ephemeralMessage": msg}]}))
                return

        # Default fallback
        print(json.dumps({"injectSteps": []}))
    except Exception:  # noqa: BROAD_EXCEPT_OK
        print(json.dumps({}))


if __name__ == "__main__":
    main()
