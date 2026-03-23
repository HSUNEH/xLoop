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

export type { ProjectSpec, Feature, Milestone }
