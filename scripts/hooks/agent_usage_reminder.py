from __future__ import annotations

import os
import sys

# Ensure the scripts directory is in sys.path if not already, to allow absolute imports like `from hooks.utils import is_subagent_session`
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.abspath(os.path.join(current_dir, ".."))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from hooks.utils import is_subagent_session

REMINDER_INTERVAL = 10  # Fire every N invocations
REMINDER_START = 5     # First fire at invocation N

def get_agent_usage_reminder_messages(payload: dict) -> list[dict]:
    """
    Periodically reminds the agent of important tool usage patterns.
    Only fires for non-subagent sessions at configured intervals.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    if is_subagent_session(payload):
        return []
    
    invocation_num = payload.get("invocationNum", 0)
    
    if not isinstance(invocation_num, int):
        try:
            invocation_num = int(invocation_num)
        except (ValueError, TypeError):
            invocation_num = 0

    if invocation_num >= REMINDER_START and (invocation_num - REMINDER_START) % REMINDER_INTERVAL == 0:
        reminder_content = f"""💡 AGENT USAGE REMINDER (Invocation #{invocation_num})

🔍 Codebase exploration: Use `codegraph_explore` for symbol lookups and architecture exploration
📤 Delegation: Use `invoke_subagent` to delegate implementation tasks to specialized workers
🎯 4-Phase Protocol after delegation: READ → RUN → QA → GATE (verify all subagent work)
🛠️ Skills: Activate skills with `/skill-name` (e.g. /programming, /frontend, /debugging)
📝 Notepads: Track state in `.omo/notepads/` files for cross-invocation memory
🚫 Never implement yourself: You are an orchestrator — delegate everything"""
        return [{"ephemeralMessage": reminder_content}]
    
    return []

run_agent_usage_reminder = get_agent_usage_reminder_messages
