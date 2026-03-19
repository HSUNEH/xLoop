<h1 align="center">xLoop</h1>

<p align="center">
  <strong>eXpert Loop — 6-Phase 프로덕션 파이프라인 오케스트레이터</strong><br>
  Claude Code 기반 멀티소스 딥 리서치 & 콘텐츠 프로덕션 자동화
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/claude_code-harness-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

<p align="center">
  <img src="assets/banner.png" alt="xLoop Banner" width="720" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <strong>한국어</strong>
</p>

---

xLoop은 목표 정의부터 리서치, 전략, 실행, 평가, 드리프트 보정까지 자동화하는 **6-Phase 프로덕션 파이프라인 오케스트레이터**입니다. Claude Code 슬래시 커맨드로 전체 파이프라인을 제어합니다.

## 6-Phase 파이프라인

```
Phase 0        Phase 1        Phase 2        Phase 3        Phase 4        Phase 5
Big Bang  -->  Research  -->  Strategy  -->  Execution -->  Evaluation --> Drift Check
(목표 정의)    (리서치)       (전략 수립)    (실행)         (검증)         (보정)
   |                                                             |              |
   |              spec.json → research.json → strategy.json → execution.json → validation.json
   |                                                                            |
   +<---------- drift > 0.3: 재시작 --------<---------<---------<--------------+
                 drift ≤ 0.3: Phase 2로 백트래킹
```

### Phase 상세

| Phase | 커맨드 | 모듈 | 출력 |
|-------|--------|------|------|
| 0 — Big Bang | `/big-bang` | `goal_engine.py`, `pipeline_spec.py` | `spec.json` |
| 1 — Research | `/expert-loop` | `loop_engine.py`, 검색 스크립트 | `research.json` |
| 2 — Strategy | `/strategy-build` | `strategy_engine.py` | `strategy.json` |
| 3 — Execution | `/execute` | `execution_engine.py` | `execution.json` |
| 4 — Evaluation | `/validate` | `evaluation_engine.py` | `validation.json` |
| 5 — Drift Check | (자동) | `drift_checker.py` | 행동 결정 |

### 핵심 메커니즘

- **Ambiguity Gate** (Phase 0): 모호성 점수 ≤ 0.2 이하가 될 때까지 목표 구체화 루프
- **Resilience** (Phase 1): 정체 감지 + 페르소나 전환 (Researcher → Hacker → Contrarian → Simplifier)
- **Double Diamond** (Phase 2): 발산 (후보 생성) → 수렴 (제약조건 필터링)
- **Tool Registry** (Phase 3): 플러그인 방식 도구 실행 (dall-e, flux 등)
- **B+C Drift Measurement** (Phase 4): 3단계 검증 (기계적 → 의미적 → 합의: 옹호자/비판자/판사)
- **PAL Router**: Phase별 모델 티어 라우팅 (frugal 1x / standard 10x / frontier 30x)
- **Headless Execution**: 자동 소스 선택, 재시도+건너뛰기, 구조화 로깅, 웹훅 알림

## 설치

```bash
cd xLoop
bash setup.sh
notebooklm login  # Google 계정 인증
```

setup.sh가 수행하는 작업:
1. Python 의존성 설치 (`requirements.txt`)
2. yt-dlp 설치 확인
3. Playwright Chromium 설치 (NotebookLM용)
4. NotebookLM 인증 안내
5. NotebookLM 스킬 설치
6. 슬래시 커맨드를 `.claude/commands/`에 심링크

## 요구사항

- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube 검색
- [notebooklm-py](https://github.com/nichochar/notebooklm-py) — NotebookLM 연동
- [Playwright](https://playwright.dev/) — 브라우저 자동화
- [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) — 웹 검색
- [arxiv](https://github.com/lukasschwab/arxiv.py) — arXiv 논문 검색

## 사용법

### 전체 파이프라인

```bash
# 1. 목표 정의 (대화형)
/big-bang

# 2. 전체 파이프라인 실행
bash scripts/pipeline_runner.sh <session_id>

# 또는 Phase별 개별 실행:
/expert-loop --session <session_id>    # Phase 1
/strategy-build --session <session_id> # Phase 2
/execute --session <session_id>        # Phase 3
/validate --session <session_id>       # Phase 4
```

### 파이프라인 커맨드

| 커맨드 | Phase | 설명 |
|--------|-------|------|
| `/big-bang` | 0 | 목표, 산출물, 성공 기준 정의 |
| `/expert-loop` | 1 | 멀티소스 딥 리서치 루프 |
| `/strategy-build` | 2 | 리서치 기반 실행 전략 생성 |
| `/execute` | 3 | 도구 레지스트리를 통한 태스크 실행 |
| `/validate` | 4 | 3단계 검증 + 드리프트 점수 |

### 검색 커맨드

| 커맨드 | 설명 | 예시 |
|--------|------|------|
| `/yt-search` | YouTube 검색 | `/yt-search "transformer" --count 5` |
| `/web-search` | 웹 검색 (DuckDuckGo) | `/web-search "AI framework" --time w` |
| `/arxiv-search` | arXiv 논문 검색 | `/arxiv-search "attention mechanism" --sort date` |
| `/community-search` | Reddit & HN 검색 | `/community-search all "LLM deploy" --min-score 50` |

### 세션 & NotebookLM

| 커맨드 | 설명 |
|--------|------|
| `/session-new` | 새 세션 생성 |
| `/session-list` | 세션 목록 조회 |
| `/session-resume` | 기존 세션 이어하기 |
| `/session-summary` | 세션 요약 보기 |
| `/notebooklm-add` | NotebookLM에 소스 추가 |
| `/notebooklm-ask` | NotebookLM에 질문 |
| `/research` | 리서치 세션 관리 |

## 아키텍처

```
xLoop/
├── commands/                <- Claude Code 슬래시 커맨드 (16개)
│   ├── big-bang.md          <- Phase 0: 목표 정의
│   ├── expert-loop.md       <- Phase 1: 리서치 루프
│   ├── strategy-build.md    <- Phase 2: 전략 생성
│   ├── execute.md           <- Phase 3: 태스크 실행
│   ├── validate.md          <- Phase 4: 검증
│   ├── yt-search.md         <- YouTube 검색
│   ├── web-search.md        <- 웹 검색
│   ├── arxiv-search.md      <- arXiv 검색
│   ├── community-search.md  <- Reddit/HN 검색
│   ├── notebooklm-add.md    <- NotebookLM 소스 추가
│   ├── notebooklm-ask.md    <- NotebookLM 질의응답
│   ├── research.md          <- 리서치 관리
│   ├── session-new.md
│   ├── session-list.md
│   ├── session-resume.md
│   └── session-summary.md
├── scripts/                 <- Python 모듈 (17개)
│   ├── pipeline_spec.py     <- Pipeline Spec (Phase 0 스키마)
│   ├── goal_engine.py       <- 목표 구체화 루프
│   ├── pipeline_schema.py   <- Phase 간 JSON 스키마 계약
│   ├── pipeline_runner.sh   <- Phase 0→5 오케스트레이터
│   ├── loop_engine.py       <- 리서치 루프 + 레질리언스
│   ├── strategy_engine.py   <- 전략 생성 (Double Diamond)
│   ├── execution_engine.py  <- 태스크 실행 + 도구 레지스트리
│   ├── evaluation_engine.py <- 3단계 검증 (B+C 드리프트)
│   ├── drift_checker.py     <- 드리프트 검사 + 백트래킹/재시작
│   ├── pal_router.py        <- Phase별 모델 티어 라우팅
│   ├── headless.py          <- 자동 소스 선택, 재시도, 로깅, 알림
│   ├── session_manager.py   <- 세션 CRUD
│   ├── yt_search.py         <- YouTube 검색 (yt-dlp)
│   ├── web_search.py        <- 웹 검색 (DuckDuckGo)
│   ├── arxiv_search.py      <- arXiv 논문 검색
│   ├── community_search.py  <- Reddit & Hacker News 검색
│   ├── notebooklm_add.py    <- NotebookLM 노트북 + 소스
│   └── notebooklm_ask.py    <- NotebookLM 질의응답
├── tests/                   <- pytest 테스트 (440+)
├── data/
│   ├── sessions/            <- 세션 데이터 (JSON)
│   └── pipelines/           <- 파이프라인 핸드오프 데이터
├── requirements.txt
├── setup.sh
└── README.md
```

### 데이터 흐름

```
spec.json ──→ research.json ──→ strategy.json ──→ execution.json ──→ validation.json
  (Phase 0)     (Phase 1)        (Phase 2)         (Phase 3)          (Phase 4)
     ↑                                                                     │
     └──── handoff_{N}_to_{N+1}.json (Phase 간 핸드오프) ─────────────────→│
                                                                    drift_score
                                                                     > 0.3 → Phase 0
                                                                     ≤ 0.3 → Phase 2
```

## 개발

```bash
cd xLoop
pytest                     # 테스트 실행 (440+)
ruff check scripts/ tests/ # 린트
```

### 코딩 컨벤션

- 절차적 설계 (클래스 미사용)
- `snake_case` (함수/변수), `UPPER_SNAKE_CASE` (상수)
- 커스텀 CLI 파싱 (argparse 미사용)
- `ensure_ascii=False` (모든 JSON 출력)
- `stderr` + `sys.exit(1)` (에러 처리)
- `subprocess` 리스트 인자 전달 (`shell=True` 금지)
- Lazy import

## 라이선스

MIT
