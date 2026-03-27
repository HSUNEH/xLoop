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

<TDD_Mode>
<!-- Inspired by: superpowers TDD (https://github.com/obra/superpowers) -->
When invoked with `--tdd` flag, enforce Red-Green-Refactor for every story:

1. **RED**: Write tests FIRST that describe the expected behavior. Run them — they MUST fail.
2. **GREEN**: Write minimal implementation to make tests pass. No extra code.
3. **REFACTOR**: Clean up while keeping tests green. Remove duplication.

Rules:
- Code written before tests → delete it and restart from RED
- Each story must have at least one test before implementation begins
- If `--tdd` is not set, normal execution (tests encouraged but not enforced)
</TDD_Mode>

<Worktree_Isolation>
<!-- Inspired by: superpowers git worktree (https://github.com/obra/superpowers) -->
When working within excalibur (milestone-scoped execution):
- Create a git worktree on a new branch for this milestone
- Run project setup in the worktree, verify clean test baseline
- All implementation happens in the worktree — main branch untouched
- On milestone completion: merge worktree branch back to main
- On failure: worktree can be discarded without affecting main
- If git worktree is unavailable, fall back to normal branch workflow
</Worktree_Isolation>

<Fresh_Subagent>
<!-- Inspired by: superpowers fresh subagent per task (https://github.com/obra/superpowers) -->
For multi-story execution, each story gets a fresh executor agent:
- New agent receives only: story spec + relevant code context + test results
- Previous story's conversation history is NOT carried over
- Prevents context drift during long autonomous sessions
- State is preserved via prd.json and ralph-state.json, not agent memory
</Fresh_Subagent>

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

7. **Code Review**:
   <!-- Inspired by: gstack /review (https://github.com/garrytan/gstack) -->
   - Dedicated reviewer checks: plan compliance, performance, maintainability
   - Review the diff, not the whole file — focus on what changed

8. **Security Audit**:
   <!-- Inspired by: gstack /cso (https://github.com/garrytan/gstack) -->
   - Check OWASP Top 10: injection, auth bypass, XSS, CSRF, data exposure
   - Validate input sanitization on all user-facing endpoints
   - If no security concerns found, pass silently (no noise)

9. **Reviewer verification**: Verifier or architect reviews against specific acceptance criteria from prd.json.

10. **On approval**: Clean state and report completion.

11. **On rejection**: Fix issues, re-verify, loop back.
</Steps>

<Debug_Protocol>
<!-- Inspired by: superpowers 4-phase debugging (https://github.com/obra/superpowers) -->
When a test or verification fails, follow this 4-step protocol:

1. **Reproduce**: Create a minimal reproduction of the failure. Write a test that triggers it.
2. **Isolate**: Narrow down to the specific module/function. Binary search if needed.
3. **Root Cause**: Identify WHY it fails, not just WHERE. Check assumptions.
4. **Fix**: Apply the minimal fix. Verify the reproduction test now passes.

Rules:
- Do NOT guess-and-check. Always reproduce first.
- Do NOT fix symptoms. Find the root cause.
- If stuck after 3 iterations, escalate as potential fundamental problem.
</Debug_Protocol>

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
