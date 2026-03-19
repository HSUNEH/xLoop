---
description: "Resume an existing research session — view details and continue work"
argument-hint: "<session_id>"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Resume a research session by showing its current state and offering next steps.

## Step 1: Show session details

```
python xLoop/scripts/session_manager.py show $ARGUMENTS
```

## Step 2: Present summary and offer next steps

Show the session summary to the user, then:

- If the session has a `notebook_id` → ask: "이 노트북에 소스를 추가하거나 질문을 계속하시겠습니까?"
- If the session has no `notebook_id` → ask: "검색을 시작하시겠습니까? (/research로 진행)"

## Error handling
- If session not found → show error and suggest `/session-list` to see available sessions
