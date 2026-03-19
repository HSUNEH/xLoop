<h1 align="center">xLoop</h1>

<p align="center">
  <strong>e**X**pert **L**oop - claude code harness</strong><br>
  Automated multi-source deep research powered by Claude Code
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
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

xLoop searches across YouTube, Web, arXiv, and Reddit/HN, analyzes sources with NotebookLM, detects knowledge gaps, and iteratively re-searches until full topic coverage is achieved — all through a single **Expert Loop** pipeline.

## Core Concept

```
Search → Collect sources → NotebookLM analysis → Gap detection → Re-search → ... → Final report
```

Expert Loop doesn't stop at a single search. The AI identifies **missing perspectives (gaps)** from the analysis, automatically matches each gap to the optimal source type, and re-searches to progressively deepen topic coverage.

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

- Python 3.11+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube search
- [notebooklm-py](https://github.com/nichochar/notebooklm-py) — NotebookLM integration
- [Playwright](https://playwright.dev/) — Browser automation
- [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) — Web search
- [arxiv](https://github.com/lukasschwab/arxiv.py) — arXiv paper search

## Usage

### Expert Loop (full pipeline)

```
/expert-loop "AI agents" --max-iterations 3
```

Automatically runs the entire pipeline: session creation → multi-source search → NotebookLM analysis → gap detection → iterative re-search → final report → action card extraction.

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/yt-search` | Search YouTube videos | `/yt-search "transformer" --count 5` |
| `/web-search` | Web search (DuckDuckGo) | `/web-search "AI framework" --time w` |
| `/arxiv-search` | Search arXiv papers | `/arxiv-search "attention mechanism" --sort date` |
| `/community-search` | Search Reddit & HN | `/community-search all "LLM deploy" --min-score 50` |
| `/notebooklm-add` | Add sources to NotebookLM | `/notebooklm-add "research" URL1 URL2` |
| `/notebooklm-ask` | Ask NotebookLM | `/notebooklm-ask <notebook_id> "key summary"` |
| `/research` | Manage research sessions | `/research` |

### Session Management

| Command | Description |
|---------|-------------|
| `/session-new` | Create a new research session |
| `/session-list` | List all sessions |
| `/session-resume` | Resume an existing session |
| `/session-summary` | View session summary |

## Search Options

### yt-search

| Flag | Default | Description |
|------|---------|-------------|
| `--count N` | 20 | Number of results |
| `--months N` | 6 | Filter to last N months |
| `--no-date-filter` | - | Search all time |
| `--min-views N` | 0 | Minimum view count |
| `--min-duration M` | 0 | Minimum length (minutes) |
| `--max-duration M` | 0 | Maximum length (minutes) |
| `--channel NAME` | - | Filter by channel |
| `--json` | - | JSON output |

### web-search

| Flag | Default | Description |
|------|---------|-------------|
| `--count N` | 10 | Number of results |
| `--time d\|w\|m\|y` | - | Time filter |
| `--json` | - | JSON output |

### arxiv-search

| Flag | Default | Description |
|------|---------|-------------|
| `--count N` | 10 | Number of results |
| `--sort` | relevance | `relevance` or `date` |
| `--json` | - | JSON output |

### community-search

| Flag | Default | Description |
|------|---------|-------------|
| platform | (required) | `reddit`, `hn`, or `all` |
| `--count N` | 10 | Number of results |
| `--subreddit NAME` | - | Filter by subreddit |
| `--min-score N` | 0 | Minimum score |
| `--time d\|w\|m\|y` | year | Time filter |
| `--json` | - | JSON output |

## How Expert Loop Works

```
Step 0: Create session + Initialize loop
    |
    v
+--- Loop starts ----------------------------+
|                                             |
|  Step 1: Multi-source search + collection   |
|    -> YouTube / Web / arXiv / Community     |
|    -> User selects results                  |
|    -> Add to NotebookLM                     |
|                                             |
|  Step 2: Deep analysis via NotebookLM       |
|    -> Core concepts, approaches, trade-offs |
|                                             |
|  Step 3: Gap analysis + Source matching      |
|    -> Axes: theory/practice, pro/con, etc.  |
|    -> Match gap type to optimal source      |
|    -> Generate new search queries           |
|                                             |
|  Step 4: Termination check                  |
|    -> Max iterations or no gaps -> exit     |
|    -> Gaps remain -> back to Step 1         |
|                                             |
+---------------------------------------------+
    |
    v
Step 5: Final synthesis
Step 6: Research report generation
Step 7: Action card extraction (-> GitHub Issues)
```

### Gap-to-Source Matching Strategy

| Gap Type | Recommended Source | Rationale |
|----------|-------------------|-----------|
| Theory / Academic / Proofs | arXiv | Papers are the most precise |
| Practical / Implementation / Tutorials | YouTube | Visual explanations, code walkthroughs |
| Comparisons / Opinions / Experience | Community | Real-world developer discussions |
| Latest trends / Official docs | Web | Blogs, official documentation |

## Project Structure

```
xLoop/
├── commands/              <- Claude Code slash commands (13)
|   ├── expert-loop.md     <- Core: Expert Loop orchestration
|   ├── yt-search.md
|   ├── web-search.md
|   ├── arxiv-search.md
|   ├── community-search.md
|   ├── notebooklm-add.md
|   ├── notebooklm-ask.md
|   ├── research.md
|   ├── session-new.md
|   ├── session-list.md
|   ├── session-resume.md
|   └── session-summary.md
├── scripts/               <- Python search & analysis scripts
|   ├── loop_engine.py     <- Loop state management
|   ├── session_manager.py <- Session CRUD + search/source/question tracking
|   ├── yt_search.py       <- YouTube search (yt-dlp)
|   ├── web_search.py      <- Web search (DuckDuckGo)
|   ├── arxiv_search.py    <- arXiv paper search
|   ├── community_search.py<- Reddit & Hacker News search
|   ├── notebooklm_add.py  <- NotebookLM notebook creation + source addition
|   └── notebooklm_ask.py  <- NotebookLM Q&A
├── tests/                 <- pytest tests
├── data/sessions/         <- Session data (JSON)
├── assets/                <- Static resources (images, etc.)
├── requirements.txt
├── setup.sh
└── README.md
```

## Development

```bash
cd xLoop
pytest                     # Run tests
ruff check .               # Lint
ruff format .              # Format
```

## License

MIT
