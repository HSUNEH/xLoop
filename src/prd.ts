import type { LLMBridge } from './llm-bridge.js'

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

export async function generatePrdAsync(
  task: string,
  bridge: LLMBridge,
  options?: { projectName?: string }
): Promise<PrdDocument> {
  const projectName = options?.projectName ?? task
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 40)

  try {
    const result = await bridge.complete({
      prompt: `Break this task into user stories with acceptance criteria.\nTask: ${task}\nRespond as JSON: {"stories":[{"title":"...","description":"...","priority":1,"acceptanceCriteria":["..."]}]}`,
      systemPrompt: 'You are a product manager creating user stories. Be specific and testable.',
      model: 'haiku',
      maxTokens: 1024,
      temperature: 0.3
    })

    const parsed = JSON.parse(result.text) as { stories?: Array<{ title?: string; description?: string; priority?: number; acceptanceCriteria?: string[] }> }
    const stories: PrdStory[] = (parsed.stories ?? []).map((s, i) => ({
      id: `US-${String(i + 1).padStart(3, '0')}`,
      title: s.title ?? task.slice(0, 100),
      description: s.description ?? task,
      priority: s.priority ?? i + 1,
      passes: false,
      acceptanceCriteria: s.acceptanceCriteria ?? ['Task is implemented', 'All tests pass']
    }))

    return {
      project: projectName || 'unnamed-project',
      phase: 'Phase 1',
      stories: stories.length > 0 ? stories : createScaffold(projectName, task).stories
    }
  } catch {
    return createScaffold(projectName, task)
  }
}

export type { PrdDocument, PrdStory }
