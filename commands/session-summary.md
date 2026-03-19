---
description: "Generate a markdown summary of a research session"
argument-hint: "<session_id>"
allowed-tools:
  - Bash
---

Generate a comprehensive summary of a research session.

## Step 1: Load session data

```
python xLoop/scripts/session_manager.py show $ARGUMENTS --json
```

## Step 2: Generate summary

Using the JSON data, generate a markdown summary including:

1. **주제 및 기간** — topic, created_at ~ updated_at, status
2. **수행한 검색** — list each search with source type, query, and results count
3. **추가한 소스** — list each source with title, type, and URL
4. **질문/답변 이력** — list each question asked
5. **NotebookLM 링크** — notebook_url if available

Present the summary in a clean markdown format to the user.

## Error handling
- If session not found → show error and suggest `/session-list`
- If session JSON is corrupted → show the error message from session_manager.py
