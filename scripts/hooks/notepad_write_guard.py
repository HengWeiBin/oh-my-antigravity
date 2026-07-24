from __future__ import annotations

import os

def check_notepad_write_guard(tool_name: str, tool_input: dict) -> dict | None:
    """
    Returns a denial dict if the write would destructively shrink a notepad file >50%.
    Returns None to allow the write.
    """
    if tool_name != "write_to_file":
        return None
        
    target_file = tool_input.get("TargetFile", "")
    if not target_file:
        return None
        
    normalized_path = target_file.replace("\\", "/")
    if "/.omo/notepads/" not in normalized_path:
        return None
        
    new_content = tool_input.get("CodeContent", "")
    
    if not os.path.exists(target_file):
        return None
        
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            old_content = f.read()
    except Exception:
        return None
        
    if not old_content:
        return None
        
    if len(new_content) < (len(old_content) / 2.0):
        return {
            "permissionDecision": "deny",
            "permissionDecisionReason": "NOTEPAD WRITE GUARD: This write would reduce the notepad content by >50%, which is likely an accidental overwrite. Use replace_file_content or multi_replace_file_content to make targeted edits instead."
        }
        
    return None

run_notepad_write_guard = check_notepad_write_guard
