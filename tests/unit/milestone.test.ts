import { describe, it, expect } from 'vitest'
import { getNextMilestone, completeMilestone, getMilestoneProgress } from '../../src/milestone.js'
import { createProjectSpec } from '../../src/interview.js'

describe('milestone', () => {
  const spec = createProjectSpec({
    features: [
      { id: 'f1', name: 'Feature 1', priority: 'P0', status: 'pending' },
      { id: 'f2', name: 'Feature 2', priority: 'P1', status: 'pending' }
    ],
    milestones: [
      { id: 'ms1', features: ['f1'], dependsOn: [], description: 'Milestone 1' },
      { id: 'ms2', features: ['f2'], dependsOn: ['ms1'], description: 'Milestone 2' }
    ]
  })

  it('getNextMilestone returns first available', () => {
    const next = getNextMilestone(spec)
    expect(next).not.toBeNull()
    expect(next!.id).toBe('ms1')
  })

  it('completeMilestone marks features done', () => {
    const updated = completeMilestone(spec, 'ms1')
    expect(updated.features.find(f => f.id === 'f1')!.status).toBe('done')
  })

  it('respects dependencies', () => {
    expect(getNextMilestone(spec)!.id).toBe('ms1')
  })

  it('returns ms2 after ms1 completed', () => {
    const updated = completeMilestone(spec, 'ms1')
    expect(getNextMilestone(updated)!.id).toBe('ms2')
  })

  it('getMilestoneProgress correct percentages', () => {
    const progress = getMilestoneProgress(spec)
    expect(progress.completed).toEqual([])
    expect(progress.remaining).toEqual(['ms1', 'ms2'])
    expect(progress.percentage).toBe(0)
  })

  it('progress after completing one', () => {
    const updated = completeMilestone(spec, 'ms1')
    const progress = getMilestoneProgress(updated)
    expect(progress.completed).toEqual(['ms1'])
    expect(progress.percentage).toBe(50)
  })

  it('completeMilestone is immutable', () => {
    const updated = completeMilestone(spec, 'ms1')
    expect(spec.features[0]!.status).toBe('pending')
    expect(updated.features[0]!.status).toBe('done')
  })

  it('returns null when all done', () => {
    let s = completeMilestone(spec, 'ms1')
    s = completeMilestone(s, 'ms2')
    expect(getNextMilestone(s)).toBeNull()
  })

  it('handles empty milestones', () => {
    const empty = createProjectSpec()
    expect(getNextMilestone(empty)).toBeNull()
    expect(getMilestoneProgress(empty).percentage).toBe(0)
  })
})
