---
description: "Ask a question to a NotebookLM notebook"
argument-hint: "<notebook_id> \"<question>\" [--conversation-id ID] [--json]"
allowed-tools:
  - Bash
---

Ask a question to a NotebookLM notebook and display the AI-generated answer.

Execute this command:

```
python xLoop/scripts/notebooklm_ask.py $ARGUMENTS
```

Present the answer directly to the user. Include the references section if present.

For follow-up questions, use the `conversation_id` from the previous response:

```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "<follow-up question>" --conversation-id <id>
```

## Error handling
- "Not authenticated" → guide the user to run `notebooklm login`
- "notebooklm-py not installed" → guide the user to run `pip install notebooklm-py[browser]`
- "Notebook not found" → ask the user to verify the notebook ID
- Timeout errors → suggest checking network connection and retrying
