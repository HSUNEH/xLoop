---
description: "Phase 4: execution.json 검증 → validation.json 저장 (3단계: 기계적→의미적→합의)"
argument-hint: "<session_id>"
allowed-tools:
  - Bash
  - AskUserQuestion
---

Phase 4 — Execution 결과를 Spec과 비교하여 3단계 검증을 수행하고 드리프트를 측정한다.

## Step 0: 입력 검증

### 0a. Session ID 확인

인자에서 `<session_id>`를 추출한다. 없으면 사용자에게 요청:

> 세션 ID를 입력해주세요.

### 0b. Spec 결과 로드

```
python xLoop/scripts/pipeline_spec.py load <session_id>
```

**spec.json이 없으면:**
> Phase 0 (Big Bang)이 아직 완료되지 않았습니다.
> `/big-bang`으로 먼저 스펙을 정의해주세요.

### 0c. Execution 결과 로드

```
python xLoop/scripts/pipeline_schema.py load execution <session_id>
```

**execution.json이 없으면:**
> Phase 3 (Execution)이 아직 완료되지 않았습니다.
> `/execute`로 먼저 작업을 실행해주세요.

**execution.json이 있으면 요약 표시:**

> ## 검증 대상
>
> | 항목 | 값 |
> |------|-----|
> | **Session** | session_id |
> | **완료 작업** | N개 |
> | **실패 작업** | M개 |
> | **산출물** | K개 |
>
> 3단계 검증을 시작할까요?
> 1. **전체 검증** — Stage 1~3 모두 실행
> 2. **기계적 검증만** — Stage 1만 실행
> 3. **취소**

---

## Step 1: 검증 실행

사용자 선택에 따라:

### 전체 검증

```
python xLoop/scripts/evaluation_engine.py full <session_id>
```

### Stage 0만 (런타임 검증)

```
python xLoop/scripts/evaluation_engine.py stage0 <session_id>
```

### Stage 1만

```
python xLoop/scripts/evaluation_engine.py stage1 <session_id>
```

결과 JSON을 파싱하여 진행 상황을 보여준다.

### Stage 0: 런타임 검증 (Runtime Verification)

Stage 1 실행 전에 자동 수행되는 런타임 검증 단계.

- `execution.json`의 `smoke_test` 결과를 확인
- `smoke_test`가 없으면 Stage 0 FAIL (런타임 테스트 미실행)
- `start_command` 미설정으로 스킵된 경우는 PASS (서버 없는 프로젝트)
- 각 엔드포인트 결과를 checks[]로 변환

**Drift Score에 미치는 영향:**
- Stage 0 전체 실패: drift += 0.5 (치명적)
- Stage 0 부분 실패: drift += (실패 비율 x 0.3)
- Stage 0 FAIL 시 drift_checker가 drift score와 무관하게 backtrack 강제

---

## Step 2: 결과 표시

```
python xLoop/scripts/evaluation_engine.py show <session_id>
```

검증 결과를 사용자에게 표시:

> ## Phase 4 검증 결과
>
> | 항목 | 결과 |
> |------|------|
> | **Stage 0 (런타임)** | PASS/FAIL |
> | **Stage 1 (기계적)** | PASS/FAIL |
> | **Stage 2 (의미적)** | PASS/FAIL (정합성 N%) |
> | **Stage 3 (합의)** | PASS/FAIL |
> | **Drift Score** | 0.XX |
> | **판정** | pass / restart |

---

## Step 3: 핸드오프 기록

```
echo '<handoff_json>' | python xLoop/scripts/pipeline_schema.py save handoff <session_id>
```

handoff 데이터:
```json
{
  "version": "1.0",
  "from_phase": 3,
  "to_phase": 4,
  "session_id": "<session_id>",
  "timestamp": "<now>",
  "status": "success",
  "output_file": "validation.json",
  "summary": {
    "passed": true,
    "drift_score": 0.XX,
    "action": "pass"
  }
}
```

---

## Step 4: 완료 안내

### drift <= 0.3 (통과)

> ## Phase 4 완료 — 통과
>
> Drift Score: 0.XX (임계값 0.3 이하)
>
> 다음 단계: Phase 5 (Drift Check)로 진행하시겠습니까?

### drift > 0.3 (재검토)

> ## Phase 4 완료 — 재검토 필요
>
> Drift Score: 0.XX (임계값 0.3 초과)
>
> **피드백:**
> - [Stage1] ...
> - [Stage2] ...
>
> 옵션:
> 1. **Phase 0 복귀** — spec을 재정의합니다
> 2. **Phase 2 백트래킹** — 전략을 재수립합니다
> 3. **무시하고 진행** — drift를 수용합니다

---

## Error handling

- spec.json 없음 → `/big-bang` 안내
- execution.json 없음 → `/execute` 안내
- 검증 스키마 오류 → 누락 필드 안내
- Stage 실행 오류 → 해당 Stage 에러 표시 + 재시도 옵션
