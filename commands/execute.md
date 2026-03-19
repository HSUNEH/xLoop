---
description: "Phase 3: strategy.json 작업 실행 → execution.json 저장"
argument-hint: "<session_id>"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Phase 3 — Strategy의 작업 목록을 Tool Registry를 통해 순서대로 실행하고 결과를 저장한다.

## Step 0: 입력 검증

### 0a. Session ID 확인

인자에서 `<session_id>`를 추출한다. 없으면 사용자에게 요청:

> 세션 ID를 입력해주세요.

### 0b. Strategy 결과 로드

```
python xLoop/scripts/pipeline_schema.py load strategy <session_id>
```

**strategy.json이 없으면:**
> Phase 2 (Strategy)가 아직 완료되지 않았습니다.
> `/strategy-build`으로 먼저 전략을 수립해주세요.

**strategy.json이 있으면 tasks 확인:**
- tasks가 비어있으면 경고 후 진행 여부 확인
- tasks가 있으면 Step 1로 진행

### 0c. 등록된 도구 확인

```
python xLoop/scripts/execution_engine.py tools
```

사용 가능한 도구 목록을 보여준다.

---

## Step 1: 실행 계획 확인

tasks를 사용자에게 보여준다:

> ## 실행 계획
>
> **총 작업 수:** N개
>
> | # | 작업 | 도구 | 우선순위 |
> |---|------|------|---------|
> | 1 | 작업 제목 | dall-e | 🔴 high |
> | 2 | 작업 제목 | claude | 🟡 medium |
>
> 실행을 시작할까요?
> 1. **실행** — 모든 작업 실행
> 2. **취소** — 실행하지 않음

---

## Step 2: 실행

사용자가 승인하면:

```
python xLoop/scripts/execution_engine.py run <session_id>
```

결과 JSON을 파싱하여 진행 상황을 보여준다.

---

## Step 3: 검증 + 저장

### 3a. 검증 실행

```
python xLoop/scripts/pipeline_schema.py validate execution <session_id>
```

검증 실패 시 → 에러 필드를 보여주고 수정 요청.

### 3b. 핸드오프 기록

```
echo '<handoff_json>' | python xLoop/scripts/pipeline_schema.py save handoff <session_id>
```

handoff 데이터:
```json
{
  "version": "1.0",
  "from_phase": 2,
  "to_phase": 3,
  "session_id": "<session_id>",
  "timestamp": "<now>",
  "status": "success",
  "output_file": "execution.json",
  "summary": {
    "tasks_completed": N,
    "tasks_failed": M,
    "total_artifacts": K
  }
}
```

---

## Step 4: 완료 안내

> ## Phase 3 완료
>
> 📁 `data/pipelines/<session_id>/execution.json`
>
> | 항목 | 값 |
> |------|-----|
> | **완료** | N개 |
> | **실패** | M개 |
> | **산출물** | K개 |
>
> 다음 단계: Phase 4 (Evaluation)을 시작하시겠습니까?

---

## Error handling

- strategy.json 없음 → `/strategy-build` 안내
- tasks 비어있음 → 경고 + 빈 execution 생성 가능
- 도구를 찾을 수 없음 → 해당 task를 failed로 기록하고 계속
- 전체 실패 → 에러 요약 + 재시도 옵션
- 검증 실패 → 누락 필드 안내 + 수정 요청
