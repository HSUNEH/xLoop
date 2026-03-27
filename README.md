<h1 align="center">xLoop</h1>

<p align="center">
  <strong>Excalibur — Research-Integrated Agent Harness with Self-Improvement</strong><br>
  Full project orchestration powered by Claude Code
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
  <strong>English</strong> | <a href="./README.ko.md">한국어</a>
</p>

---

xLoop is an **agent harness** that orchestrates planning, research, implementation, and self-improvement — all through a single command.

## Excalibur — The Essence of xLoop

```
xloop excalibur "build a real-time chat app"
```

One command to orchestrate an entire project:

```
Phase 0: Deep Interview (co-create spec with user, one question at a time)
    │
    ▼
Big Loop × N milestones:
    ├── Ralplan (4-agent consensus + integrated research — THIS milestone only)
    ├── Ralph  (PRD-driven implementation loop — parallel execution)
    └── Eval   (auto-verification + learnings → next milestone)
```

### Key Mechanisms

- **Complexity Gate**: 2-step bidirectional routing — simple tasks skip orchestration entirely
- **Research-Integrated Planning**: Research happens WITHIN the planning loop, not before it
- **Milestone-Scoped Execution**: Each loop plans and implements one milestone, not the whole project
- **Auto-Verification**: 5 metrics checked after every implementation cycle
- **Mode B/C**: Semi-auto (user approves) or full-auto (threshold-based) upgrade decisions
- **Self-Improvement**: Checksum-protected, snapshot-backed upgrade cycle with rollback
- **Learnings**: Each milestone's lessons feed into the next loop's planning context

## Architecture

```
Task Entry → Complexity Gate (hook-level, structural)
    │
    ├── score 1 (simple)  → Executor direct — zero overhead
    ├── score 2 (medium)  → Ralph only — skip planning
    └── score 3 (complex) → Ralplan + Ralph — full process
```

### Agents (7)

| Agent | Model | Role |
|-------|-------|------|
| planner | Opus | Strategic planning, research needs identification |
| architect | Opus | Architecture review, steelman counterarguments |
| critic | Opus | Quality gate, principle-option consistency |
| researcher | Sonnet | Multi-source investigation (web, arxiv, docs) |
| executor | Sonnet | Code implementation |
| verifier | Sonnet | Acceptance criteria verification |
| explorer | Haiku | Codebase search, quick lookups |

### Skills (8)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| excalibur | `"excalibur"` | Full project orchestration |
| deep-interview | (via excalibur) | Project spec co-creation |
| ralph | `"ralph"` | PRD-driven implementation loop |
| ralplan | `"ralplan"` | 4-agent consensus planning with integrated research |
| research | `"research"` | Multi-source investigation |
| setup | `"setup"` | Installation wizard |
| upgrade | `"upgrade"` | Self-improvement cycle |
| rollback | `"rollback"` | Snapshot restore |

## Installation

In Claude Code, run the following commands:

```bash
# 1. Add the xLoop marketplace
/plugin marketplace add HSUNEH/xLoop

# 2. Install the plugin
/plugin install xloop@xloop
```

What the setup does:
1. Installs CLAUDE.md (agent instructions)
2. Configures test mode (B: semi-auto / C: full-auto)
3. Registers MCP server (state, notepad, PRD tools)
4. Sets up NotebookLM authentication
5. Configures Complexity Gate thresholds

## Usage

### Full Project Orchestration

```bash
xloop excalibur "real-time chat app"
# → Deep Interview → (Ralplan + Ralph + Eval) × N milestones → Done
```

### Individual Commands

```bash
xloop ralph "fix the auth bug"        # PRD-driven implementation loop
xloop ralplan "design caching layer"   # 4-agent consensus planning
xloop research "WebSocket vs SSE"      # Standalone research
xloop upgrade                          # Self-improvement cycle
xloop rollback                         # Restore from snapshot
xloop status                           # Show current state
```

### Keywords (use naturally in Claude Code)

```
"excalibur build a chat app"   → full project orchestration
"ralph fix this bug"           → implementation loop
"ralplan design new feature"   → consensus planning
```

## Complexity Gate

Every task is structurally routed before any orchestration:

| Score | Route | When |
|-------|-------|------|
| 1 (simple) | Executor direct | "fix typo", "rename X", single file path |
| 2 (medium) | Ralph only | Multi-file task, clear scope |
| 3 (complex) | Ralplan + Ralph | Architecture decisions, vague scope |

**2-step gate**: Structural heuristic (instant, 0 LLM cost) → Haiku micro-assessment (only when uncertain).

3-dimension scoring: Scope (40%) + Clarity (35%) + Decision (25%).

## Excalibur Big Loop

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

### Milestone Parallelization

Independent milestones (no `depends_on` conflicts) run in parallel lanes. Conflict detected → sequential fallback.

### Learnings

Each loop generates `.xloop/learnings/loop-{N}.json`:
- Technical lessons (which libraries/patterns worked)
- Process lessons (story ordering, parallelization)
- Quality lessons (missed metrics)

Next Ralplan receives previous learnings as context.

## Self-Improvement

```
Ralph complete → Auto-verification (5 metrics) → Threshold check
    │
    Mode B: User decides → upgrade or accept
    Mode C: Auto-upgrade if metrics fail (max 3 cycles)
    │
    ▼
xloop upgrade:
  Checksum verify → Snapshot → Ralplan → Ralph → Review gate → Commit
```

**Safety**: PRINCIPLES.md SHA-256 checksum, git pre-commit hook, snapshot/rollback, multi-model review gate. Upgrades modify only xLoop files — never host project code.

## Project Structure

```
xloop/
├── agents/                  ← 7 agent definitions (md)
│   ├── planner.md          (Opus)
│   ├── architect.md        (Opus)
│   ├── critic.md           (Opus)
│   ├── researcher.md       (Sonnet)
│   ├── executor.md         (Sonnet)
│   ├── verifier.md         (Sonnet)
│   └── explorer.md         (Haiku)
├── skills/                  ← 8 skill definitions
│   ├── excalibur/SKILL.md  ← The essence of xLoop
│   ├── deep-interview/SKILL.md
│   ├── ralph/SKILL.md
│   ├── ralplan/SKILL.md
│   ├── research/SKILL.md
│   ├── setup/SKILL.md + phases/
│   ├── upgrade/SKILL.md
│   └── rollback/SKILL.md
├── hooks/                   ← 8 lifecycle hooks
│   ├── hooks.json
│   └── scripts/*.mjs
├── src/                     ← Core TypeScript modules
│   ├── cli.ts              ← CLI entry point
│   ├── mcp-server.ts       ← MCP tool server (7 tools)
│   ├── state.ts            ← Session state management
│   ├── gate.ts             ← Complexity Gate
│   ├── prd.ts              ← PRD scaffold generator
│   ├── router.ts           ← PAL model tier routing
│   ├── checksum.ts         ← PRINCIPLES.md integrity
│   ├── snapshot.ts         ← Pre-upgrade snapshot + rollback
│   ├── excalibur/          ← Excalibur orchestration modules
│   ├── interview.ts        ← Deep Interview logic
│   ├── milestone.ts        ← Milestone progress tracking
│   └── llm-bridge.ts       ← LLM API abstraction
├── templates/CLAUDE.md      ← Project template
├── tests/                   ← 94 tests across 10 files
├── package.json
└── tsconfig.json
```

## Design Decisions

xLoop combines the best of three systems:

| Source | What xLoop Takes | What xLoop Leaves |
|--------|-----------------|-------------------|
| **OMC** | Plugin/skill/hook architecture, Ralph PRD loop, Ralplan consensus, MCP integration | 179K compiled lines, 19 agents, excessive hook injection |
| **Ouroboros (razzant)** | Self-modification concept, constitutional governance, multi-model review | Colab dependency, unlimited self-mod, no rollback |
| **Ouroboros (Q00)** | Ambiguity scoring inspiration, specification-first approach | 166 Python modules, no fast path, immutable specs |

### Key Differentiators

- **Complexity Gate**: Bidirectional routing — OMC and Ouroboros only scale UP, xLoop also scales DOWN
- **Research-Integrated Planning**: Research within the planning loop, not as a separate pre-step
- **Milestone-Scoped Execution**: Plan one chunk at a time, not the whole project
- **Excalibur**: Single command for entire project lifecycle

## Development

```bash
npm install
npm run typecheck           # tsc --noEmit
npm test                    # vitest run (94 tests)
npm run build               # tsc
```

## License

MIT
