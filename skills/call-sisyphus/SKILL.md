---
name: call-sisyphus
description: "Call Sisyphus subagent directly to execute tasks. Trigger when the user mentions Sisyphus, asks to send a message to Sisyphus, or requests Sisyphus. Triggers: call-sisyphus, sisyphus, 呼叫 sisyphus, 傳送給 sisyphus, sisyphus subagent."
---

# Call Sisyphus

This skill automates the packaging of your message and forwards it directly to the Sisyphus subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user.
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `sisyphus`
   - **Role**: `Sisyphus - Lead Developer`
   - **Prompt**:
     ```text
     [User's Message]
     ```
3. Do NOT execute any other operations (such as file edits, command execution, or other tool calls) that are not explicitly specified by the Subagent or the User.
4. Execute the `invoke_subagent` tool immediately and report back.
