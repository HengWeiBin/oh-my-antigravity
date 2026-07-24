---
name: call-prometheus
description: "Call Prometheus subagent directly to execute tasks. Trigger when the user mentions Prometheus, asks to send a message to Prometheus, or requests Prometheus. Triggers: call-prometheus, prometheus, 呼叫 prometheus, 傳送給 prometheus, prometheus subagent."
---

# Call Prometheus

This skill automates the packaging of your message and forwards it directly to the Prometheus subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user (ignoring the meta-command requesting the call).
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `prometheus`
   - **Role**: `Prometheus - Planner`
   - **Prompt**:
     ```text
     [User's Message]

     不要執行任何 Subagent / User 未交代的任何操作。
     ```
3. Execute the `invoke_subagent` tool immediately.
4. Report back to the user that you have forwarded the request to Prometheus.
