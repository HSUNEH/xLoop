import type { ProjectSpec, Milestone } from './interview.js'

export function getNextMilestone(spec: ProjectSpec): Milestone | null {
  const completedFeatureIds = new Set(
    spec.features.filter(f => f.status === 'done').map(f => f.id)
  )

  for (const ms of spec.milestones) {
    const allDepsCompleted = ms.dependsOn.every(depId => {
      const depMilestone = spec.milestones.find(m => m.id === depId)
      if (!depMilestone) return true
      return depMilestone.features.every(fId => completedFeatureIds.has(fId))
    })

    const milestoneComplete = ms.features.every(fId => completedFeatureIds.has(fId))

    if (!milestoneComplete && allDepsCompleted) {
      return ms
    }
  }

  return null
}

export function completeMilestone(spec: ProjectSpec, milestoneId: string): ProjectSpec {
  return {
    ...spec,
    features: spec.features.map(f => {
      const ms = spec.milestones.find(m => m.id === milestoneId)
      if (ms && ms.features.includes(f.id)) {
        return { ...f, status: 'done' as const }
      }
      return f
    })
  }
}

export function getMilestoneProgress(spec: ProjectSpec): {
  completed: string[]
  remaining: string[]
  percentage: number
} {
  const completedFeatureIds = new Set(
    spec.features.filter(f => f.status === 'done').map(f => f.id)
  )

  const completed: string[] = []
  const remaining: string[] = []

  for (const ms of spec.milestones) {
    const done = ms.features.every(fId => completedFeatureIds.has(fId))
    if (done) completed.push(ms.id)
    else remaining.push(ms.id)
  }

  const total = spec.milestones.length
  const percentage = total > 0 ? Math.round((completed.length / total) * 100) : 0

  return { completed, remaining, percentage }
}
