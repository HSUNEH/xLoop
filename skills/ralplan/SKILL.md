---
name: ralplan
description: 4-agent consensus planning with integrated research — plans one milestone at a time
level: 4
---

# Ralplan — 4-Agent Consensus with Integrated Research

<Purpose>
Ralplan creates implementation plans through iterative consensus between Planner, Researcher, Architect, and Critic. Research happens WITHIN the planning loop — targeted by context, not front-loaded blindly. Plans one milestone at a time, not the whole project at once.
</Purpose>

<Use_When>
- Task requires structured planning before implementation
- User says "ralplan", "plan this", "design this"
- Work is complex enough to benefit from multi-perspective review
</Use_When>

<Do_Not_Use_When>
- Full project orchestration — use `excalibur` (which invokes ralplan internally)
- Quick fix with obvious scope — delegate to executor or use ralph directly
- User wants to start coding immediately — use ralph
</Do_Not_Use_When>

<Agents>
1. **Planner** (Opus): Creates plans, identifies research needs, incorporates findings
2. **Researcher** (Sonnet): Investigates specific questions identified by other agents
3. **Architect** (Opus): Steelman counterargument, tradeoff tensions, synthesis path
4. **Critic** (Opus): Principle-option consistency, alternative depth, risk/verification rigor
</Agents>

<Steps>
1. **Planner**: Initial plan draft + identifies specific research questions (not broad topics)

2. **Researcher**: Investigates Planner's questions in parallel (web, arxiv, docs)
   - Results cached and shared across the ralplan loop
   - Each source adapter fails independently (returns partial results, not error)

3. **Planner**: Incorporates research findings into revised plan + RALPLAN-DR summary
   - Principles (3-5), Decision Drivers (top 3), Viable Options (>=2)

4. **Architect**: Reviews for architectural soundness
   - Steelman counterargument against favored option
   - At least one tradeoff tension + synthesis path
   - Can request additional research → Researcher investigates → Architect re-evaluates

5. **Critic**: Evaluates against quality criteria
   - Principle-option consistency, fair alternative exploration
   - Risk mitigations specific and actionable
   - 90%+ acceptance criteria are testable
   - Can request additional research → Researcher investigates → Critic re-evaluates

6. **If Critic rejects**: Planner revises (may request new research) → back to Step 4
   - Max 5 iterations total
   - Max 2 research requests per agent per iteration

7. **On approval**: Save plan to `.xloop/plans/`, output ADR

</Steps>

<Research_Protocol>
- Any agent can emit `research_needed` with specific questions
- Researcher runs in parallel across multiple questions
- Results injected back into requesting agent's context
- Findings cached across loop iterations (avoid re-fetching)
- Zero usable findings → flag as "unresearched — proceed with assumptions"
</Research_Protocol>

<Milestone_Scoping>
When invoked within excalibur:
- Receives project-spec.json + current milestone + previous learnings
- Plans ONLY this milestone's features (ignore future milestones)
- Builds on already-implemented code from previous milestones
- Does NOT plan the whole project at once
</Milestone_Scoping>

<Output>
- Plan document (.md) saved to `.xloop/plans/{task}-{timestamp}.md`
- RALPLAN-DR summary (Principles, Decision Drivers, Options)
- ADR (Decision, Drivers, Alternatives considered, Why chosen, Consequences)
</Output>
