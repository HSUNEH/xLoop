---
description: "Deep research loop: search → analyze → find gaps → re-search until coverage is sufficient"
argument-hint: "<topic> [--max-iterations N]"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Orchestrate a deep research loop: multi-source search → NotebookLM analysis → gap detection (grill-me style) → gap-based source matching → re-search → repeat until coverage is sufficient. Then generate a structured report and action items.

## Step 0: Session + Loop initialization

### 0a. Create or resume a session

Ask the user:

> 세션을 어떻게 하시겠습니까?
> 1. **새 세션 시작** — 새 주제로 세션을 만들고 진행
> 2. **기존 세션 이어하기** — 이전 세션에 소스를 추가

**Option 1 — 새 세션:**
```
python xLoop/scripts/session_manager.py create "<topic>"
```

**Option 2 — 기존 세션:**
```
python xLoop/scripts/session_manager.py list --status active
```
Let the user pick. Load it:
```
python xLoop/scripts/session_manager.py show <session_id>
```

### 0b. Initialize the loop

Parse `--max-iterations` from the user's arguments (default: 3).

```
python xLoop/scripts/loop_engine.py start <session_id> "<initial_query>" --max-iterations <N>
```

Confirm to the user:
> 루프를 시작합니다. 최대 **N회** 반복하며, 갭이 없으면 조기 종료합니다.

---

## ┌─── 루프 시작 ───────────────────────────────────┐

## Step 1: Search + source collection (루프 내)

검색과 소스 수집은 **매 반복** 루프 안에서 수행한다.

### 1a. Source selection

**첫 반복 (iteration 1):**
- 사용자에게 소스를 선택하게 하거나, "All"로 넓게 시작:

> 어떤 소스에서 검색할까요?
> 1. **YouTube** — 영상
> 2. **Web** — 블로그, 기사, 공식 문서
> 3. **arXiv** — 학술 논문
> 4. **Community** — Reddit & Hacker News
> 5. **All** — 전체 소스 검색

**2회차 이후 (iteration 2+):**
- Step 3에서 생성된 **갭→소스 매칭 테이블**을 사용한다.
- 매칭된 소스와 쿼리를 사용자에게 보여주고 확인받는다.

### 1b. Search

선택된 소스에 대해 검색 실행:

```
python xLoop/scripts/yt_search.py "<query>" --count 5
python xLoop/scripts/web_search.py "<query>" --count 5
python xLoop/scripts/arxiv_search.py "<query>" --count 5
python xLoop/scripts/community_search.py all "<query>" --count 5
```

Record each search:
```
python xLoop/scripts/session_manager.py add-search <session_id> --source <source> --query "<query>" --count <count> --results <results_count>
```

### 1c. User selects results

Present numbered results. Ask user which to add (e.g., "1, 3, 5" or "all").

### 1d. Add to NotebookLM

Re-run search with `--json` to extract URLs, then:
```
python xLoop/scripts/notebooklm_add.py "<topic>" <selected_urls>
```

**첫 반복 시:** 새 노트북이 생성되므로 notebook_id를 기록:
```
python xLoop/scripts/session_manager.py add-source <session_id> --url "<url>" --title "<title>" --type <source_type>
python xLoop/scripts/session_manager.py set-notebook <session_id> <notebook_id>
```

**2회차 이후:** 기존 노트북에 추가:
```
python xLoop/scripts/notebooklm_add.py --notebook-id <notebook_id> <new_urls>
python xLoop/scripts/session_manager.py add-source <session_id> --url "<url>" --title "<title>" --type <source_type>
```

## Step 2: Analysis questions

Ask NotebookLM a comprehensive analysis question about the topic:

```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "지금까지 추가된 모든 자료를 기반으로 <topic>에 대해 다음을 분석해줘: 1) 핵심 개념과 정의 2) 주요 접근 방법/프레임워크 3) 장단점과 트레이드오프 4) 실무 적용 사례 5) 아직 다루지 못한 영역이 있다면 무엇인지" --json
```

Record the question:
```
python xLoop/scripts/session_manager.py add-question <session_id> --question "<question>" --conversation-id "<conversation_id>"
```

Save the answer for gap analysis in Step 3.

## Step 3: Gap analysis + iteration recording + gap→source matching

This is the core differentiator. Explore the topic's decision tree to find blind spots, then match each gap to the optimal source.

### 3a. Build the decision tree

From the Step 2 answer, construct the topic's key axes:

| Axis | Examples |
|------|----------|
| Theory vs Practice | 이론적 근거 vs 실제 적용 사례 |
| Pros vs Cons | 옹호 관점 vs 비판 관점 |
| Historical vs Current | 역사적 발전 vs 최신 트렌드 |
| Basics vs Advanced | 기초 개념 vs 심화/엣지 케이스 |

For each axis, assess:
- **Covered**: what the current sources already address
- **Gap**: what the current sources do NOT address

### 3b. Grill the gaps

For each identified gap (max 2 per axis to avoid slowdown):

Ask NotebookLM a targeted question:
```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "현재 자료들에서 <gap_area>에 대한 내용이 있는가? 있다면 요약하고, 없다면 '자료에서 다루지 않음'이라고 답해줘" --conversation-id <id> --json
```

If the answer confirms "자료에서 다루지 않음" → this is a confirmed gap.
If the answer provides content → the gap was perceived, not real. Remove it.

### 3c. Gap→source matching

각 확인된 갭에 대해 유형을 판단하고 최적 소스를 매칭한다:

| 갭 유형 | 매칭 소스 | 매칭 근거 |
|---------|----------|----------|
| 이론/학술/증명 | arXiv | 논문이 가장 정확 |
| 실전/구현/튜토리얼 | YouTube | 시각적 설명, 코드 워크스루 |
| 비교/의견/경험 | Community (Reddit/HN) | 현업 개발자 토론 |
| 최신 동향/문서/공식 | Web | 블로그, 공식 문서 |
| 불확실 | All | 넓게 검색 후 좁히기 |

### 3d. Generate new search queries

From confirmed gaps, generate new search queries:
- Each gap → 1~2 search queries
- Filter through loop_engine to remove duplicates:

```
python xLoop/scripts/loop_engine.py filter-queries <session_id> --candidates-json '<["query1", "query2", ...]>'
```

### 3e. Present gaps with recommended sources + record iteration

사용자에게 갭 분석 결과와 추천 소스를 보여준다:

> **발견된 갭:**
> 1. 수학적 근거 부족 → 📄 arXiv: "attention mechanism proof"
> 2. 실무 사례 부족 → 🎬 YouTube: "agent production deployment"
> 3. 커뮤니티 평가 없음 → 💬 Community: "framework X real experience"
>
> 이대로 검색할까요? (소스/쿼리 수정 가능)

Wait for user confirmation before proceeding.

Record the iteration (**매 반복** 기록, 첫 반복 포함):
```
python xLoop/scripts/loop_engine.py add-iteration <session_id> \
  --queries-json '<["q1", "q2"]>' \
  --sources-added <N> \
  --findings-json '<["finding1", "finding2"]>' \
  --gaps-json '<["gap1", "gap2"]>'
```

## Step 4: Termination check

```
python xLoop/scripts/loop_engine.py check <session_id>
```

- **Should terminate = Yes** → proceed to **Step 5** (최종 분석)
- **Should terminate = No** → proceed to **Step 1** (다음 반복, 갭→소스 매칭 사용)

Tell the user the result:
> **종료 판단:** [계속/종료] — [이유]

## └─── 루프 종료 ───────────────────────────────────┘

## Step 5: Loop end + final analysis

```
python xLoop/scripts/loop_engine.py end <session_id>
```

Ask NotebookLM a final synthesis question:
```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "지금까지 추가된 모든 자료를 종합하여 <topic>에 대한 최종 분석을 해줘. 1) 가장 중요한 핵심 발견 3가지 2) 주요 관점 간의 차이와 합의점 3) 실무에서 바로 적용할 수 있는 것 4) 추가 조사가 필요한 미해결 질문" --json
```

Present a loop summary to the user:
```
python xLoop/scripts/loop_engine.py status <session_id> --json
```

> **루프 완료 요약:**
> - 총 반복: N회
> - 총 소스: N개
> - 총 쿼리: N개
> - 커버한 주제: [topics]

Ask the user:
> 리서치 보고서를 생성할까요? (Step 6으로 진행)

## Step 6: Research report — write-a-prd style

Generate a structured research report from all loop data.

### 6a. Collect loop data

```
python xLoop/scripts/loop_engine.py status <session_id> --json
python xLoop/scripts/session_manager.py show <session_id> --json
```

Extract: all iterations' findings, gaps, covered_topics, sources, queries.

### 6b. Final synthesis from NotebookLM

```
python xLoop/scripts/notebooklm_ask.py <notebook_id> "지금까지의 모든 자료를 기반으로 <topic>에 대한 종합 보고서를 작성해줘. 구조: 1) 핵심 발견 2) 주요 관점/논쟁 3) 실무 적용 방법 4) 한계/미해결 질문" --json
```

### 6c. Generate report file

Create the report at `xLoop/data/sessions/<session_id>/research-report.md`:

```markdown
# Research Report: <topic>

**Session:** <session_id>
**Date:** <date>
**Loop iterations:** <N>
**Total sources:** <N>

## Executive Summary

<1-paragraph summary>

## Key Findings

<Numbered list from loop findings + NotebookLM synthesis>

## Perspectives & Debates

<Different viewpoints identified across sources>

## Practical Applications

<Actionable insights for real-world use>

## Limitations & Open Questions

<What remains unanswered, areas needing further research>

## Sources

<Numbered list of all sources with URLs>

## Loop History

| Iteration | Queries | Sources Added | Key Findings | Gaps |
|-----------|---------|---------------|--------------|------|
| 1 | ... | N | ... | ... |
```

Present a summary to the user and ask:
> 보고서가 생성되었습니다. 작업 카드를 도출할까요? (Step 7로 진행)

## Step 7: Action cards — prd-to-issues style

Extract follow-up tasks from the report as vertical-slice work items.

### 7a. Extract tasks

From the report's "Practical Applications" + "Open Questions" sections, identify actionable items. Each task should be:
- **Independent**: can be worked on without other tasks
- **Vertical slice**: delivers value end-to-end
- **Concrete**: has clear done criteria

### 7b. Present cards

> **도출된 작업 카드:**
>
> 1. **[Task title]**
>    - 설명: [description]
>    - 선행 조건: [prerequisites or "없음"]
>    - 예상 규모: [small/medium/large]
>
> 2. **[Task title]**
>    - ...
>
> GitHub 이슈로 생성할 카드를 선택해주세요 (예: "1, 3" 또는 "all")

### 7c. Create GitHub issues

For each selected card:
```
gh issue create --title "<task_title>" --body "$(cat <<'EOF'
## Context

From research on: <topic>
Session: <session_id>
Report: xLoop/data/sessions/<session_id>/research-report.md

## Description

<task_description>

## Prerequisites

<prerequisites>

## Acceptance Criteria

- [ ] <criteria_1>
- [ ] <criteria_2>

---
Generated by /expert-loop
EOF
)"
```

If `gh` CLI is not available, output the issue content as Markdown instead:
> `gh` CLI가 설치되어 있지 않습니다. 아래 내용을 수동으로 이슈에 복사해주세요:

## Error handling

- Search script 실패 → 에러 설명 + 대안 소스 제안
- NotebookLM 인증 실패 → `notebooklm login` 안내
- NotebookLM 소스 추가 한도 초과 → 기존 소스로 분석 계속 진행
- 사용자가 잘못된 번호 선택 → 유효 범위 안내 후 재요청
- 부분 실패 (여러 소스 중 하나 실패) → 나머지로 계속 진행
