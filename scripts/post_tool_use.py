import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooks import empty_task_response_detector, comment_checker, plan_format_validator

def main():
    try:
        # Read JSON from stdin
        payload = json.load(sys.stdin)
        tool_name = payload.get("tool_name")
        if not tool_name and "toolCall" in payload:
            tool_name = payload["toolCall"].get("name")
        
        contexts = []

        # Check if subagent was invoked
        if tool_name == "invoke_subagent":
            # Inject verification reminder
            contexts.append(
                "**THE SUBAGENT HAS FINISHED. THEIR WORK IS EXTREMELY SUSPICIOUS. YOU MUST VERIFY WITH ACTUAL TOOL CALLS. NOT REASONING. TOOL CALLS.**\n\n"
                "Subagents ROUTINELY produce broken, incomplete, wrong code and then claim it is done. "
                "Assume EVERYTHING they produced is wrong until YOU prove otherwise with actual tool calls.\n\n"
                "4-Phase Protocol (every delegation, no exceptions):\n"
                "1. **READ CODE** - Read every changed file, trace logic, check scope.\n"
                "2. **RUN CHECKS** - Run build, tests, lint diagnostics using run_command.\n"
                "3. **HANDS-ON QA** - Actually run/open/interact with the deliverable using browser_subagent (/browser) or curl.\n"
                "4. **GATE DECISION** - Can you explain every line? Did you see it work? Confident nothing broke?\n\n"
                "On failure: Resume the SAME session conversation ID with the SPECIFIC failure message using send_message."
            )
            
            tool_response = payload.get("tool_response")
            empty_msg = empty_task_response_detector.run_empty_task_response_detector(tool_name, tool_response)
            if empty_msg:
                contexts.append(empty_msg)

        elif tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
            tool_input = payload.get("tool_input")
            if not tool_input and "toolCall" in payload:
                tool_input = payload["toolCall"].get("args", {})
            if not tool_input:
                tool_input = {}
                
            tool_response = payload.get("tool_response")
            
            comment_msg = comment_checker.run_comment_checker(tool_name, tool_input, tool_response)
            if comment_msg:
                contexts.append(comment_msg)
                
            plan_msg = plan_format_validator.run_plan_format_validator(tool_name, tool_input, tool_response)
            if plan_msg:
                contexts.append(plan_msg)
                
        if contexts:
            combined_context = "\n\n".join(contexts)
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": combined_context
                }
            }
            print(json.dumps(response))
            return
        
        print(json.dumps({}))
    except Exception:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
