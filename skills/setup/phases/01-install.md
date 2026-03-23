# Phase 1: Install

## Step 1.1: Select target

If `--local` or `--global` flag passed, use that. Otherwise ask:
```
"Where should xLoop be configured?"
1. Local (this project) → .claude/CLAUDE.md
2. Global (all projects) → ~/.claude/CLAUDE.md
```

## Step 1.2: Install CLAUDE.md

1. Backup existing CLAUDE.md (if exists) → `.claude/CLAUDE.md.backup.{YYYY-MM-DD}`
2. Copy bundled `templates/CLAUDE.md` to target location
3. No network required (bundled, not downloaded)

## Step 1.3: Create .xloop/ directories

```
.xloop/
├── state/sessions/
├── plans/
├── research/cache/
├── reports/
├── snapshots/
├── learnings/
└── specs/
```

## Step 1.4: PRINCIPLES.md checksum

1. If PRINCIPLES.md exists, compute SHA-256 → `.xloop-checksum`
2. If not exists, skip (will be created in Phase 4 post-MVP)

## Step 1.5: Git exclude (if git repo)

Add to `.git/info/exclude`:
```
.xloop/state/
.xloop/snapshots/
.xloop/reports/
.xloop/research/cache/
```

## Save progress

Write `.xloop/setup-state.json` → `{ "lastStep": 1, "configTarget": "local|global" }`

If `--local` or `--global` flag: clear setup state and STOP HERE.
