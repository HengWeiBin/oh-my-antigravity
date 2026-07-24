from __future__ import annotations

import os

def get_directory_agents_messages(payload: dict) -> list[dict]:
    """
    Walks from cwd upward to find AGENTS.md files (up to workspace root).
    Injects their content as ephemeral messages.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    try:
        cwd = payload.get("cwd", "")
        if not isinstance(cwd, str) or not cwd:
            return []

        workspace_paths_raw = payload.get("workspacePaths", [])
        workspace_paths = []
        if isinstance(workspace_paths_raw, list):
            for wp in workspace_paths_raw:
                if isinstance(wp, str) and wp:
                    workspace_paths.append(wp)

        # Normalize workspace paths
        workspace_paths = [os.path.normpath(wp) for wp in workspace_paths]

        found_files = []
        current_dir = os.path.normpath(cwd)

        while True:
            agents_file = os.path.join(current_dir, "AGENTS.md")
            if os.path.isfile(agents_file):
                try:
                    with open(agents_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 4096:
                            content = content[:4096] + "... [truncated]"
                        
                        msg = f"📋 AGENTS.md from {current_dir}:\n\n{content}"
                        found_files.append({"ephemeralMessage": msg})
                except OSError:
                    pass

            if len(found_files) >= 3:
                break

            # Stop if we've reached a workspace root
            if current_dir in workspace_paths:
                break

            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                # Reached root of file system
                break
            
            # Additional check for Windows to avoid infinite loop on drive root
            if current_dir.endswith(":\\") and parent.endswith(":\\"):
                break
                
            current_dir = parent

        # Return in reverse order so most specific is injected last
        found_files.reverse()
        return found_files
    except Exception:
        return []

run_directory_agents_injector = get_directory_agents_messages
