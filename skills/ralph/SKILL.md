---
name: ralph
description: PRD-driven persistence loop — implements until all stories pass with verification
level: 4
---

# Ralph — PRD-Driven Implementation Loop

<Purpose>
Ralph keeps working on a task until ALL user stories in prd.json have passes: true and are reviewer-verified. Uses parallel execution for independent work, saves state between stories, and requires fresh evidence for every acceptance criterion.
</Purpose>

<Use_When>
- Task requires guaranteed completion with verification
- User says "ralph", "don't stop", "finish this"
- Work benefits from structured PRD-driven execution
</Use_When>

<Do_Not_Use_When>
- Full project orchestration needed — use `excalibur`
- Planning needed before implementation — use `ralplan`
- Quick one-shot fix — delegate directly to executor agent
</Do_Not_Use_When>

<Execution_Policy>
- Fire independent agent calls simultaneously — never wait sequentially for independent work
- Route to correct model tier: explorer (Haiku), executor (Sonnet), architect review (Opus)
- Use `run_in_background: true` for long operations (builds, tests, installs)
- Track background tasks; verify all complete before marking story done
- Deliver full implementation: no scope reduction, no partial completion
</Execution_Policy>

<Steps>
1. **PRD Setup** (first iteration only):
   a. Check if `prd.json` exists. If yes, read and proceed to Step 2.
   b. If no `prd.json`, generate scaffold via `xloop_prd_generate` MCP tool or deterministic template.
   c. **Refine the scaffold**: Replace generic criteria with task-specific, verifiable criteria.
   d. Order stories by priority (foundational first, dependent later).
   e. Write refined `prd.json` to disk.

2. **Pick next story**: Select highest-priority story with `passes: false`.

3. **Implement**: Delegate to specialist agents at appropriate tiers.
   - If independent sub-tasks exist, fire them in parallel.
   - If sub-tasks are discovered during implementation, add as new stories to `prd.json`.

4. **Verify**: For EACH acceptance criterion, verify with fresh evidence.
   - Run tests, builds, lint, typecheck and read the output.
   - If any criterion NOT met, continue working — do NOT mark complete.

5. **Mark complete + save state**:
   a. Set `passes: true` for this story in `prd.json`.
   b. **Save ralph-state.json and prd.json to disk** (protects against context compaction).
   c. Record progress in `progress.txt`.

6. **Check completion**: All stories `passes: true`? If not, loop to Step 2.

7. **Reviewer verification**: Verifier or architect reviews against specific acceptance criteria from prd.json.

8. **On approval**: Clean state and report completion.

9. **On rejection**: Fix issues, re-verify, loop back.
</Steps>

<OMC_Pattern_Checklist>
Executor must verify each during ralph SKILL.md authoring:
- [ ] PRD refinement step (concrete, verifiable criteria)
- [ ] Story-by-story execution (one at a time, in priority order)
- [ ] Parallel execution policy (independent tasks simultaneously)
- [ ] Background operation rules (builds/tests in background)
- [ ] Tiered reviewer verification (scope-appropriate tier)
- [ ] State persistence between stories (save after each completion)
- [ ] Escalation conditions (blocker → report, same issue 3x → fundamental problem)
- [ ] Final checklist (all stories pass, tests pass, build succeeds)
</OMC_Pattern_Checklist>

<Escalation>
- Fundamental blocker requiring user input → stop and report
- Same issue 3+ iterations → report as potential fundamental problem
- User says "stop" or "cancel" → clean exit
</Escalation>
