---
name: deep-interview
description: Phase 0 user interview — co-create project spec through guided conversation
level: 3
---

# Deep Interview — Project Spec Co-Creation

<Purpose>
Co-create a comprehensive project specification through guided conversation with the user. One question at a time, building on answers, exploring the codebase before asking about it.
</Purpose>

<Use_When>
- Invoked by `excalibur` as Phase 0
- User wants structured requirements gathering
- Project scope is unclear and needs crystallization
</Use_When>

<Do_Not_Use_When>
- User has a clear, specific task — use Complexity Gate routing
- User already has a spec — use `excalibur --skip-interview`
</Do_Not_Use_When>

<Rules>
1. **One question at a time** — never batch multiple questions
2. **Answer-driven follow-ups** — each question builds on the previous answer
3. **Codebase first** — explore existing code before asking user about patterns/structure
4. **User terminates** — interview ends when user says "enough", "start", "let's go", or similar
5. **No judgment** — accept user's choices, offer alternatives only when asked
</Rules>

<Question_Categories>

**1. Project Vision**
- What is the ultimate goal of this project?
- Who will use this? Target audience?
- What does success look like?

**2. Technical Direction**
- Any tech stack preferences?
- Existing codebase to build on? (explore first, then ask)
- Deployment environment?

**3. Core Features**
- Must-have features? (with priority)
- What must NOT be included?
- Any reference projects or inspirations?

**4. Quality Standards**
- Design theme / visual tone?
- Performance requirements?
- Security level needed?

**5. Process**
- Timeline constraints?
- Confirm test mode (B/C from setup)
- How many milestones to split into?
</Question_Categories>

<Flow>
1. Greet user, explain the interview process briefly
2. Start with Vision category
3. After each answer, decide:
   - Follow up on this topic? → ask deeper
   - Move to next category? → transition naturally
   - User signals readiness? → wrap up
4. Before asking tech questions, spawn explorer agent to scan codebase
5. After all categories covered (or user says "enough"):
   - Synthesize answers into project-spec.json
   - Present spec summary to user
   - User confirms: "Start with this? [Y/modify/cancel]"
</Flow>

<Output>
```json
// .xloop/specs/project-spec.json
{
  "name": "project-name",
  "vision": "...",
  "target_users": "...",
  "tech_stack": ["..."],
  "features": [
    { "id": "F1", "name": "...", "priority": "P0", "status": "pending" }
  ],
  "constraints": ["..."],
  "design": { "theme": "...", "tone": "..." },
  "milestones": [
    { "id": "M1", "features": ["F1", "F2"], "depends_on": [], "description": "MVP" }
  ],
  "test_mode": "B",
  "created_at": "..."
}
```

Key: `milestones` includes `depends_on` for dependency graph analysis.
Features are ordered by priority (P0 > P1 > P2).
</Output>
