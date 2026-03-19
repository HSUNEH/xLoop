---
description: "Phase 2: research.json → Double Diamond 전략 수립 → strategy.json 저장"
argument-hint: "<session_id>"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Phase 2 — Research 결과를 Double Diamond (Diverge → Converge) 패턴으로 실행 전략으로 변환한다.

## Step 0: 입력 검증

### 0a. Session ID 확인

인자에서 `<session_id>`를 추출한다. 없으면 사용자에게 요청:

> 세션 ID를 입력해주세요.

### 0b. Research 결과 로드

```
python xLoop/scripts/pipeline_schema.py load research <session_id>
```

**research.json이 없으면:**
> Phase 1 (Research)이 아직 완료되지 않았습니다.
> `/expert-loop`으로 먼저 리서치를 수행해주세요.

**research.json이 있으면 findings 확인:**
- findings가 비어있으면 경고 후 진행 여부 확인
- findings가 있으면 Step 1로 진행

### 0c. Pipeline Spec 로드 (선택)

```
python xLoop/scripts/pipeline_spec.py load <session_id>
```

spec.json이 있으면 constraints와 tools를 전략에 반영.
없으면 constraints 없이 진행.

---

## Step 1: 전략 생성 (Diverge → Converge)

```
python xLoop/scripts/strategy_engine.py generate <session_id>
```

결과를 파싱하여 사용자에게 보여준다:

> ## 전략 수립 결과
>
> **접근 방식:** Double Diamond
> **총 작업 수:** N개
> **적용된 제약:** [constraints]
>
> | # | 작업 | 도구 | 우선순위 |
> |---|------|------|---------|
> | 1 | 작업 제목 | dall-e | 🔴 high |
> | 2 | 작업 제목 | claude | 🟡 medium |
>
> 이 전략으로 진행할까요?
> 1. **승인** — 저장하고 Phase 3으로 진행
> 2. **수정** — 작업/우선순위 조정
> 3. **재생성** — 다시 전략 수립

---

## Step 2: 사용자 확인

사용자 응답에 따라:

**Option 1 — 승인:**
→ Step 3으로 진행

**Option 2 — 수정:**
> 어떤 작업을 수정할까요? (번호, 변경 내용)
수정 후 다시 Step 1의 테이블을 보여주고 재확인.

**Option 3 — 재생성:**
> 추가 제약 조건이 있나요? (없으면 Enter)
제약 조건을 반영하여 Step 1 반복.

---

## Step 3: 검증 + 저장

### 3a. 검증

생성된 strategy를 stdin으로 파이프하여 저장:
```
echo '<strategy_json>' | python xLoop/scripts/pipeline_schema.py save strategy <session_id>
```

### 3b. 검증 실행

```
python xLoop/scripts/pipeline_schema.py validate strategy <session_id>
```

검증 실패 시 → 에러 필드를 보여주고 수정 요청.

### 3c. 핸드오프 기록

```
echo '<handoff_json>' | python xLoop/scripts/pipeline_schema.py save handoff <session_id>
```

handoff 데이터:
```json
{
  "version": "1.0",
  "from_phase": 1,
  "to_phase": 2,
  "session_id": "<session_id>",
  "timestamp": "<now>",
  "status": "success",
  "output_file": "strategy.json",
  "summary": {
    "total_tasks": N,
    "approach": "Double Diamond"
  }
}
```

---

## Step 4: 완료 안내

> ## Phase 2 완료
>
> 📁 `data/pipelines/<session_id>/strategy.json`
>
> | 항목 | 값 |
> |------|-----|
> | **작업 수** | N개 |
> | **접근 방식** | Double Diamond |
> | **제약 조건** | [constraints] |
>
> 다음 단계: Phase 3 (Execution)을 시작하시겠습니까?

---

## Error handling

- research.json 없음 → `/expert-loop` 안내
- spec.json 없음 → constraints 없이 진행 (경고만 표시)
- findings 비어있음 → 경고 + 빈 전략 생성 가능
- 검증 실패 → 누락 필드 안내 + 수정 요청
- strategy 저장 실패 → 에러 메시지 + 재시도
