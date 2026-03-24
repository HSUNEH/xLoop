import { describe, it, expect } from 'vitest'
import { getProjectProgress } from '../../src/excalibur/index.js'
import { checkCostGuard, DEFAULT_COST_GUARD } from '../../src/excalibur/cost-guard.js'
import { shouldAutoProceed, createCheckpointSummary } from '../../src/excalibur/checkpoint.js'
import { CostTracker } from '../../src/llm-bridge.js'
import type { ExcaliburState } from '../../src/excalibur/index.js'

describe('excalibur state', () => {
  it('getProjectProgress returns correct shape', () => {
    const state: ExcaliburState = {
      active: true, projectSpec: '', currentLoop: 0,
      activeLanes: [{ lane: 'main', milestone: 'ms1', status: 'in_progress' }],
      completedLoops: [], testMode: 'B', parallelEnabled: false,
      startedAt: new Date().toISOString(), lastActivity: new Date().toISOString()
    }
    const progress = getProjectProgress(state)
    expect(progress.completedMilestones).toBe(0)
    expect(progress.totalMilestones).toBe(1)
    expect(progress.percentage).toBe(0)
  })

  it('progress with completed loops', () => {
    const state: ExcaliburState = {
      active: true, projectSpec: '', currentLoop: 2,
      activeLanes: [{ lane: 'main', milestone: 'ms3', status: 'pending' }],
      completedLoops: [
        { loop: 0, milestone: 'ms1', plan: '', report: '', learnings: '' },
        { loop: 1, milestone: 'ms2', plan: '', report: '', learnings: '' }
      ],
      testMode: 'C', parallelEnabled: true,
      startedAt: new Date().toISOString(), lastActivity: new Date().toISOString()
    }
    const progress = getProjectProgress(state)
    expect(progress.completedMilestones).toBe(2)
    expect(progress.totalMilestones).toBe(3)
    expect(progress.percentage).toBe(67)
  })
})

describe('cost guard', () => {
  it('allows within limits', () => {
    const tracker = new CostTracker()
    expect(checkCostGuard(tracker, 0).allowed).toBe(true)
  })

  it('blocks at max loops', () => {
    const tracker = new CostTracker()
    const result = checkCostGuard(tracker, DEFAULT_COST_GUARD.maxLoops)
    expect(result.allowed).toBe(false)
    expect(result.reason).toContain('Max loops')
  })

  it('blocks on token budget exceeded', () => {
    const tracker = new CostTracker()
    tracker.record({ provider: 'test', model: 'opus', tokensUsed: 600000 })
    const result = checkCostGuard(tracker, 0)
    expect(result.allowed).toBe(false)
    expect(result.reason).toContain('budget exceeded')
  })
})

describe('checkpoint', () => {
  it('autohunt auto-proceeds on good metrics', () => {
    expect(shouldAutoProceed(
      { mode: 'autohunt', autoDelayMs: 10000 },
      { testPassRate: 0.8, typecheck: true, buildSuccess: true, coverage: 0.7, acceptanceMet: 0.9 }
    )).toBe(true)
  })

  it('grab mode never auto-proceeds', () => {
    expect(shouldAutoProceed(
      { mode: 'grab', autoDelayMs: 10000 },
      { testPassRate: 1.0, typecheck: true, buildSuccess: true, coverage: 1.0, acceptanceMet: 1.0 }
    )).toBe(false)
  })

  it('summary includes all metrics', () => {
    const summary = createCheckpointSummary(1, {
      testPassRate: 0.85, typecheck: true, buildSuccess: true, coverage: 0.72, acceptanceMet: 0.9
    })
    expect(summary).toContain('Loop 1')
    expect(summary).toContain('PASS')
  })
})
