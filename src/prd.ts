interface PrdStory {
  id: string
  title: string
  description: string
  priority: number
  passes: boolean
  acceptanceCriteria: string[]
}

interface PrdDocument {
  project: string
  phase: string
  stories: PrdStory[]
}

export function generatePrd(task: string, options?: { useLlm?: boolean }): PrdDocument {
  const projectName = task
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 40)

  if (options?.useLlm) {
    // LLM enrichment path — would call Haiku to break task into stories
    // For now: same as deterministic but marked for future LLM integration
    return createScaffold(projectName, task)
  }

  return createScaffold(projectName, task)
}

function createScaffold(projectName: string, task: string): PrdDocument {
  return {
    project: projectName || 'unnamed-project',
    phase: 'Phase 1',
    stories: [
      {
        id: 'US-001',
        title: task.slice(0, 100),
        description: task,
        priority: 1,
        passes: false,
        acceptanceCriteria: [
          `Task "${task.slice(0, 50)}" is implemented`,
          'All tests pass',
          'TypeScript compiles without errors'
        ]
      }
    ]
  }
}

export type { PrdDocument, PrdStory }
