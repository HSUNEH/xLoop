<h1 align="center">xLoop</h1>

<p align="center">
  <strong>Excalibur — 리서치 통합 자기개선 에이전트 하네스</strong><br>
  Claude Code 기반 프로젝트 오케스트레이션
</p>

<p align="center">
  <img src="https://img.shields.io/badge/typescript-5.7+-blue?logo=typescript&logoColor=white" alt="TypeScript 5.7+">
  <img src="https://img.shields.io/badge/claude_code-harness-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/version-0.2.0-orange" alt="v0.2.0">
</p>

<p align="center">
  <img src="assets/banner.png" alt="xLoop Banner" width="720" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <strong>한국어</strong>
</p>

---

xLoop은 기획, 리서치, 구현, 자기개선을 하나의 명령으로 오케스트레이션하는 **에이전트 하네스**입니다.

## Excalibur — xLoop의 핵심

```
xloop excalibur "실시간 채팅 앱 만들기"
```

하나의 명령으로 프로젝트 전체를 오케스트레이션합니다:

```
Phase 0: Deep Interview (사용자와 함께 스펙 공동 작성, 한 번에 하나의 질문)
    │
    ▼
Big Loop × N 마일스톤:
    ├── Ralplan (4-에이전트 합의 + 통합 리서치 — 현재 마일스톤만)
    ├── Ralph  (PRD 기반 구현 루프 — 병렬 실행)
    └── Eval   (자동 검증 + 학습 → 다음 마일스톤)
```

### 핵심 메커니즘

- **Complexity Gate**: 2단계 양방향 라우팅 — 단순 작업은 오케스트레이션을 건너뜀
- **리서치 통합 기획**: 리서치가 기획 루프 안에서 수행됨 (별도 사전 단계 아님)
- **마일스톤 단위 실행**: 각 루프가 전체 프로젝트가 아닌 하나의 마일스톤만 기획하고 구현
- **자동 검증**: 매 구현 사이클 후 5개 메트릭 검사
- **Mode B/C**: 반자동(사용자 승인) 또는 완전 자동(임계값 기반) 업그레이드 결정
- **자기개선**: 체크섬 보호, 스냅샷 기반 업그레이드 사이클 (롤백 지원)
- **학습**: 각 마일스톤의 교훈이 다음 루프 기획에 반영

## 아키텍처

```
작업 진입 → Complexity Gate (hook 수준, 구조적)
    │
    ├── 점수 1 (단순)  → Executor 직접 실행 — 오버헤드 없음
    ├── 점수 2 (중간)  → Ralph만 — 기획 건너뜀
    └── 점수 3 (복잡)  → Ralplan + Ralph — 전체 프로세스
```

### 에이전트 (7개)

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| planner | Opus | 전략 기획, 리서치 필요사항 식별 |
| architect | Opus | 아키텍처 리뷰, 반론 검토 |
| critic | Opus | 품질 게이트, 원칙-옵션 일관성 |
| researcher | Sonnet | 다중 소스 조사 (웹, arxiv, 문서) |
| executor | Sonnet | 코드 구현 |
| verifier | Sonnet | 인수 기준 검증 |
| explorer | Haiku | 코드베이스 검색, 빠른 조회 |

### 스킬 (8개)

| 스킬 | 트리거 | 용도 |
|------|--------|------|
| excalibur | `"excalibur"` | 전체 프로젝트 오케스트레이션 |
| deep-interview | (excalibur 경유) | 프로젝트 스펙 공동 작성 |
| ralph | `"ralph"` | PRD 기반 구현 루프 |
| ralplan | `"ralplan"` | 4-에이전트 합의 기획 + 통합 리서치 |
| research | `"research"` | 다중 소스 조사 |
| setup | `"setup"` | 설치 마법사 |
| upgrade | `"upgrade"` | 자기개선 사이클 |
| rollback | `"rollback"` | 스냅샷 복원 |

## 설치

Claude Code에서 아래 명령어를 실행하세요:

```bash
# 1. xLoop 마켓플레이스 추가
/plugin marketplace add HSUNEH/xLoop

# 2. 플러그인 설치
/plugin install xloop@xloop
```

설치 시 수행되는 작업:
1. CLAUDE.md 설치 (에이전트 지시사항)
2. 테스트 모드 설정 (B: 반자동 / C: 완전 자동)
3. MCP 서버 등록 (state, notepad, PRD 도구)
4. NotebookLM 인증 설정
5. Complexity Gate 임계값 설정

## 사용법

### 전체 프로젝트 오케스트레이션

```bash
xloop excalibur "실시간 채팅 앱"
# → Deep Interview → (Ralplan + Ralph + Eval) × N 마일스톤 → 완료
```

### 개별 명령어

```bash
xloop ralph "인증 버그 수정"          # PRD 기반 구현 루프
xloop ralplan "캐싱 레이어 설계"      # 4-에이전트 합의 기획
xloop research "WebSocket vs SSE"     # 단독 리서치
xloop upgrade                         # 자기개선 사이클
xloop rollback                        # 스냅샷 복원
xloop status                          # 현재 상태 표시
```

### 키워드 (Claude Code에서 자연스럽게 사용)

```
"excalibur 채팅 앱 만들기"     → 전체 프로젝트 오케스트레이션
"ralph 이 버그 수정"           → 구현 루프
"ralplan 새 기능 설계"         → 합의 기획
```

## Complexity Gate

모든 작업은 오케스트레이션 전에 구조적으로 라우팅됩니다:

| 점수 | 라우트 | 조건 |
|------|--------|------|
| 1 (단순) | Executor 직접 | "오타 수정", "이름 변경", 단일 파일 |
| 2 (중간) | Ralph만 | 다중 파일 작업, 명확한 범위 |
| 3 (복잡) | Ralplan + Ralph | 아키텍처 결정, 모호한 범위 |

**2단계 게이트**: 구조적 휴리스틱(즉시, LLM 비용 0) → Haiku 마이크로 평가(불확실할 때만).

3차원 점수: 범위(40%) + 명확성(35%) + 결정(25%).

## Excalibur Big Loop

```
Big Loop #1 (M1: MVP)
  ├── Ralplan: M1 기능만 기획 (+ 필요시 리서치)
  ├── Ralph: M1 스토리 구현 (병렬 실행)
  └── Eval: 자동 검증 → 스펙 업데이트 → 학습 생성
        │
        Mode B: "M1 완료 (33%). 계속 / 스펙 수정 / 업그레이드?"
        Mode C: 10초 체크포인트 → 자동 진행

Big Loop #2 (M2 + M3 독립적이면 병렬)
  ├── Lane A: Ralplan(M2) → Ralph(M2)
  ├── Lane B: Ralplan(M3) → Ralph(M3)  [동시 실행]
  └── Eval: 둘 다 완료 → 프로젝트 완료
```

### 마일스톤 병렬화

독립적인 마일스톤(`depends_on` 충돌 없음)은 병렬 레인으로 실행됩니다. 충돌 감지 시 순차 실행으로 전환됩니다.

### 학습

각 루프는 `.xloop/learnings/loop-{N}.json`을 생성합니다:
- 기술 교훈 (어떤 라이브러리/패턴이 효과적이었는지)
- 프로세스 교훈 (스토리 순서, 병렬화)
- 품질 교훈 (놓친 메트릭)

다음 Ralplan은 이전 학습을 컨텍스트로 받습니다.

## 자기개선

```
Ralph 완료 → 자동 검증 (5개 메트릭) → 임계값 확인
    │
    Mode B: 사용자 결정 → 업그레이드 또는 수용
    Mode C: 메트릭 미달 시 자동 업그레이드 (최대 3사이클)
    │
    ▼
xloop upgrade:
  체크섬 검증 → 스냅샷 → Ralplan → Ralph → 리뷰 게이트 → 커밋
```

**안전장치**: PRINCIPLES.md SHA-256 체크섬, git pre-commit hook, 스냅샷/롤백, 멀티 모델 리뷰 게이트. 업그레이드는 xLoop 파일만 수정 — 호스트 프로젝트 코드는 절대 변경하지 않음.

## 프로젝트 구조

```
xloop/
├── agents/                  ← 7개 에이전트 정의 (md)
│   ├── planner.md          (Opus)
│   ├── architect.md        (Opus)
│   ├── critic.md           (Opus)
│   ├── researcher.md       (Sonnet)
│   ├── executor.md         (Sonnet)
│   ├── verifier.md         (Sonnet)
│   └── explorer.md         (Haiku)
├── skills/                  ← 8개 스킬 정의
│   ├── excalibur/SKILL.md  ← xLoop의 핵심
│   ├── deep-interview/SKILL.md
│   ├── ralph/SKILL.md
│   ├── ralplan/SKILL.md
│   ├── research/SKILL.md
│   ├── setup/SKILL.md + phases/
│   ├── upgrade/SKILL.md
│   └── rollback/SKILL.md
├── hooks/                   ← 8개 라이프사이클 Hook
│   ├── hooks.json
│   └── scripts/*.mjs
├── src/                     ← 핵심 TypeScript 모듈
│   ├── cli.ts              ← CLI 진입점
│   ├── mcp-server.ts       ← MCP 도구 서버 (7개 도구)
│   ├── state.ts            ← 세션 상태 관리
│   ├── gate.ts             ← Complexity Gate
│   ├── prd.ts              ← PRD 스캐폴드 생성기
│   ├── router.ts           ← PAL 모델 계층 라우팅
│   ├── checksum.ts         ← PRINCIPLES.md 무결성
│   ├── snapshot.ts         ← 업그레이드 전 스냅샷 + 롤백
│   ├── excalibur/          ← Excalibur 오케스트레이션 모듈
│   ├── interview.ts        ← Deep Interview 로직
│   ├── milestone.ts        ← 마일스톤 진행률 추적
│   └── llm-bridge.ts       ← LLM API 추상화
├── templates/CLAUDE.md      ← 프로젝트 템플릿
├── tests/                   ← 10개 파일 94개 테스트
├── package.json
└── tsconfig.json
```

## 설계 결정

xLoop은 세 시스템의 장점을 결합합니다:

| 출처 | xLoop이 취한 것 | xLoop이 버린 것 |
|------|----------------|----------------|
| **OMC** | 플러그인/스킬/Hook 아키텍처, Ralph PRD 루프, Ralplan 합의, MCP 통합 | 179K 컴파일 라인, 19개 에이전트, 과도한 Hook 주입 |
| **Ouroboros (razzant)** | 자기수정 개념, 헌법적 거버넌스, 멀티 모델 리뷰 | Colab 의존, 무제한 자기수정, 롤백 없음 |
| **Ouroboros (Q00)** | 모호성 스코어링 영감, 스펙 우선 접근 | 166개 Python 모듈, 빠른 경로 없음, 불변 스펙 |

### 핵심 차별점

- **Complexity Gate**: 양방향 라우팅 — OMC와 Ouroboros는 위로만 확장, xLoop은 아래로도 축소
- **리서치 통합 기획**: 별도 사전 단계가 아닌 기획 루프 안에서 리서치 수행
- **마일스톤 단위 실행**: 전체 프로젝트가 아닌 한 번에 하나의 청크만 기획
- **Excalibur**: 단일 명령으로 전체 프로젝트 라이프사이클 관리

## 개발

```bash
npm install
npm run typecheck           # tsc --noEmit
npm test                    # vitest run (94개 테스트)
npm run build               # tsc
```

## 라이선스

MIT
