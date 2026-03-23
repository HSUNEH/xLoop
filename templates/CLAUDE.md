# xLoop — Agent Harness for Research-Integrated Planning + Self-Improvement

You are running with xLoop, a lean agent harness that orchestrates planning, research, implementation, and self-improvement.

## Core Command

`xloop excalibur <description>` — The essence of xLoop. Full project orchestration:
1. Deep Interview → project-spec.json (co-created with user)
2. Big Loop × N milestones: Ralplan → Ralph → Eval → next milestone

## Complexity Gate

Every task is auto-routed before any orchestration:
- **Score 1 (simple)**: Executor direct — zero overhead
- **Score 2 (medium)**: Ralph only — skip planning
- **Score 3 (complex)**: Ralplan + Ralph — full process

Keywords bypass the gate: "excalibur", "ralph", "ralplan" route directly.

## Agents (7)

| Agent | Model | Role |
|-------|-------|------|
| planner | Opus | Strategic planning, research needs identification |
| architect | Opus | Architecture review, steelman counterarguments |
| critic | Opus | Quality gate, principle-option consistency |
| researcher | Sonnet | Multi-source investigation (web, arxiv, docs) |
| executor | Sonnet | Code implementation |
| verifier | Sonnet | Acceptance criteria verification |
| explorer | Haiku | Codebase search, quick lookups |

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| excalibur | "excalibur" | Full project orchestration |
| ralph | "ralph" | PRD-driven implementation loop |
| ralplan | "ralplan" | 4-agent consensus planning with integrated research |
| research | "research" | Multi-source investigation |
| deep-interview | (via excalibur) | Project spec co-creation |
| setup | "setup" | Installation wizard |
| upgrade | "upgrade" | Self-improvement cycle |
| rollback | "rollback" | Snapshot restore |

## Hooks (8 events)

| Event | Behavior |
|-------|----------|
| SessionStart | Initialize .xloop/ directories |
| UserPromptSubmit | Detect keywords (excalibur, ralph, ralplan, research, upgrade) |
| PreToolUse | Parallel execution hints (Agent/Bash only) |
| PostToolUse | Validation (Write/Edit only) |
| PostToolUseFailure | Recovery guidance |
| SubagentStart | Track agent spawn |
| SubagentStop | Review gate + duration |
| Stop | State persistence + cleanup |

## Test Modes

- **Mode B (semi-auto)**: Auto-verify → user approves upgrade
- **Mode C (full-auto)**: Auto-verify → threshold-based auto-upgrade (max 3 cycles)

## State Paths

- `.xloop/state/sessions/{id}/` — Session state (ralph, ralplan, excalibur)
- `.xloop/plans/` — Generated plans
- `.xloop/research/` — Research findings + cache
- `.xloop/reports/` — Auto-verification reports
- `.xloop/snapshots/` — Pre-upgrade snapshots
- `.xloop/learnings/` — Milestone learnings
- `.xloop/specs/` — Project specifications

## Excalibur Workflow

```
xloop excalibur "project description"
  → Deep Interview (one question at a time, user co-creates spec)
  → Big Loop per milestone:
    → Ralplan (4 agents + research, THIS milestone only)
    → Ralph (implement stories, parallel execution)
    → Eval (metrics + learnings + checkpoint)
  → Project complete
```
