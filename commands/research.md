---
description: "Search multiple sources → select results → add to NotebookLM in one flow"
argument-hint: "<search_query> [--count N] [--months N] [--no-date-filter] [source-specific filters]"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Orchestrate the full research pipeline: multi-source search → user selects results → add to NotebookLM.

## Step -1: Session selection

Before anything else, ask the user:

> 세션을 어떻게 하시겠습니까?
> 1. **새 세션 시작** — 새 주제로 세션을 만들고 진행
> 2. **기존 세션 이어하기** — 이전 세션에 소스를 추가
> 3. **세션 없이 진행** — 기존처럼 일회성으로 진행

**Option 1 — 새 세션:**
```
python xLoop/scripts/session_manager.py create "<topic>"
```
Save the returned session ID for use in subsequent steps.

**Option 2 — 기존 세션:**
```
python xLoop/scripts/session_manager.py list --status active
```
Let the user pick a session. Load it:
```
python xLoop/scripts/session_manager.py show <session_id>
```
Use this session's `notebook_id` (if any) in Step 4.

**Option 3 — 세션 없이:** Skip all `session_manager.py` calls below and proceed as before.

## Step 0: Ask source selection

Before searching, ask the user which source(s) to search:

1. **YouTube** — videos (default)
2. **Web** — blogs, articles, docs
3. **arXiv** — academic papers
4. **Community** — Reddit & Hacker News discussions
5. **All** — search all sources

If the user doesn't specify, default to YouTube (existing behavior).

## Step 1: Search selected source(s)

Before running the search, inform the user of available filter options for the selected source(s):

| 소스 | 사용 가능한 필터 |
|------|-----------------|
| YouTube | `--min-views N` `--min-duration M` `--max-duration M` `--channel NAME` `--exclude-channel NAME` |
| Web | `--time d\|w\|m\|y` |
| arXiv | `--sort relevance\|lastUpdatedDate\|submittedDate` |
| Community | `--min-score N` `--time d\|w\|m\|y` `--subreddit NAME` |

Ask: "필터를 적용하시겠습니까? (예: `--min-views 10000 --max-duration 30`)" — 사용자가 필터를 지정하면 해당 옵션을 검색 스크립트 인자에 그대로 추가한다. 지정하지 않으면 기본값으로 진행한다.

Run the appropriate search script(s) based on the selected source:

**YouTube:**
```
python xLoop/scripts/yt_search.py $ARGUMENTS
```

**Web:**
```
python xLoop/scripts/web_search.py $ARGUMENTS
```

**arXiv:**
```
python xLoop/scripts/arxiv_search.py $ARGUMENTS
```

**Community:**
```
python xLoop/scripts/community_search.py all $ARGUMENTS
```

**All:** Run all four scripts above and combine results with unified numbering.

Present the numbered results to the user.

**Session tracking:** If a session is active, record each search:
```
python xLoop/scripts/session_manager.py add-search <session_id> --source <source> --query "<query>" --count <count> --results <results_count>
```

## Step 2: Ask user to select results

Ask the user:
- Which results to add to NotebookLM (e.g., "1, 3, 5" or "all")
- What notebook title to use

## Step 3: Get URLs via JSON mode

Run the search again with `--json` to extract URLs programmatically for the selected source(s).
Parse the JSON output and extract the URLs for the selected result numbers.

- For YouTube: use `url` field
- For Web: use `url` field
- For arXiv: use `pdf_url` field (better for NotebookLM)
- For Community: use `url` field

**Session tracking:** If a session is active, record each selected source:
```
python xLoop/scripts/session_manager.py add-source <session_id> --url "<url>" --title "<title>" --type <source_type>
```

## Step 4: Add to NotebookLM

Run notebooklm_add with the selected URLs:

```
python xLoop/scripts/notebooklm_add.py "<notebook_title>" <selected_urls>
```

Present the result to the user. Save the Notebook ID from the output for Step 5.

**Session tracking:** If a session is active, link the notebook:
```
python xLoop/scripts/session_manager.py set-notebook <session_id> <notebook_id>
```

## Step 5: Ask questions to the notebook

After sources are added, ask the user what they want to learn from the notebook.

For the first question:

```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "<question>"
```

Present the answer and references to the user.

For follow-up questions, use the `conversation_id` from the previous answer to maintain context:

```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "<follow-up>" --conversation-id <id>
```

**Session tracking:** If a session is active, record each question:
```
python xLoop/scripts/session_manager.py add-question <session_id> --question "<question>" --conversation-id "<conversation_id>"
```

Keep asking the user if they have more questions. When done, summarize the key findings.

## Error handling
- If any search script fails → explain the error and suggest fixes
- If notebooklm_add fails with "Not authenticated" → guide user to run `notebooklm login`
- If user selects invalid numbers → ask again with valid range
- If "All" mode and one source fails → continue with remaining sources (partial failure OK)
