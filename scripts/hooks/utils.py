import json
import os
import re

def get_home_dir() -> str:
    return os.path.expanduser("~")

def resolve_path(path: str, cwd: str = None) -> str:
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    if cwd:
        return os.path.normpath(os.path.join(cwd, path))
    return os.path.normpath(os.path.abspath(path))

def is_subagent_session(payload: dict) -> bool:
    if payload.get("isSubagent") is True:
        return True
    if str(payload.get("is_subagent", "")).lower() == "true":
        return True
    if "parentConversationId" in payload:
        return True
    if payload.get("role") in ("subagent", "worker"):
        return True
    if "typename" in payload:
        return True
        
    cid = payload.get("conversationId")
    artifact_dir = payload.get("artifactDirectoryPath")
    if cid and artifact_dir:
        brain_dir = os.path.dirname(artifact_dir)
        return check_subagent_in_brain_dir(brain_dir, cid)
        
    return False

def extract_user_prompt(payload: dict) -> str:
    if "prompt" in payload:
        return payload["prompt"]
    if "userPrompt" in payload:
        return payload["userPrompt"]
    if "messages" in payload and isinstance(payload["messages"], list):
        for msg in reversed(payload["messages"]):
            if isinstance(msg, dict) and msg.get("role") == "user":
                return msg.get("content", "")
                
    # Fallback to transcript
    transcript_path = payload.get("transcriptPath")
    if not transcript_path:
        artifact_dir = payload.get("artifactDirectoryPath", "")
        if artifact_dir:
            transcript_path = os.path.join(artifact_dir, ".system_generated", "logs", "transcript.jsonl")
            if not os.path.isfile(transcript_path):
                transcript_path = os.path.join(artifact_dir, ".system_generated", "logs", "transcript_full.jsonl")
    
    if transcript_path and os.path.isfile(transcript_path):
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    try:
                        step = json.loads(line)
                        step_type = step.get("type", "")
                        if step_type in ("USER_INPUT", "USER_EXPLICIT"):
                            if "content" in step:
                                return step["content"]
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass
            
    return ""

def parse_skill_commands(prompt: str) -> list[str]:
    skills = []
    # match /skill-name but not http://
    matches = re.findall(r'(?<!http:)(?<!https:)(?:^|[^\w\-\/])/([a-zA-Z0-9_\-]+)', prompt)
    for match in matches:
        if match not in skills:
            skills.append(match)
    return skills

def is_mcp_configured_in_file(path: str, server_name: str) -> bool:
    return False

def check_mcp_active(workspaces: list[str]) -> bool:
    for wp in workspaces:
        if os.path.isdir(os.path.join(wp, ".gemini/antigravity/mcp/codegraph")):
            return True
        for p in [".agents/mcp_config.json", ".gemini/antigravity/mcp_config.json", ".gemini/config/mcp_config.json"]:
            mcp_cfg = os.path.join(wp, p)
            if os.path.isfile(mcp_cfg):
                try:
                    with open(mcp_cfg) as f:
                        if "codegraph" in f.read():
                            return True
                except Exception:
                    pass
    return False

def check_codegraph_dir_exists(workspaces: list[str], cwd: str) -> bool:
    for wp in workspaces:
        if os.path.isdir(os.path.join(wp, ".codegraph")):
            return True
    if cwd and os.path.isdir(os.path.join(cwd, ".codegraph")):
        return True
    return False

def is_cid_invoked_in_log(log_path: str, cid: str) -> bool:
    if not log_path or not os.path.isfile(log_path):
        return False
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if cid in line:
                    if "invoke_subagent" in line or "conversationId" in line or "conversation_id" in line:
                        return True
    except OSError:
        pass
    return False

def check_subagent_in_brain_dir(brain_dir: str, cid: str) -> bool:
    if not brain_dir or not os.path.isdir(brain_dir):
        return False
    try:
        for entry in os.listdir(brain_dir):
            convo_dir = os.path.join(brain_dir, entry)
            if not os.path.isdir(convo_dir):
                continue
            if entry == cid:
                continue # Skip checking own directory
            
            # check transcript
            t_path = os.path.join(convo_dir, ".system_generated", "logs", "transcript.jsonl")
            if is_cid_invoked_in_log(t_path, cid):
                return True
                
            tf_path = os.path.join(convo_dir, ".system_generated", "logs", "transcript_full.jsonl")
            if is_cid_invoked_in_log(tf_path, cid):
                return True
    except OSError:
        pass
    return False
