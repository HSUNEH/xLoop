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

<Phase_0_Deep_Interview>
Invokes the `deep-interview` skill to co-create a project spec with the user.

**Rules**:
- One question at a time — never batch questions
- Explore codebase before asking user about it
- Build on answers — each question informed by previous
- User terminates with "enough", "start", or "let's go"

**Output**: `project-spec.json` with features, milestones, dependencies, design themes.
Saved to `.xloop/specs/project-spec.json`.

User confirms: "This spec looks good? [Y/modify/cancel]"
</Phase_0_Deep_Interview>

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
  │   - Update project-spec.json feature statuses
  │   - Generate learnings → .xloop/learnings/loop-{N}.json
  │
  └── Checkpoint (mode-dependent):
      Mode B: Full review — user chooses: proceed / modify spec / upgrade / stop
      Mode C: 10-second checkpoint — input = modify, no input = auto-proceed
```
</Big_Loop>

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
