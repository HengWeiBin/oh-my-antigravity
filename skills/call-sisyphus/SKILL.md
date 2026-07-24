---
name: call-sisyphus
description: "Call Sisyphus subagent directly to execute tasks. Trigger when the user mentions Sisyphus, asks to send a message to Sisyphus, or requests Sisyphus. Triggers: call-sisyphus, sisyphus, 呼叫 sisyphus, 傳送給 sisyphus, sisyphus subagent."
---

# Call Sisyphus

This skill automates the packaging of your message and forwards it directly to the Sisyphus subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user (ignoring the meta-command requesting the call).
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `sisyphus`
   - **Role**: `Sisyphus - Lead Developer`
   - **Prompt**:
     ```text
     [User's Message]

     不要執行任何 Subagent / User 未交代的任何操作。
     ```
3. Execute the `invoke_subagent` tool immediately.
4. Report back to the user that you have forwarded the request to Sisyphus.
