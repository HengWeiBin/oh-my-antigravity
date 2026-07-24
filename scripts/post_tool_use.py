import sys
import json

def main():
    try:
        # Read JSON from stdin
        payload = json.load(sys.stdin)
        tool_name = payload.get("tool_name")
        if not tool_name and "toolCall" in payload:
            tool_name = payload["toolCall"].get("name")
        
        # Check if subagent was invoked
        if tool_name == "invoke_subagent":
            # Inject verification reminder
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
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
                }
            }
            print(json.dumps(response))
            return
        
        print(json.dumps({}))
    except Exception as e:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
