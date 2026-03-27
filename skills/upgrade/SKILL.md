---
name: upgrade
description: Self-improvement cycle — research + plan + implement improvements to xLoop itself
level: 4
---

# Upgrade — Self-Improvement Cycle

<Purpose>
Improve xLoop itself based on auto-verification metrics. Checksum-protected, snapshot-backed, review-gated.
</Purpose>

<Scope_Boundary>
`xloop upgrade` modifies ONLY xLoop package files: agents/, skills/, hooks/, src/, templates/.
It MUST NOT modify host project source code.
</Scope_Boundary>

<Steps>
1. **Checksum verify**: Compute SHA-256 of PRINCIPLES.md, compare to `.xloop-checksum`. Mismatch → ABORT.
2. **Snapshot**: Save current xLoop files to `.xloop/snapshots/{semver}/` via `src/snapshot.ts`.
3. **Ralplan**: 4-agent consensus to plan improvements (research integrated).
   - Input: auto-verification report from `.xloop/reports/`, previous learnings
   - Scope: xLoop internals only
4. **Ralph**: Implement the improvement plan.
5. **Review gate**: Architect + Critic verify changes before commit.
6. **Experiment loop** (autoresearch pattern):
   <!-- Inspired by: Karpathy autoresearch (https://github.com/karpathy/autoresearch) -->
   - **Modify**: Apply the planned change to xLoop files
   - **Eval**: Run auto-verification (5 metrics) on the modified version
   - **Keep/Discard**: If metrics improved → `git commit` (keep). If not → `git revert` (discard).
   - Repeat for each independent improvement in the plan
   - This ensures only proven improvements survive — no regressions
7. **Commit**: Finalize kept changes, update `.xloop/evolution.json`.

On failure at any step → `xloop rollback` to restore from snapshot.
</Steps>

<Safety>
- PRINCIPLES.md protected by SHA-256 checksum + git pre-commit hook
- Max 3 upgrade cycles per session (Mode C)
- Each cycle must improve ≥1 metric vs previous, otherwise halt
- After 3rd cycle: force Mode B (user must approve)
- Rollback always available via `xloop rollback`
</Safety>

<Evolution_Log>
`.xloop/evolution.json` tracks each upgrade:
```json
{
  "upgrades": [
    { "version": "0.1.1", "date": "...", "metrics_before": {...}, "metrics_after": {...}, "files_changed": [...] }
  ]
}
```
</Evolution_Log>
