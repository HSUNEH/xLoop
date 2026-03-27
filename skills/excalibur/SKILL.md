---
name: excalibur
description: The essence of xLoop — full project orchestration from interview to completion
level: 5
---

# Excalibur — Project-Level Orchestrator

<Purpose>
One command to orchestrate an entire project. Deep Interview creates a perfect spec with the user, then a big loop of (Ralplan + Ralph + Eval) iterates milestone by milestone until the project is complete.
</Purpose>

<Use_When>
- User says "excalibur" or wants full project orchestration
- Project needs structured planning before implementation
- Multiple milestones with dependencies
</Use_When>

<Do_Not_Use_When>
- Single task or quick fix — Complexity Gate routes to executor or ralph
- User just wants planning without execution — use ralplan
- User just wants implementation without planning — use ralph
</Do_Not_Use_When>

<Phase_0a_Office_Hours>
<!-- Inspired by: gstack /office-hours (https://github.com/garrytan/gstack) -->
Before diving into spec creation, reframe the project at a product level.

**Office Hours Questions** (ask one at a time):
- "Why does this need to exist? What problem are you solving?"
- "Who is the core user? What does their day look like without this?"
- "What existing alternatives have you considered? Why aren't they enough?"
- "What is the single most important thing this must do on day one?"
- "What would make you say 'this failed' six months from now?"

**Rules**:
- Push back on framing — don't just accept feature requests
- If the user's idea can be solved simpler, say so
- Output: refined problem statement + success criteria
- User says "enough reframing" or answers feel solid → proceed to Deep Interview
- User says "skip" → go directly to Deep Interview
</Phase_0a_Office_Hours>

<Phase_0b_Deep_Interview>
Invokes the `deep-interview` skill to co-create a project spec with the user, informed by the reframed problem statement from Office Hours.

**Rules**:
- One question at a time — never batch questions
- Explore codebase before asking user about it
- Build on answers — each question informed by previous
- User terminates with "enough", "start", or "let's go"

**Output**: `project-spec.json` with features, milestones, dependencies, design themes.
Saved to `.xloop/specs/project-spec.json`.

User confirms: "This spec looks good? [Y/modify/cancel]"
</Phase_0b_Deep_Interview>

<Big_Loop>
Each iteration handles ONE milestone. Does not plan the whole project at once.

```
Big Loop #N (Milestone M{N}):
  │
  ├── Ralplan: Plan THIS milestone only
  │   - Receives: project-spec.json + current milestone + previous learnings
  │   - 4-agent consensus (Planner + Researcher + Architect + Critic)
  │   - Output: plan-m{N}.md + prd-m{N}.json
  │
  ├── Ralph: Implement THIS milestone's stories
  │   - PRD-driven, story-by-story with verification
  │   - Parallel execution for independent tasks
  │
  ├── Eval: Check progress
  │   - Auto-verification (5 metrics)
  │   - Browser QA: if available, test the running app in a real browser
  │   - Update project-spec.json feature statuses
  │   - Sprint Retro: what worked, what didn't, what to change
  │   - Generate learnings → .xloop/learnings/loop-{N}.json
  │
  └── Checkpoint (mode-dependent):
      Mode B: Full review — user chooses: proceed / modify spec / upgrade / stop
      Mode C: 10-second checkpoint — input = modify, no input = auto-proceed
```
</Big_Loop>

<Eval_Enhanced>
<!-- Inspired by: gstack /browse, /qa, /retro (https://github.com/garrytan/gstack) -->

**Browser QA** (optional — when the project has a UI):
- Launch the app and verify key user flows in a real browser
- Check visual rendering, navigation, form submissions
- If browser tools are unavailable, fall back to code-level verification only

**Sprint Retro** (after every milestone):
- What went well? (keep doing)
- What went wrong? (stop doing)
- What to try next? (experiment)
- Retro findings are merged into learnings for the next Ralplan
</Eval_Enhanced>

<Learnings>
After each big loop, auto-generate learnings:
- Technical: which libraries/patterns worked or didn't
- Process: story ordering, parallelization effectiveness
- Quality: which metrics were missed and why

Stored in `.xloop/learnings/loop-{N}.json`.
Next Ralplan receives previous learnings as context.
Learnings older than 5 loops are auto-archived.
</Learnings>

<Milestone_Parallelization>
When multiple milestones have all dependencies satisfied:
- Analyze `depends_on` in project-spec.json
- Independent milestones can run in parallel (Lane A + Lane B)
- Conflict detection: if both lanes modify same files → sequential fallback
- Mode B: ask user "M2 and M3 are independent. Parallel?"
- Mode C: auto-parallel with conflict fallback
</Milestone_Parallelization>

<Test_Modes>
Selected during `xloop setup`, stored in `.xloop-config.json`.

**Mode B (semi-auto)**: Full review checkpoint after each milestone.
User sees progress report + options: proceed / modify spec / upgrade harness / stop.

**Mode C (full-auto)**: 10-second checkpoint after each milestone.
No input → auto-proceed. Input → process modification.
Safety: max 3 upgrade cycles per session, must improve ≥1 metric per cycle.
After 3rd upgrade → forces Mode B.
</Test_Modes>

<State>
```json
// .xloop/state/sessions/{id}/excalibur-state.json
{
  "active": true,
  "project_spec": ".xloop/specs/project-spec.json",
  "current_loop": 2,
  "active_lanes": [
    { "lane": "A", "milestone": "M2", "status": "in_progress" }
  ],
  "completed_loops": [
    { "loop": 1, "milestone": "M1", "plan": "...", "report": "...", "learnings": "..." }
  ],
  "test_mode": "B",
  "parallel_enabled": true
}
```
</State>

<Resume>
`xloop excalibur --resume` continues from current milestone.
Detects existing excalibur-state.json and asks: "Resume from M{N}? [Y/new/cancel]"
</Resume>

<CLI>
```
xloop excalibur <description>       # New project
xloop excalibur --resume             # Continue existing
xloop excalibur --status             # Show progress
xloop excalibur --skip-interview     # Use existing spec
```
</CLI>
