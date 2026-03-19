---
description: "Create a new research session to track searches, sources, and questions"
argument-hint: "<topic>"
allowed-tools:
  - Bash
---

Create a new research session for the given topic.

## Step 1: Create session

```
python xLoop/scripts/session_manager.py create $ARGUMENTS
```

## Step 2: Present result

Show the created session ID and topic to the user.

Then ask: "이 세션으로 /research를 시작하시겠습니까?"
