---
description: "Phase 0: 모호한 요구를 Pipeline Spec (실행 가능한 JSON)으로 결정화"
argument-hint: "<topic> [--config spec_template.yaml]"
allowed-tools:
  - Bash
  - AskUserQuestion
  - WebSearch
---

Phase 0 — 사용자의 모호한 요구를 대화를 통해 Pipeline Spec으로 구체화한다.
Ouroboros Ambiguity Gate + Grill-me 패턴 적용.

## Step 0: 세션 생성 + 빈 spec 초기화

### 0a. 모드 판별

인자에 `--config`가 있으면 **템플릿 모드**, 없으면 **대화형 모드**.

### 0b. 템플릿 모드 (`--config`)

```
# YAML 파일을 읽어서 spec으로 변환
cat <config_path>
```

YAML을 파싱하여 Pipeline Spec으로 변환한 후, 검증:
```
python xLoop/scripts/pipeline_spec.py create > /tmp/spec.json
# (YAML 내용을 spec에 병합)
```

검증 통과 시 → **Step 5**로 바로 이동.
검증 실패 시 → 부족한 부분만 대화형으로 보충 (Step 1~4 선택적 진행).

### 0c. 대화형 모드

```
python xLoop/scripts/session_manager.py create "<topic>" --type pipeline
```

세션 ID를 기록한 후, Goal Loop 시작:
```
python xLoop/scripts/goal_engine.py start <session_id>
```

빈 spec 생성:
```
python xLoop/scripts/pipeline_spec.py create
```

사용자에게 안내:
> Pipeline Spec을 함께 만들어 보겠습니다.
> 몇 가지 질문을 드리고, 답변을 바탕으로 실행 계획을 구체화합니다.
> 모호성 점수가 0.2 이하가 되면 자동으로 완료됩니다.

---

## Step 1: 목표(goal) 질문 블록

사용자에게 다음을 물어본다 (한 번에 하나씩, 자연스러운 대화로):

**1a. 산출물 (deliverables)**
> 최종적으로 무엇을 만들고 싶으신가요?
> (예: "유튜브 썸네일 3개", "리서치 보고서", "영상 스크립트 5편")

답변을 `spec.goal.deliverables`에 기록.

**1b. 성공 기준 (success_criteria)**
> 결과물이 성공적이라고 판단하는 기준은 무엇인가요?
> **정량 기준을 최소 1개 포함**해주세요.
> (예: "파일 3개, 1280x720", "5000자 이상", "유사도 70% 이상")

답변을 `spec.goal.success_criteria`에 기록.

**정량 기준 강제 (C 전략):**
- 정성 기준만 있으면 추가 질문:
  > 측정 가능한 정량 기준을 하나 추가해주세요.
  > 예: 파일 개수, 해상도, 글자 수, 시간 제한 등
- "피식대학 느낌" 같은 모호한 기준 → 정량화 유도:
  > "피식대학 느낌"을 구체화할 수 있을까요?
  > 예: "피식대학 레이아웃 참고" (정성) + "텍스트 3단어 이하" (정량)

**1c. 마감 (deadline) — 선택**
> 마감 기한이 있나요? (없으면 "없음")

**1d. 비용 한도 (cost_limit) — 선택**
> 비용 제한이 있나요? (예: API 비용 $10 이하, 없음)

---

## Step 2: 도메인(domain) 질문 블록

**2a. 대상 (target)**
> 구체적인 대상/타겟은 무엇인가요?
> (예: "youtube.com/c/MrBeast", "AI agent 프레임워크", "한국 시장")

답변이 모호하면 **자동 리서치**로 구체화:
```
python xLoop/scripts/web_search.py "<모호한 답변>" --count 3 --json
```
검색 결과를 보여주며:
> 이 중 해당하는 것이 있나요? 아니면 더 구체적으로 설명해주세요.

**2b. 제약 조건 (constraints)**
> 지켜야 할 제약 조건이 있나요?
> (예: 한국어만, 특정 포맷, 저작권 제한, 기술 스택)

**2c. 참고 자료 (references)**
> 참고할 레퍼런스가 있나요?
> (예: 경쟁사 URL, 스타일 가이드, 기존 작업물)

---

## Step 3: 파이프라인(pipeline) 질문 블록

**3a. 활성 Phase (active_phases)**
> 어떤 Phase를 실행할까요? (기본: 전체)
> - Phase 1: 리서치 (소스 검색 + 분석)
> - Phase 2: 전략 수립
> - Phase 3: 실행 (산출물 생성)
> - Phase 4: 평가 (드리프트 체크)
> - Phase 5: 드리프트 검사
>
> 전체 실행하려면 "전체", 특정 Phase만 선택하려면 번호를 알려주세요.

**3b. 도구/소스 (tools)**
> 사용할 도구/소스는? (복수 선택 가능)
> 1. YouTube  2. Web  3. arXiv  4. Community  5. NotebookLM  6. 전체

**3c. 모델 티어 (model_tiers) — 선택**
> Phase별 모델 설정이 필요하면 알려주세요. (기본: 자동)

---

## Step 4: 모호성 체크 → 추가 질문 or 확정

각 질문 블록 후, 현재 spec의 모호성을 체크:

```
python xLoop/scripts/pipeline_spec.py validate <session_id>
```

**모호성 > 0.2:**
```
python xLoop/scripts/goal_engine.py check <session_id>
```
미충족 필드에 대해 추가 질문 생성:
```
# get_next_questions()의 결과를 사용하여 추가 질문
```

반복 기록:
```
python xLoop/scripts/goal_engine.py add-iteration <session_id> \
  --questions-json '<[...]>' \
  --responses-json '<[...]>' \
  --spec-updates-json '<{...}>' \
  --ambiguity <score>
```

사용자에게 결과 보고:
> **모호성 점수:** 0.45 (기준: ≤ 0.2)
> 아직 구체화가 필요합니다. 추가 질문을 드리겠습니다.

추가 질문 후 다시 모호성 체크 → 0.2 이하가 될 때까지 반복.

**모호성 ≤ 0.2:**
> **모호성 점수:** 0.15 ✓
> 모든 필수 필드가 충족되었습니다. spec을 확정합니다.

**Step 5**로 진행.

---

## Step 5: spec.json 저장 + 요약 출력

spec을 저장:
```
echo '<spec_json>' | python xLoop/scripts/pipeline_spec.py save <session_id>
```

Goal Loop 종료:
```
python xLoop/scripts/goal_engine.py end <session_id>
```

최종 요약을 사용자에게 보여준다:

> ## Pipeline Spec 확정
>
> | 항목 | 값 |
> |------|-----|
> | **산출물** | 썸네일 3개 |
> | **성공 기준** | 파일 3개, 1280x720, 텍스트 3단어 이하 |
> | **대상** | youtube.com/c/MrBeast |
> | **제약** | 한국어, Canva 포맷 |
> | **참고** | 피식대학 레이아웃 |
> | **도구** | YouTube, Web |
> | **모호성** | 0.10 ✓ |
>
> 📁 `data/pipelines/<session_id>/spec.json`
>
> `/expert-loop`으로 리서치를 시작하시겠습니까?

---

## Error handling

- 검색 실패 → 사용자에게 직접 입력 요청
- spec 저장 실패 → 에러 메시지 + 재시도
- 모호성 점수가 5회 반복 후에도 0.2 이하 안 됨 → 강제 확정 제안:
  > 5회 반복했지만 모호성이 여전히 높습니다.
  > 현재 상태로 확정할까요, 아니면 계속 구체화할까요?
