<h1 align="center">xLoop</h1>

<p align="center">
  <strong>Excalibur — Research-Integrated Agent Harness with Self-Improvement</strong><br>
  Full project orchestration powered by Claude Code
</p>

<p align="center">
  <img src="https://img.shields.io/badge/claude_code-plugin-blueviolet" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/version-0.2.0-orange" alt="v0.2.0">
</p>

<p align="center">
  <img src="assets/banner.png" alt="xLoop Banner" width="720" />
</p>

<p align="center">
  <strong>English</strong> | <a href="./README.ko.md">한국어</a>
</p>

---

xLoop is a **Claude Code plugin** that orchestrates planning, research, implementation, and self-improvement — all through a single keyword.

## Quick Start

### 1. Install

In Claude Code, run:

```
/plugin marketplace add HSUNEH/xLoop
/plugin install xloop@xloop
```

### 2. Use

Just type a keyword naturally in Claude Code:

```
excalibur "build a real-time chat app"
```

That's it. xLoop handles the rest:

```
Deep Interview → (Ralplan + Ralph + Eval) × N milestones → Done
```

## Keywords

| Keyword | What it does |
|---------|-------------|
| `excalibur "..."` | Full project orchestration (interview → plan → implement → verify) |
| `ralph "..."` | PRD-driven implementation loop |
| `ralplan "..."` | 4-agent consensus planning with integrated research |
| `research "..."` | Multi-source investigation (web, arxiv, docs) |
| `upgrade` | Self-improvement cycle |
| `rollback` | Restore from snapshot |

---

## How It Works

### Complexity Gate

Every task is automatically routed before orchestration:

| Score | Route | Example |
|-------|-------|---------|
| 1 (simple) | Executor direct | "fix typo", "rename X" |
| 2 (medium) | Ralph only | multi-file task, clear scope |
| 3 (complex) | Ralplan + Ralph | architecture decisions, vague scope |

2-step gate: Structural heuristic (instant, 0 LLM cost) → Haiku micro-assessment (only when uncertain).

3-dimension scoring: Scope (40%) + Clarity (35%) + Decision (25%).

### Excalibur Big Loop

```
Big Loop #1 (M1: MVP)
  ├── Ralplan: Plan M1 features only (+ research as needed)
  ├── Ralph: Implement M1 stories (parallel execution)
  └── Eval: Auto-verify → update spec → generate learnings
        │
        Mode B: "M1 done (33%). Proceed / modify spec / upgrade?"
        Mode C: 10-second checkpoint → auto-proceed

Big Loop #2 (M2 + M3 in parallel if independent)
  ├── Lane A: Ralplan(M2) → Ralph(M2)
  ├── Lane B: Ralplan(M3) → Ralph(M3)  [concurrent]
  └── Eval: Both complete → project done
```

Independent milestones run in parallel lanes. Conflict detected → sequential fallback.

Each loop generates `.xloop/learnings/loop-{N}.json` (technical, process, quality lessons) that feed into the next loop.

### Self-Improvement

```
Ralph complete → Auto-verification (5 metrics) → Threshold check
    │
    Mode B: User decides → upgrade or accept
    Mode C: Auto-upgrade if metrics fail (max 3 cycles)
    │
    ▼
upgrade:
  Checksum verify → Snapshot → Ralplan → Ralph → Review gate → Commit
```

**Safety**: SHA-256 checksum, git pre-commit hook, snapshot/rollback, multi-model review gate. Upgrades modify only xLoop files — never your project code.

## Agents & Skills

### Agents (7)

| Agent | Model | Role |
|-------|-------|------|
| planner | Opus | Strategic planning, research needs identification |
| architect | Opus | Architecture review, steelman counterarguments |
| critic | Opus | Quality gate, principle-option consistency |
| researcher | Sonnet | Multi-source investigation |
| executor | Sonnet | Code implementation |
| verifier | Sonnet | Acceptance criteria verification |
| explorer | Haiku | Codebase search, quick lookups |

### Skills (8)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| excalibur | `"excalibur"` | Full project orchestration |
| deep-interview | (via excalibur) | Project spec co-creation |
| ralph | `"ralph"` | PRD-driven implementation loop |
| ralplan | `"ralplan"` | 4-agent consensus planning |
| research | `"research"` | Multi-source investigation |
| setup | `"setup"` | Installation wizard |
| upgrade | `"upgrade"` | Self-improvement cycle |
| rollback | `"rollback"` | Snapshot restore |

## Design Decisions

xLoop combines the best of three systems:

| Source | What xLoop Takes | What xLoop Leaves |
|--------|-----------------|-------------------|
| **OMC** | Plugin/skill/hook architecture, Ralph PRD loop, Ralplan consensus, MCP integration | 179K compiled lines, 19 agents, excessive hook injection |
| **Ouroboros (razzant)** | Self-modification concept, constitutional governance, multi-model review | Colab dependency, unlimited self-mod, no rollback |
| **Ouroboros (Q00)** | Ambiguity scoring inspiration, specification-first approach | 166 Python modules, no fast path, immutable specs |

### Key Differentiators

- **Complexity Gate**: Bidirectional routing — scales DOWN for simple tasks, not just up
- **Research-Integrated Planning**: Research within the planning loop, not as a separate pre-step
- **Milestone-Scoped Execution**: Plan one chunk at a time, not the whole project
- **Excalibur**: Single keyword for entire project lifecycle

## Development

```bash
npm install                 # install dev dependencies
npm run typecheck           # tsc --noEmit
npm test                    # vitest run (94 tests)
```

## License

MIT
