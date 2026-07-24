from __future__ import annotations

import json
import os
import re
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


def is_cid_invoked_in_log(log_path: str, target_cid: str) -> bool:
    """Check if target_cid was invoked as a subagent by the conversation owning log_path."""
    try:
        target_lower = target_cid.lower()
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                line_lower = line.lower()
                if target_lower in line_lower:
                    if "invoke_subagent" in line_lower or "created the following subagents" in line_lower:
                        return True
                    if f'"conversationid": "{target_lower}"' in line_lower or f'"conversationid":  "{target_lower}"' in line_lower:
                        return True
    except Exception:
        pass
    return False


def check_subagent_in_brain_dir(brain_dir: str, target_cid: str) -> bool:
    """Check transcript logs in brain directory to see if target_cid was invoked as subagent."""
    try:
        if not os.path.isdir(brain_dir):
            return False
        for cid in os.listdir(brain_dir):
            if cid == target_cid:
                continue
            cid_dir = os.path.join(brain_dir, cid)
            if not os.path.isdir(cid_dir):
                continue
            logs_dir = os.path.join(cid_dir, ".system_generated", "logs")
            if not os.path.exists(logs_dir):
                continue
            for name in ("transcript.jsonl", "transcript_full.jsonl"):
                log_path = os.path.join(logs_dir, name)
                if os.path.isfile(log_path):
                    if is_cid_invoked_in_log(log_path, target_cid):
                        return True
    except Exception:
        pass
    return False


def is_subagent_session(payload: dict) -> bool:
    """Check if the payload represents a SubAgent session."""
    if not isinstance(payload, dict):
        return False

    # 1. Direct subagent boolean/string flags
    for key in ("isSubagent", "is_subagent", "isSubAgent"):
        val = payload.get(key)
        if val is True or (isinstance(val, str) and val.strip().lower() == "true"):
            return True

    # 2. Parent conversation ID checks
    for key in ("parentConversationId", "parent_conversation_id", "parentConversationID", "parentId", "parent_id"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return True

    # 3. Check role/typename
    worker_roles = {"subagent", "worker", "hephaestus", "sisyphus-junior", "explore", "librarian"}
    for key in ("role", "typename", "type_name", "agentRole", "agent_role"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            val_lower = val.strip().lower()
            if val_lower in worker_roles or "subagent" in val_lower or "worker" in val_lower:
                return True

    # 4. Check transcript logs in brain directories
    cid = payload.get("conversationId") or payload.get("conversation_id")
    if isinstance(cid, str) and cid.strip():
        target_cid = cid.strip()

        brain_dirs: list[str] = []
        artifact_dir = payload.get("artifactDirectoryPath") or payload.get("artifact_directory_path")
        if isinstance(artifact_dir, str) and artifact_dir.strip():
            b_dir = os.path.dirname(os.path.abspath(artifact_dir.strip()))
            if os.path.isdir(b_dir) and b_dir not in brain_dirs:
                brain_dirs.append(b_dir)

        home = get_home_dir()
        default_brain = os.path.join(home, ".gemini", "antigravity", "brain")
        if os.path.isdir(default_brain) and default_brain not in brain_dirs:
            brain_dirs.append(default_brain)

        workspace_paths_raw = payload.get("workspacePaths") or payload.get("workspace_paths") or []
        if isinstance(workspace_paths_raw, list):
            for wp in workspace_paths_raw:
                if isinstance(wp, str) and wp:
                    wp_brain = os.path.join(wp, ".gemini", "antigravity", "brain")
                    if os.path.isdir(wp_brain) and wp_brain not in brain_dirs:
                        brain_dirs.append(wp_brain)

        for b_dir in brain_dirs:
            if check_subagent_in_brain_dir(b_dir, target_cid):
                return True

    return False


def extract_user_prompt(payload: dict) -> str:
    """Extract user prompt text from payload dictionary or transcript file."""
    if not isinstance(payload, dict):
        return ""

    # Direct string fields
    for key in (
        "prompt",
        "userPrompt",
        "user_prompt",
        "promptText",
        "prompt_text",
        "message",
        "userMessage",
        "user_message",
        "input",
        "userInput",
        "user_input",
        "text",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    # Check messages list
    messages = payload.get("messages")
    if isinstance(messages, list):
        for msg in reversed(messages):
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
            elif isinstance(msg, dict):
                role = msg.get("role", "")
                if role in ("user", "") or len(messages) == 1:
                    content = msg.get("content") or msg.get("text") or msg.get("prompt")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                    elif isinstance(content, list):
                        parts = []
                        for part in content:
                            if isinstance(part, str):
                                parts.append(part)
                            elif isinstance(part, dict) and "text" in part:
                                parts.append(str(part["text"]))
                        if parts:
                            return "\n".join(parts).strip()

    # Fallback to transcriptPath or transcript.jsonl
    transcript_path = payload.get("transcriptPath") or payload.get("transcript_path")
    paths_to_try: list[str] = []
    if isinstance(transcript_path, str) and transcript_path.strip():
        resolved_t_path = resolve_path(transcript_path.strip())
        paths_to_try.append(resolved_t_path)
        dir_name = os.path.dirname(resolved_t_path)
        paths_to_try.append(os.path.join(dir_name, "transcript.jsonl"))

    for t_path in paths_to_try:
        if os.path.isfile(t_path):
            try:
                with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("type") in ("USER_INPUT", "USER_EXPLICIT") or data.get("source") == "USER_EXPLICIT":
                                content = data.get("content", "")
                                if isinstance(content, str) and content.strip():
                                    cleaned = content.strip()
                                    if "<USER_REQUEST>" in cleaned:
                                        m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", cleaned, re.DOTALL)
                                        if m:
                                            cleaned = m.group(1).strip()
                                    return cleaned
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

    return ""


def parse_skill_commands(prompt_text: str) -> list[str]:
    """Extract skill commands like /skill-name from user prompt using regex."""
    if not prompt_text:
        return []
    matches = re.findall(r"(?:^|\s)/([a-zA-Z0-9_\-]+)", prompt_text)
    seen = set()
    result = []
    for skill in matches:
        if skill and skill not in seen:
            seen.add(skill)
            result.append(skill)
    return result


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

        print(json.dumps({"injectSteps": steps}))
    except Exception:  # noqa: BROAD_EXCEPT_OK
        print(json.dumps({}))


if __name__ == "__main__":
    main()

