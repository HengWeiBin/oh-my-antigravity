import sys
import json
import os

def main():
    try:
        # Read JSON from stdin
        payload = json.load(sys.stdin)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})
        
        # Check if tool is write/edit
        if tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
            # Extract file path
            file_path = tool_input.get("TargetFile", "")
            if not file_path:
                file_path = tool_input.get("file_path", "")
            
            # If path is specified, check it
            if file_path:
                basename = os.path.basename(file_path)
                # Allow markdown plan/task files or files in scratch/ or .agents/
                is_plan = "plan" in basename.lower() or "task" in basename.lower() or file_path.endswith(".md")
                normalized_path = file_path.replace("\\", "/").lower()
                is_scratch = "scratch" in normalized_path or ".agents" in normalized_path
                
                if not (is_plan or is_scratch):
                    # Direct code write/edit detected! Warn/Ask
                    response = {
                        "permissionDecision": "ask",
                        "permissionDecisionReason": (
                            f"STOP. Lead Orchestrator agents do not edit source code directly (Path: {file_path}).\n"
                            "Implementing yourself is forbidden. You are paid to ORCHESTRATE, not implement.\n"
                            "If this is a tiny verification fix (<= 2 lines) on subagent output, you may proceed. "
                            "Otherwise, please delegate it via invoke_subagent."
                        )
                    }
                    print(json.dumps(response))
                    return
        
        # Default allow
        print(json.dumps({"permissionDecision": "allow"}))
    except Exception as e:
        # Fallback to allow if any error
        print(json.dumps({"permissionDecision": "allow"}))

if __name__ == "__main__":
    main()
