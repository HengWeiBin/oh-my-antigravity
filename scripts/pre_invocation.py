from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooks import (
    agent_usage_reminder,
    compaction_todo_preserver,
    directory_agents_injector,
    init_project_dir_replacer,
    keyword_detector,
    rules_injector,
    todo_continuation_enforcer,
)
from hooks.utils import (
    check_codegraph_dir_exists,
    check_mcp_active,
    extract_user_prompt,
    get_home_dir,
    is_subagent_session,
    parse_skill_commands,
    resolve_path,
    setup_utf8_streams,
)


def find_skill_md_file(skill_name: str, workspace_paths: list[str], cwd: str) -> str | None:
    """Find SKILL.md file for the given skill name across workspace, plugin, user config, and builtin skills."""
    if not skill_name:
        return None

    home = get_home_dir()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.dirname(script_dir)

    dirs_to_check: list[str] = []
    for wp in workspace_paths:
        if wp and wp not in dirs_to_check:
            dirs_to_check.append(wp)
    if cwd and cwd not in dirs_to_check:
        dirs_to_check.append(cwd)

    paths_to_check: list[str] = []

    # 1. Workspace skills
    for d in dirs_to_check:
        paths_to_check.append(os.path.join(d, "skills", skill_name, "SKILL.md"))
        paths_to_check.append(os.path.join(d, ".agents", "skills", skill_name, "SKILL.md"))
        paths_to_check.append(os.path.join(d, ".gemini", "skills", skill_name, "SKILL.md"))

    # 2. Plugin skills
    paths_to_check.append(os.path.join(plugin_dir, "skills", skill_name, "SKILL.md"))

    # 2.5 Sibling plugin directories
    plugins_dir = os.path.dirname(plugin_dir)
    if os.path.isdir(plugins_dir):
        try:
            for entry in os.listdir(plugins_dir):
                d = os.path.join(plugins_dir, entry)
                if os.path.isdir(d) and entry != os.path.basename(plugin_dir):
                    paths_to_check.append(os.path.join(d, "skills", skill_name, "SKILL.md"))
        except OSError:
            pass

    # 3. User config skills
    paths_to_check.append(os.path.join(home, ".gemini", "config", "skills", skill_name, "SKILL.md"))

    # 4. Builtin skills
    paths_to_check.append(os.path.join(home, ".gemini", "antigravity", "builtin", "skills", skill_name, "SKILL.md"))

    for path in paths_to_check:
        resolved = resolve_path(path)
        if os.path.isfile(resolved):
            return resolved

    return None


def format_skill_instruction(skill_name: str, skill_content: str) -> str:
    """Format skill content into <skill-instruction> block."""
    content = skill_content.strip()
    return f"<skill-instruction>\n{content}\n</skill-instruction>"


def main() -> None:
    setup_utf8_streams()
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

        resolved_cwd = resolve_path(cwd) if cwd else ""
        resolved_workspaces = [
            resolve_path(wp, resolved_cwd if resolved_cwd else None)
            for wp in workspace_paths
        ]

        steps: list[dict[str, str]] = []

        try:
            res = directory_agents_injector.run_directory_agents_injector(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = rules_injector.run_rules_injector(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = compaction_todo_preserver.run_compaction_todo_preserver(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = todo_continuation_enforcer.run_todo_continuation_enforcer(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = agent_usage_reminder.run_agent_usage_reminder(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = keyword_detector.run_keyword_detector(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass
        try:
            res = init_project_dir_replacer.run_init_project_dir_replacer(payload)
            if res:
                steps.extend(res)
        except Exception:  # noqa: BLE001, S110
            pass

        # Retain existing invocationNum == 0 codegraph recommendation behavior
        if invocation_num == 0:
            codegraph_exists = check_codegraph_dir_exists(resolved_workspaces, resolved_cwd)
            mcp_active = check_mcp_active(resolved_workspaces)

            if codegraph_exists and mcp_active:
                msg = (
                    "A `.codegraph` directory and the `codegraph` MCP server are active in this workspace. "
                    "You should prioritize using `codegraph_explore` to explore symbols, find call paths, "
                    "and understand the codebase architecture in a single round-trip instead of standard grep + read loops."
                )
                steps.append({"ephemeralMessage": msg})

        # SubAgent skill auto-loader (ONLY for SubAgent sessions)
        if is_subagent_session(payload):
            user_prompt = extract_user_prompt(payload)
            if user_prompt:
                skill_names = parse_skill_commands(user_prompt)
                for s_name in skill_names:
                    md_path = find_skill_md_file(s_name, resolved_workspaces, resolved_cwd)
                    if md_path:
                        try:
                            with open(md_path, "r", encoding="utf-8") as f:
                                skill_content = f.read()
                            formatted = format_skill_instruction(s_name, skill_content)
                            steps.append({"ephemeralMessage": formatted})
                        except OSError:
                            pass

        print(json.dumps({"injectSteps": steps}, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        print(json.dumps({}, ensure_ascii=False))


if __name__ == "__main__":
    main()

