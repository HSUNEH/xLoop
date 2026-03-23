---
name: rollback
description: Restore xLoop from a previous snapshot
level: 2
---

# Rollback — Snapshot Restore

<Purpose>
Restore xLoop to a previous state after a failed upgrade or unwanted changes.
</Purpose>

<Steps>
1. **List snapshots**: Read `.xloop/snapshots/` directory, show available versions with dates.
2. **Select**: User picks a version, or default to latest snapshot.
3. **Restore**: Copy snapshot files back to agents/, skills/, hooks/, src/, templates/.
4. **Verify**: Run typecheck + tests to confirm restoration is valid.
5. **Report**: Show what was restored and from which version.
</Steps>

<CLI>
```
xloop rollback           # Restore latest snapshot
xloop rollback 0.1.0     # Restore specific version
xloop rollback --list     # List available snapshots
```
</CLI>
