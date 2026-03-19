---
description: "List all research sessions with status, source count, and last activity"
argument-hint: "[--status active|closed]"
allowed-tools:
  - Bash
---

List all research sessions in a table format.

## Step 1: List sessions

```
python xLoop/scripts/session_manager.py list $ARGUMENTS
```

## Step 2: Present result

Show the session table to the user. If no sessions exist, inform the user and suggest `/session-new <topic>` to create one.
