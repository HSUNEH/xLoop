---
name: setup
description: Install and configure xLoop — the only command you need to learn
level: 2
---

# xLoop Setup

The **only command you need to learn**. After this, everything else is automatic.

## Flag Parsing

- `--help` → Show help and stop
- `--local` → Phase 1 only (target=local), then stop
- `--global` → Phase 1 only (target=global), then stop
- `--force` → Skip "already configured" check, run full setup

## Pre-Setup Check

Check `~/.claude/.xloop-config.json` for `setupCompleted`. If already configured (and no --force):
- "xLoop is already configured. What would you like to do?"
  1. Update CLAUDE.md only
  2. Run full setup again
  3. Cancel

## Resume Detection

Check `.xloop/setup-state.json`. If exists:
- "Found previous setup session. Resume from step {N}? [Y/start fresh]"

## Phase Execution

### Phase 1 — Install
Read `skills/setup/phases/01-install.md` and follow instructions.

### Phase 2 — Configure
Read `skills/setup/phases/02-configure.md` and follow instructions.

### Phase 3 — Welcome
Read `skills/setup/phases/03-welcome.md` and follow instructions.

## Re-setup

```
xloop setup              # Normal (checks if configured)
xloop setup --force      # Force full re-setup
xloop setup --local      # Update local CLAUDE.md only
xloop setup --global     # Update global CLAUDE.md only
```
