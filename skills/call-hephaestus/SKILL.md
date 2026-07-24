---
name: call-hephaestus
description: "Call Hephaestus subagent directly to execute tasks. Trigger when the user mentions Hephaestus, asks to send a message to Hephaestus, or requests Hephaestus. Triggers: call-hephaestus, hephaestus, 呼叫 hephaestus, 傳送給 hephaestus, hephaestus subagent."
---

# Call Hephaestus

This skill automates the packaging of your message and forwards it directly to the Hephaestus subagent.

## Instructions

When this skill is loaded, do the following:
1. Extract the core task or message provided by the user (ignoring the meta-command requesting the call).
2. Formulate a call to the `invoke_subagent` tool with the following configurations:
   - **TypeName**: `hephaestus`
   - **Role**: `Hephaestus - Deep Worker`
   - **Prompt**:
     ```text
     [User's Message]

     不要執行任何 Subagent / User 未交代的任何操作。
     ```
3. Execute the `invoke_subagent` tool immediately.
4. Report back to the user that you have forwarded the request to Hephaestus.
