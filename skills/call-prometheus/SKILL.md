---
name: call-prometheus
description: "Call Prometheus subagent directly to execute tasks. Trigger when the user mentions Prometheus, asks to send a message to Prometheus, or requests Prometheus. Triggers: call-prometheus, prometheus, 呼叫 prometheus, 傳送給 prometheus, prometheus subagent."
---

# Call Prometheus

This skill automates the packaging of your message and forwards it directly to the Prometheus subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user.
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `prometheus`
   - **Role**: `Prometheus - Planner`
   - **Prompt**:
     ```text
     [User's Message]
     ```
3. Do NOT execute any other operations (such as file edits, command execution, or other tool calls) that are not explicitly specified by the Subagent or the User.
4. Execute the `invoke_subagent` tool immediately and report back.
