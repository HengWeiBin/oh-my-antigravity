from __future__ import annotations
import re

WARNING_MSG = '⚠️ EMPTY SUBAGENT RESPONSE DETECTED: The subagent returned a very short or empty response. This is suspicious — the subagent may have failed silently. Please verify by checking the subagent transcript or re-dispatching with a more explicit task.'

def check_empty_task_response(tool_name: str, tool_response: dict | str | None) -> str | None:
    """
    Analyzes the response from invoke_subagent.
    Returns a warning string if response is empty/near-empty (< 50 meaningful chars).
    Returns None if response looks normal.
    """
    if tool_name != 'invoke_subagent':
        return None

    if tool_response is None:
        return WARNING_MSG

    text = ""
    if isinstance(tool_response, str):
        text = tool_response
    elif isinstance(tool_response, dict):
        for key in ['output', 'result', 'content', 'message']:
            if key in tool_response:
                val = tool_response[key]
                if isinstance(val, str):
                    text = val
                    break
                elif val is not None:
                    text = str(val)
                    break

    # Clean text
    clean_text = text.lower()
    for phrase in ['done', 'completed', 'ok', 'yes']:
        # remove standalone phrases
        clean_text = re.sub(rf'\b{phrase}\b', '', clean_text)
        
    # Remove whitespace to count meaningful chars
    meaningful_content = re.sub(r'\s+', '', clean_text)
    
    if len(meaningful_content) < 50:
        return WARNING_MSG
        
    return None

run_empty_task_response_detector = check_empty_task_response
