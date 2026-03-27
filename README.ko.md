<h1 align="center">xLoop</h1>

<p align="center">
  <strong>Excalibur — 리서치 통합 자기개선 에이전트 하네스</strong><br>
  Claude Code 기반 프로젝트 오케스트레이션
</p>

<p align="center">
  <img src="https://img.shields.io/badge/claude_code-plugin-blueviolet" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/version-0.3.0-orange" alt="v0.3.0">
</p>

<p align="center">
  <img src="assets/banner.png" alt="xLoop Banner" width="720" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <strong>한국어</strong>
</p>

---

xLoop은 기획, 리서치, 구현, 자기개선을 하나의 키워드로 오케스트레이션하는 **Claude Code 플러그인**입니다.

## 빠른 시작

### 1. 설치

Claude Code에서 실행:

```
/plugin marketplace add HSUNEH/xLoop
/plugin install xloop@xloop
```

플러그인에는 선택적 **HUD (상태 표시줄)**가 포함되어 있습니다: 폴더, git 브랜치, 컨텍스트 사용량, 도구/에이전트/스킬 호출 수, 활성 플랜명, 5시간 rate limit을 표시합니다. HUD는 StatusLine 훅을 지원하는 환경(예: [oh-my-claudecode](https://github.com/anthropics/oh-my-claudecode))이 필요합니다. `hooks/scripts/xloop-hud.mjs` 참조.

### 2. 사용

Claude Code에서 키워드를 자연스럽게 입력하세요:

```
excalibur "실시간 채팅 앱 만들기"
```

끝입니다. xLoop이 나머지를 처리합니다:

```
Deep Interview → (Ralplan + Ralph + Eval) × N 마일스톤 → 완료
```

## 키워드

### 코어 — Excalibur 오케스트레이션

| 키워드 | 기능 |
|--------|------|
| `excalibur "..."` | 전체 프로젝트 오케스트레이션 (오피스아워 → 인터뷰 → 기획 → 구현 → 검증) |
| `ralph "..."` | PRD 기반 구현 루프 (TDD, 코드 리뷰, 보안 감사) |
| `ralplan "..."` | 6-에이전트 합의 기획 (디자인 리뷰, 크로스모델 리뷰, 아이디어 발굴) |
| `deep-interview "..."` | 소크라틱 스펙 공동 작성 (excalibur 내부 또는 단독 사용) |
| `research "..."` | 다중 소스 조사 (웹, arxiv, 문서, NotebookLM) |
| `upgrade` | 자기개선 사이클 (체크섬 → 스냅샷 → 구현 → 리뷰 → 커밋) |
| `rollback` | 스냅샷 복원 |

### 유틸리티 — 독립 도구

| 키워드 | 기능 |
|--------|------|
| `opportunity-scout "..."` | 트렌드 기반 기회 탐색 (Google Trends + GitHub + YouTube + 마케팅 프레임워크) |
| `youtube-transcript <URL>` | YouTube 영상 자막 추출 (다국어, 수동+자동생성 2-pass) |
| `setup` | 설치 마법사 (CLAUDE.md, MCP 서버, 설정) |

---

## 동작 원리

### Complexity Gate

모든 작업은 오케스트레이션 전에 자동으로 라우팅됩니다:

| 점수 | 라우트 | 예시 |
|------|--------|------|
| 1 (단순) | Executor 직접 | "오타 수정", "이름 변경" |
| 2 (중간) | Ralph만 | 다중 파일 작업, 명확한 범위 |
| 3 (복잡) | Ralplan + Ralph | 아키텍처 결정, 모호한 범위 |

2단계 게이트: 구조적 휴리스틱(즉시, LLM 비용 0) → Haiku 마이크로 평가(불확실할 때만).

3차원 점수: 범위(40%) + 명확성(35%) + 결정(25%).

### Excalibur Big Loop

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

독립적인 마일스톤은 병렬 레인으로 실행됩니다. 충돌 감지 시 순차 실행으로 전환됩니다.

각 루프는 `.xloop/learnings/loop-{N}.json`(기술, 프로세스, 품질 교훈)을 생성하여 다음 루프에 반영합니다.

### 자기개선

```
Ralph 완료 → 자동 검증 (5개 메트릭) → 임계값 확인
    │
    Mode B: 사용자 결정 → 업그레이드 또는 수용
    Mode C: 메트릭 미달 시 자동 업그레이드 (최대 3사이클)
    │
    ▼
upgrade:
  체크섬 검증 → 스냅샷 → Ralplan → Ralph → 리뷰 게이트 → 커밋
```

**안전장치**: SHA-256 체크섬, git pre-commit hook, 스냅샷/롤백, 멀티 모델 리뷰 게이트. 업그레이드는 xLoop 파일만 수정 — 프로젝트 코드는 절대 변경하지 않음.

## 에이전트 & 스킬

### 에이전트 (8개)

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| planner | Opus | 전략 기획, 리서치 필요사항 식별 |
| architect | Opus | 아키텍처 리뷰, 반론 검토 |
| critic | Opus | 품질 게이트, 원칙-옵션 일관성 |
| researcher | Sonnet | 다중 소스 조사 |
| executor | Sonnet | 코드 구현 |
| verifier | Sonnet | 인수 기준 검증 |
| designer | Sonnet | UX/UI 디자인 리뷰, 컴포넌트 설계 |
| explorer | Haiku | 코드베이스 검색, 빠른 조회 |

### 스킬 (10개)

#### 코어 — Excalibur 파이프라인

| 스킬 | 트리거 | 용도 |
|------|--------|------|
| excalibur | `"excalibur"` | 전체 프로젝트 오케스트레이션 (Interview → Ralplan → Ralph → Eval per milestone) |
| deep-interview | `"deep-interview"` | 소크라틱 스펙 공동 작성, 모호성 게이팅 |
| ralph | `"ralph"` | PRD 기반 구현 루프 (TDD, 코드 리뷰, 보안 감사) |
| ralplan | `"ralplan"` | 6-에이전트 합의 기획 (Planner → Researcher → Architect → Designer → Critic) |
| research | `"research"` | 다중 소스 조사 (웹, arxiv, 문서, NotebookLM) |
| upgrade | `"upgrade"` | 자기개선 사이클 (체크섬 → 스냅샷 → 구현 → 리뷰 게이트 → 커밋) |
| rollback | `"rollback"` | 스냅샷 복원 |

#### 유틸리티 — 독립 도구

| 스킬 | 트리거 | 용도 |
|------|--------|------|
| opportunity-scout | `"opportunity-scout"` | 트렌드 기반 기회 탐색 + 마케팅 프레임워크 분석 |
| youtube-transcript | `"youtube-transcript"` | YouTube 자막 추출 (ko/en/ja, 수동+자동생성) |
| setup | `"setup"` | 설치 마법사 (CLAUDE.md, MCP 서버, 설정) |

## 영감 & 크레딧

xLoop의 Excalibur는 7개 오픈소스 프로젝트의 핵심 아이디어를 흡수한 메타 오케스트레이터입니다:

| 출처 | xLoop이 가져온 것 | Excalibur 단계 |
|------|------------------|---------------|
| [**OMC**](https://github.com/Yeachan-Heo/oh-my-claudecode) | 플러그인/스킬/Hook 아키텍처, Ralph PRD 루프, Ralplan 합의 | 기반 |
| [**Ouroboros**](https://github.com/Q00/ouroboros) | 자기개선 개념, 헌법적 거버넌스, 멀티 모델 리뷰 | Upgrade |
| [**gstack**](https://github.com/garrytan/gstack) | Office Hours 리프레이밍, Design Review, Code Review, 보안 감사(CSO), 브라우저 QA, 스프린트 회고 | Interview, Ralplan, Ralph, Eval |
| [**superpowers**](https://github.com/obra/superpowers) | TDD (Red-Green-Refactor), git worktree 격리, fresh subagent, 4단계 디버깅 | Ralph |
| [**ARIS**](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Cross-model adversarial review, 아이디어 발굴 파이프라인 | Ralplan |
| [**autoresearch**](https://github.com/karpathy/autoresearch) | Modify→eval→keep/discard 실험 루프 | Upgrade |
| [**notebooklm-py**](https://github.com/nichochar/notebooklm-py) | NotebookLM API 소스 수집 및 합성 | Research |

### 핵심 차별점

- **메타 오케스트레이터**: 아이디어를 SKILL.md에 흡수 — 런타임 플러그인 의존성 없음
- **Complexity Gate**: 양방향 라우팅 — 단순 작업은 아래로 축소, 복잡한 작업만 위로 확장
- **리서치 통합 기획**: 별도 사전 단계가 아닌 기획 루프 안에서 리서치 수행
- **마일스톤 단위 실행**: 전체 프로젝트가 아닌 한 번에 하나의 청크만 기획
- **Excalibur**: 단일 키워드로 전체 프로젝트 라이프사이클 관리

## 개발

```bash
npm install                 # 개발 의존성 설치
npm run typecheck           # tsc --noEmit
npm test                    # vitest run (94개 테스트)
```

## 라이선스

MIT
