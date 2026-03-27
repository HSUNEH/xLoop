# Phase 3: Welcome

## Step 3.1: Verify Installation

1. CLAUDE.md exists at target location
2. MCP server registered (check `claude mcp list` for "xloop")
3. .xloop/ directories exist (state, plans, research, reports, snapshots, learnings, specs)
4. If PRINCIPLES.md exists: checksum matches .xloop-checksum

## Step 3.2: Quick Start Guide

```
xLoop Setup Complete!

Getting Started:
  xloop excalibur <description>  — Full project orchestration (the essence of xLoop)
  xloop ralph <task>             — PRD-driven implementation loop
  xloop ralplan <task>           — 6-agent consensus planning

Keywords (use naturally):
  "excalibur ..."  → project orchestration
  "ralph ..."      → implementation loop
  "ralplan ..."    → consensus planning

Settings:
  Test mode: {B|C}
  Complexity Gate: active (simple tasks auto-routed to executor)

Config: ~/.claude/.xloop-config.json
```

## Step 3.3: Mark Completion

Save to `~/.claude/.xloop-config.json`:
```json
{
  "setupCompleted": "2026-03-24T...",
  "setupVersion": "0.3.0",
  "testMode": "B",
  "gate": { "simple": 1.5, "medium": 2.2 },
  "configTarget": "local"
}
```

Delete `.xloop/setup-state.json` (setup complete, no longer needed).
