import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooks import fsync_skip_warning, notepad_write_guard
from hooks.utils import setup_utf8_streams

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
KNOWN_AGENTS = {"sisyphus", "atlas", "prometheus", "metis", "momus", "hephaestus", "sisyphus-junior", "explore", "librarian"}

def is_probable_conversation_id(val):
    if not isinstance(val, str):
        return False
    val_stripped = val.strip()
    if val_stripped.lower() in KNOWN_AGENTS:
        return False
    if UUID_PATTERN.match(val_stripped):
        return True
    if "-" in val_stripped:
        parts = val_stripped.split("-")
        if len(parts) >= 2 and parts[-1].isdigit():
            return True
        if len(val_stripped) == 36 and val_stripped.count("-") == 4:
            return True
    return False

def find_invoke_subagent_calls(obj):
    calls = []
    if isinstance(obj, dict):
        is_invoke = False
        for k, v in obj.items():
            if k in ("name", "tool", "toolName") and v == "invoke_subagent":
                is_invoke = True
                break
        if is_invoke:
            subagents = None
            for k, v in obj.items():
                if k.lower() == "subagents":
                    subagents = v
                    break
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        if sk.lower() == "subagents":
                            subagents = sv
                            break
                elif isinstance(v, str) and ((v.strip().startswith("{") and v.strip().endswith("}")) or (v.strip().startswith("[") and v.strip().endswith("]"))):
                    try:
                        parsed_v = json.loads(v)
                        if isinstance(parsed_v, dict):
                            for sk, sv in parsed_v.items():
                                if sk.lower() == "subagents":
                                    subagents = sv
                                    break
                    except Exception:  # noqa: BLE001, S110
                        pass
            if isinstance(subagents, list):
                type_names = []
                for sa in subagents:
                    if isinstance(sa, dict):
                        tn = sa.get("TypeName") or sa.get("typename") or sa.get("type_name")
                        if tn:
                            type_names.append(tn)
                if type_names:
                    calls.append(type_names)
        else:
            for v in obj.values():
                calls.extend(find_invoke_subagent_calls(v))
    elif isinstance(obj, list):
        for item in obj:
            calls.extend(find_invoke_subagent_calls(item))
    elif isinstance(obj, str):
        if (obj.strip().startswith("{") and obj.strip().endswith("}")) or (obj.strip().startswith("[") and obj.strip().endswith("]")):
            try:
                parsed = json.loads(obj)
                calls.extend(find_invoke_subagent_calls(parsed))
            except Exception:  # noqa: BLE001, S110
                pass
    return calls

def find_conversation_ids(obj):
    cids = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("conversationId", "conversation_id") and isinstance(v, str):
                cids.append(v)
            elif isinstance(v, str):
                if (v.strip().startswith("{") and v.strip().endswith("}")) or (v.strip().startswith("[") and v.strip().endswith("]")):
                    try:
                        parsed = json.loads(v)
                        cids.extend(find_conversation_ids(parsed))
                    except Exception:  # noqa: BLE001, S110
                        pass
                elif is_probable_conversation_id(v):
                    cids.append(v)
            else:
                cids.extend(find_conversation_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str) and is_probable_conversation_id(item):
                cids.append(item)
            else:
                cids.extend(find_conversation_ids(item))
    elif isinstance(obj, str):
        if (obj.strip().startswith("{") and obj.strip().endswith("}")) or (obj.strip().startswith("[") and obj.strip().endswith("]")):
            try:
                parsed = json.loads(obj)
                cids.extend(find_conversation_ids(parsed))
            except Exception:  # noqa: BLE001, S110
                pass
        elif is_probable_conversation_id(obj):
            cids.append(obj)
    return cids

def parse_typename_from_log(log_path, target_conversation_id, parent_cid):
    pending_type_names = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001, S112
                    continue
                
                calls = find_invoke_subagent_calls(obj)
                if calls:
                    pending_type_names.extend(calls)
                    continue
                
                line_lower = line.lower()
                if "invoke_subagent" in line_lower and ("conversationid" in line_lower or "conversation_id" in line_lower) and pending_type_names:
                    cids = []
                    found_cids = find_conversation_ids(obj)
                    for cid in found_cids:
                        if cid != parent_cid:
                            cids.append(cid)
                    if cids:
                        tns = pending_type_names.pop(0)
                        for i in range(min(len(tns), len(cids))):
                            if cids[i] == target_conversation_id:
                                return tns[i]
    except Exception:  # noqa: BLE001, S110
        pass
    return None


def check_permission(tool_name, file_path, conversation_id, brain_dir):
    normalized_path = file_path.replace("\\", "/").lower()
    basename = os.path.basename(normalized_path)
    
    # 1. Parse the TypeName of the conversation_id from logs
    typename = None
    if conversation_id and brain_dir and os.path.exists(brain_dir):
        for cid in os.listdir(brain_dir):
            if cid == conversation_id:
                continue
            cid_dir = os.path.join(brain_dir, cid)
            if not os.path.isdir(cid_dir):
                continue
            logs_dir = os.path.join(cid_dir, ".system_generated", "logs")
            if not os.path.exists(logs_dir):
                continue
            for name in ["transcript.jsonl", "transcript_full.jsonl"]:
                log_path = os.path.join(logs_dir, name)
                if os.path.exists(log_path):
                    parsed_typename = parse_typename_from_log(log_path, conversation_id, cid)
                    if parsed_typename:
                        typename = parsed_typename
                        break
            if typename:
                break
                
    conductors = {None, "sisyphus", "atlas", "prometheus", "metis", "momus"}
    workers = {"hephaestus", "sisyphus-junior", "explore", "librarian"}
    
    is_worker = False
    if typename in workers:
        is_worker = True
    elif typename in conductors:
        is_worker = False
    else:
        is_worker = (typename is not None)
        
    # 2. Apply role-specific constraints
    if is_worker:
        # Subagent Constraints:
        # Cannot write to .agents/, or plugin config files (hooks.json, plugin.json, rules/)
        # For .omo/: writing to .omo/plans/ or files in .omo/ containing "plan", "task", or "draft" in the path/filename is denied,
        # but writing to .omo/notepads/ is allowed. Other .omo/ files are not denied.
        is_omo = "/.omo/" in normalized_path or normalized_path.startswith(".omo/")
        deny_omo = False
        if is_omo:
            idx = normalized_path.find("/.omo/")
            if idx != -1:
                subpath = normalized_path[idx + 1:]
            elif normalized_path.startswith(".omo/"):
                subpath = normalized_path
            else:
                subpath = ""
            
            is_omo_notepads = subpath.startswith(".omo/notepads/")
            is_omo_plans = subpath.startswith(".omo/plans/")
            contains_deny_word = any(w in subpath for w in ["plan", "task", "draft"])
            
            if not is_omo_notepads and (is_omo_plans or contains_deny_word):
                deny_omo = True
        
        is_agents = "/.agents/" in normalized_path or normalized_path.startswith(".agents/")
        is_plugin_config = (
            "hooks.json" in basename or
            "plugin.json" in basename or
            "/rules/" in normalized_path or
            normalized_path.startswith("rules/")
        )
        
        if deny_omo or is_agents or is_plugin_config:
            return {
                "decision": "deny",
                "reason": (
                    f"STOP. Subagents (workers) are forbidden from modifying .omo/ state or "
                    f"plugin configuration files (Path: {file_path})."
                )
            }
    else:
        # Orchestrator Constraints:
        # Cannot write to product files directly.
        # Allowed files for orchestrator:
        # - .md files
        # - plans/tasks files (filename contains 'plan' or 'task')
        # - .agents/ files
        # - .omo/ files
        is_plan = "plan" in basename or "task" in basename or normalized_path.endswith(".md")
        is_agents = "/.agents/" in normalized_path or normalized_path.startswith(".agents/")
        is_omo = "/.omo/" in normalized_path or normalized_path.startswith(".omo/")
        
        if not (is_plan or is_agents or is_omo):
            return {
                "decision": "ask",
                "reason": (
                    f"STOP. Lead Orchestrator agents do not edit source code directly (Path: {file_path}).\n"
                    "Implementing yourself is forbidden. You are paid to ORCHESTRATE, not implement.\n"
                    "If this is a tiny verification fix (<= 2 lines) on subagent output, you may proceed. "
                    "Otherwise, please delegate it via invoke_subagent."
                )
            }
            
    return {"decision": "allow"}

def main():
    setup_utf8_streams()
    try:
        # Read JSON from stdin
        payload = json.load(sys.stdin)
        
        # Support both schemas
        tool_name = payload.get("tool_name")
        if not tool_name and "toolCall" in payload:
            tool_name = payload["toolCall"].get("name")
        
        tool_input = payload.get("tool_input")
        if not tool_input and "toolCall" in payload:
            tool_input = payload["toolCall"].get("args", {})
        if not tool_input:
            tool_input = {}
            
        conversation_id = payload.get("conversationId", "")
        artifact_dir = payload.get("artifactDirectoryPath", "")
        brain_dir = os.path.dirname(artifact_dir) if artifact_dir else ""
        
        # Check if tool is write/edit
        if tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
            # Extract file path
            file_path = tool_input.get("TargetFile", "")
            if not file_path:
                file_path = tool_input.get("file_path", "")
            
            # If path is specified, check it
            if file_path:
                decision = check_permission(tool_name, file_path, conversation_id, brain_dir)
                if decision.get("decision") != "allow":
                    print(json.dumps(decision, ensure_ascii=False))
                    return
            
            res = notepad_write_guard.run_notepad_write_guard(tool_name, tool_input)
            if res and res.get("decision") != "allow":
                print(json.dumps(res, ensure_ascii=False))
                return

        elif tool_name == "run_command":
            res = fsync_skip_warning.run_fsync_skip_warning(tool_name, tool_input)
            if res and res.get("decision") != "allow":
                print(json.dumps(res, ensure_ascii=False))
                return
        
        # Default allow
        print(json.dumps({"decision": "allow"}, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        # Fallback to allow if any error
        print(json.dumps({"decision": "allow"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
