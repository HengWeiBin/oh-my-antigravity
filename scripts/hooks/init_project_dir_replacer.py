from __future__ import annotations

import os
import sys

# Ensure the scripts directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.abspath(os.path.join(current_dir, ".."))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from hooks.utils import extract_user_prompt, parse_skill_commands, resolve_path  # noqa: E402


def format_skill_instruction(skill_name: str, skill_content: str) -> str:
    """Format skill content into <skill-instruction> block."""
    content = skill_content.strip()
    return f"<skill-instruction>\n{content}\n</skill-instruction>"


def get_project_dir(payload: dict) -> str:
    """Determine the active project/workspace directory from payload."""
    workspace_paths = payload.get("workspacePaths")
    if isinstance(workspace_paths, list) and workspace_paths:
        first_path = workspace_paths[0]
        if isinstance(first_path, str) and first_path:
            return resolve_path(first_path)

    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return resolve_path(cwd)

    return resolve_path(os.getcwd())


def run_init_project_dir_replacer(payload: dict) -> list[dict]:
    """
    Hook triggered when the user uses the 'init' skill (e.g. /init, $init, or mentioning init skill).
    Replaces {project_dir} in the skill instructions with the actual project directory path.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    prompt = extract_user_prompt(payload)
    if not prompt:
        return []

    # Check if prompt triggers /init or $init or mentions init skill
    skill_cmds = parse_skill_commands(prompt)
    has_init = "init" in skill_cmds or "/init" in prompt.lower() or "$init" in prompt.lower()

    if not has_init:
        return []

    project_dir = get_project_dir(payload)

    # Locate skills/init/SKILL.md
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_path = os.path.join(plugin_dir, "skills", "init", "SKILL.md")

    if not os.path.isfile(skill_path):
        return []

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace {project_dir} with the actual project directory
        content_replaced = content.replace("{project_dir}", project_dir)
        formatted = format_skill_instruction("init", content_replaced)

        return [{"ephemeralMessage": formatted}]
    except OSError:
        return []
