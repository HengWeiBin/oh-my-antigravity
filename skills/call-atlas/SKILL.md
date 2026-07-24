---
name: call-atlas
description: "Call Atlas subagent directly to execute tasks. Trigger when the user mentions Atlas, asks to send a message to Atlas, or requests Atlas. Triggers: call-atlas, atlas, 呼叫 atlas, 傳送給 atlas, atlas subagent."
---

# Call Atlas

This skill automates the packaging of your message and forwards it directly to the Atlas subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user (ignoring the meta-command requesting the call).
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `atlas`
   - **Role**: `Atlas - Master Orchestrator`
   - **Prompt**:
     ```text
     [User's Message]

     不要執行任何 Subagent / User 未交代的任何操作。
     ```
3. Execute the `invoke_subagent` tool immediately.
4. Report back to the user that you have forwarded the request to Atlas.
