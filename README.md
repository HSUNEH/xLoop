<h1 align="center">xLoop</h1>

<p align="center">
  <strong>eXpert Loop — 6-Phase Production Pipeline Orchestrator</strong><br>
  Automated multi-source deep research & content production powered by Claude Code
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
  <strong>English</strong> | <a href="./README.ko.md">한국어</a>
</p>

---

xLoop is a **6-Phase production pipeline orchestrator** that takes a goal from definition through research, strategy, execution, evaluation, and drift correction — all automated through Claude Code slash commands.

## 6-Phase Pipeline

```
Phase 0        Phase 1        Phase 2        Phase 3        Phase 4        Phase 5
Big Bang  -->  Research  -->  Strategy  -->  Execution -->  Evaluation --> Drift Check
(goal)         (search)       (plan)         (produce)      (validate)     (correct)
   |                                                             |              |
   |              spec.json → research.json → strategy.json → execution.json → validation.json
   |                                                                            |
   +<---------- drift > 0.3: restart --------<---------<---------<-------------+
                 drift ≤ 0.3: backtrack to Phase 2
```

### Phase Details

| Phase | Command | Module | Output |
|-------|---------|--------|--------|
| 0 — Big Bang | `/big-bang` | `goal_engine.py`, `pipeline_spec.py` | `spec.json` |
| 1 — Research | `/expert-loop` | `loop_engine.py`, search scripts | `research.json` |
| 2 — Strategy | `/strategy-build` | `strategy_engine.py` | `strategy.json` |
| 3 — Execution | `/execute` | `execution_engine.py` | `execution.json` |
| 4 — Evaluation | `/validate` | `evaluation_engine.py` | `validation.json` |
| 5 — Drift Check | (auto) | `drift_checker.py` | action decision |

### Key Mechanisms

- **Ambiguity Gate** (Phase 0): Goal refinement loop until ambiguity score ≤ 0.2
- **Resilience** (Phase 1): Stagnation detection + persona switching (Researcher → Hacker → Contrarian → Simplifier)
- **Double Diamond** (Phase 2): Diverge (generate candidates) → Converge (filter by constraints)
- **Tool Registry** (Phase 3): Pluggable tool execution (dall-e, flux, etc.)
- **B+C Drift Measurement** (Phase 4): 3-stage validation (mechanical → semantic → consensus with advocate/critic/judge)
- **PAL Router**: Per-phase model tier routing (frugal 1x / standard 10x / frontier 30x)
- **Headless Execution**: Auto source selection, retry with skip, structured logging, webhook alerts

## Installation

```bash
cd xLoop
bash setup.sh
notebooklm login  # Google account authentication
```

What `setup.sh` does:
1. Installs Python dependencies (`requirements.txt`)
2. Verifies yt-dlp installation
3. Installs Playwright Chromium (for NotebookLM)
4. Guides NotebookLM authentication
5. Installs NotebookLM skill
6. Symlinks slash commands to `.claude/commands/`

## Requirements

- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube search
- [notebooklm-py](https://github.com/nichochar/notebooklm-py) — NotebookLM integration
- [Playwright](https://playwright.dev/) — Browser automation
- [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) — Web search
- [arxiv](https://github.com/lukasschwab/arxiv.py) — arXiv paper search

## Usage

### Full Pipeline

```bash
# 1. Define goal (interactive)
/big-bang

# 2. Run full pipeline
bash scripts/pipeline_runner.sh <session_id>

# Or run phases individually:
/expert-loop --session <session_id>   # Phase 1
/strategy-build --session <session_id> # Phase 2
/execute --session <session_id>        # Phase 3
/validate --session <session_id>       # Phase 4
```

### Pipeline Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/big-bang` | 0 | Define goal, deliverables, success criteria |
| `/expert-loop` | 1 | Multi-source deep research loop |
| `/strategy-build` | 2 | Generate execution strategy from research |
| `/execute` | 3 | Execute tasks via tool registry |
| `/validate` | 4 | 3-stage validation + drift scoring |

### Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/yt-search` | YouTube search | `/yt-search "transformer" --count 5` |
| `/web-search` | Web search (DuckDuckGo) | `/web-search "AI framework" --time w` |
| `/arxiv-search` | arXiv paper search | `/arxiv-search "attention mechanism" --sort date` |
| `/community-search` | Reddit & HN search | `/community-search all "LLM deploy" --min-score 50` |

### Session & NotebookLM

| Command | Description |
|---------|-------------|
| `/session-new` | Create a new session |
| `/session-list` | List all sessions |
| `/session-resume` | Resume existing session |
| `/session-summary` | View session summary |
| `/notebooklm-add` | Add sources to NotebookLM |
| `/notebooklm-ask` | Ask NotebookLM questions |
| `/research` | Research session management |

## Architecture

```
xLoop/
├── commands/                <- Claude Code slash commands (16)
│   ├── big-bang.md          <- Phase 0: Goal definition
│   ├── expert-loop.md       <- Phase 1: Research loop
│   ├── strategy-build.md    <- Phase 2: Strategy generation
│   ├── execute.md           <- Phase 3: Task execution
│   ├── validate.md          <- Phase 4: Validation
│   ├── yt-search.md         <- YouTube search
│   ├── web-search.md        <- Web search
│   ├── arxiv-search.md      <- arXiv search
│   ├── community-search.md  <- Reddit/HN search
│   ├── notebooklm-add.md    <- NotebookLM source addition
│   ├── notebooklm-ask.md    <- NotebookLM Q&A
│   ├── research.md          <- Research management
│   ├── session-new.md
│   ├── session-list.md
│   ├── session-resume.md
│   └── session-summary.md
├── scripts/                 <- Python modules (17)
│   ├── pipeline_spec.py     <- Pipeline Spec (Phase 0 schema)
│   ├── goal_engine.py       <- Goal refinement loop
│   ├── pipeline_schema.py   <- Phase 간 JSON schema contracts
│   ├── pipeline_runner.sh   <- Phase 0→5 orchestrator
│   ├── loop_engine.py       <- Research loop + resilience
│   ├── strategy_engine.py   <- Strategy generation (Double Diamond)
│   ├── execution_engine.py  <- Task execution + tool registry
│   ├── evaluation_engine.py <- 3-stage validation (B+C drift)
│   ├── drift_checker.py     <- Drift check + backtrack/restart
│   ├── pal_router.py        <- Per-phase model tier routing
│   ├── headless.py          <- Auto source selection, retry, logging, alerts
│   ├── session_manager.py   <- Session CRUD
│   ├── yt_search.py         <- YouTube search (yt-dlp)
│   ├── web_search.py        <- Web search (DuckDuckGo)
│   ├── arxiv_search.py      <- arXiv paper search
│   ├── community_search.py  <- Reddit & HN search
│   ├── notebooklm_add.py    <- NotebookLM notebook + source
│   └── notebooklm_ask.py    <- NotebookLM Q&A
├── tests/                   <- pytest tests (400+)
├── data/
│   ├── sessions/            <- Session data (JSON)
│   └── pipelines/           <- Pipeline handoff data
├── requirements.txt
├── setup.sh
└── README.md
```

### Data Flow

```
spec.json ──→ research.json ──→ strategy.json ──→ execution.json ──→ validation.json
  (Phase 0)     (Phase 1)        (Phase 2)         (Phase 3)          (Phase 4)
     ↑                                                                     │
     └──── handoff_{N}_to_{N+1}.json between each phase ──────────────────→│
                                                                    drift_score
                                                                     > 0.3 → Phase 0
                                                                     ≤ 0.3 → Phase 2
```

## Development

```bash
cd xLoop
pytest                     # Run tests (400+)
ruff check scripts/ tests/ # Lint
```

### Coding Conventions

- Procedural design (no classes)
- `snake_case` for functions/variables, `UPPER_SNAKE_CASE` for constants
- Custom CLI parsing (no argparse)
- `ensure_ascii=False` for all JSON output
- `stderr` + `sys.exit(1)` for errors
- `subprocess` with list args (no `shell=True`)
- Lazy imports

## License

MIT
