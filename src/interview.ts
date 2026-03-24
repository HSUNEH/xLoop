import type { LLMBridge } from './llm-bridge.js'

interface Feature {
  id: string
  name: string
  priority: 'P0' | 'P1' | 'P2'
  status: 'pending' | 'done'
}

interface Milestone {
  id: string
  features: string[]
  dependsOn: string[]
  description: string
}

interface ProjectSpec {
  name: string
  vision: string
  targetUsers: string
  techStack: string[]
  features: Feature[]
  constraints: string[]
  design: { theme: string; tone: string }
  milestones: Milestone[]
  testMode: 'B' | 'C'
  createdAt: string
}

export function createProjectSpec(overrides: Partial<ProjectSpec> = {}): ProjectSpec {
  return {
    name: '',
    vision: '',
    targetUsers: '',
    techStack: [],
    features: [],
    constraints: [],
    design: { theme: '', tone: '' },
    milestones: [],
    testMode: 'B',
    createdAt: new Date().toISOString(),
    ...overrides
  }
}

export type InterviewDimension = 'goal' | 'constraints' | 'criteria' | 'context'

export interface InterviewRound {
  round: number
  dimension: InterviewDimension
  question: string
  answer: string
  scores: Record<InterviewDimension, number>
  ambiguity: number
}

export interface InterviewState {
  rounds: InterviewRound[]
  currentAmbiguity: number
  projectType: 'greenfield' | 'brownfield'
}

export class InterviewEngine {
  private state: InterviewState
  private bridge: LLMBridge | null
  private threshold: number

  constructor(options: {
    projectType: 'greenfield' | 'brownfield'
    bridge?: LLMBridge
    threshold?: number
  }) {
    this.state = {
      rounds: [],
      currentAmbiguity: 1.0,
      projectType: options.projectType
    }
    this.bridge = options.bridge ?? null
    this.threshold = options.threshold ?? 0.2
  }

  getWeakestDimension(): InterviewDimension {
    if (this.state.rounds.length === 0) return 'goal'

    const lastRound = this.state.rounds[this.state.rounds.length - 1]!
    const scores = lastRound.scores

    const dimensions: InterviewDimension[] = this.state.projectType === 'brownfield'
      ? ['goal', 'constraints', 'criteria', 'context']
      : ['goal', 'constraints', 'criteria']

    let weakest: InterviewDimension = dimensions[0]!
    let lowestScore = Infinity

    for (const dim of dimensions) {
      const score = scores[dim] ?? 0
      if (score < lowestScore) {
        lowestScore = score
        weakest = dim
      }
    }

    return weakest
  }

  async generateQuestion(idea: string): Promise<string> {
    const weakest = this.getWeakestDimension()

    if (!this.bridge) {
      const templates: Record<InterviewDimension, string[]> = {
        goal: ['What specific outcome do you want?', 'What does success look like?'],
        constraints: ['What are the boundaries?', 'What should this NOT do?'],
        criteria: ['How will we verify this works?', 'What test would prove success?'],
        context: ['How does this fit with existing code?', 'What existing patterns should we follow?']
      }
      const options = templates[weakest]!
      return options[this.state.rounds.length % options.length]!
    }

    try {
      const transcript = this.state.rounds
        .map(r => `Q: ${r.question}\nA: ${r.answer}`)
        .join('\n\n')

      const result = await this.bridge.complete({
        prompt: `Generate ONE targeted question for dimension "${weakest}".\nIdea: ${idea}\nTranscript so far:\n${transcript}\nRespond with just the question.`,
        systemPrompt: 'You are a Socratic interviewer. Ask ONE question that exposes assumptions. Target the weakest clarity dimension.',
        model: 'haiku',
        maxTokens: 200,
        temperature: 0.7
      })

      return result.text.trim() || `What specifically do you mean about the ${weakest}?`
    } catch {
      return `Could you clarify the ${weakest} aspect?`
    }
  }

  recordAnswer(question: string, answer: string): InterviewRound {
    const round = this.state.rounds.length + 1
    const dimension = this.getWeakestDimension()

    const scores: Record<InterviewDimension, number> = {
      goal: this.state.rounds.length > 0
        ? (this.state.rounds[this.state.rounds.length - 1]!.scores.goal)
        : 0.3,
      constraints: this.state.rounds.length > 0
        ? (this.state.rounds[this.state.rounds.length - 1]!.scores.constraints)
        : 0.2,
      criteria: this.state.rounds.length > 0
        ? (this.state.rounds[this.state.rounds.length - 1]!.scores.criteria)
        : 0.1,
      context: this.state.rounds.length > 0
        ? (this.state.rounds[this.state.rounds.length - 1]!.scores.context)
        : 0.5
    }

    scores[dimension] = Math.min((scores[dimension] ?? 0) + 0.15 + (answer.length > 100 ? 0.1 : 0), 0.95)

    const weights = this.state.projectType === 'brownfield'
      ? { goal: 0.35, constraints: 0.25, criteria: 0.25, context: 0.15 }
      : { goal: 0.40, constraints: 0.30, criteria: 0.30, context: 0 }

    const clarity = Object.entries(weights).reduce(
      (sum, [dim, weight]) => sum + (scores[dim as InterviewDimension] ?? 0) * weight,
      0
    )

    const ambiguity = 1 - clarity

    const entry: InterviewRound = {
      round,
      dimension,
      question,
      answer,
      scores,
      ambiguity
    }

    this.state = {
      ...this.state,
      rounds: [...this.state.rounds, entry],
      currentAmbiguity: ambiguity
    }

    return entry
  }

  isReady(): boolean {
    return this.state.currentAmbiguity <= this.threshold
  }

  getState(): InterviewState {
    return this.state
  }

  crystallize(name: string, vision: string): ProjectSpec {
    return createProjectSpec({
      name,
      vision,
      testMode: 'B',
      createdAt: new Date().toISOString()
    })
  }
}

export type { ProjectSpec, Feature, Milestone }
