import { describe, it, expect } from 'vitest'
import { LLMBridge, HeuristicProvider, CostTracker } from '../../src/llm-bridge.js'

describe('CostTracker', () => {
  it('tracks token usage', () => {
    const tracker = new CostTracker()
    tracker.record({ provider: 'test', model: 'haiku', tokensUsed: 100 })
    expect(tracker.totalTokens()).toBe(100)
  })

  it('accumulates multiple records', () => {
    const tracker = new CostTracker()
    tracker.record({ provider: 'test', model: 'haiku', tokensUsed: 100 })
    tracker.record({ provider: 'test', model: 'sonnet', tokensUsed: 200 })
    expect(tracker.totalTokens()).toBe(300)
  })

  it('respects budget', () => {
    const tracker = new CostTracker(500)
    tracker.record({ provider: 'test', model: 'haiku', tokensUsed: 400 })
    expect(tracker.withinBudget(50)).toBe(true)
    expect(tracker.withinBudget(200)).toBe(false)
  })

  it('infinite budget by default', () => {
    const tracker = new CostTracker()
    tracker.record({ provider: 'test', model: 'haiku', tokensUsed: 999999 })
    expect(tracker.withinBudget(999999)).toBe(true)
  })

  it('provides summary', () => {
    const tracker = new CostTracker()
    tracker.record({ provider: 'test', model: 'haiku', tokensUsed: 100 })
    const summary = tracker.summary()
    expect(summary.totalTokens).toBe(100)
    expect(summary.totalCalls).toBe(1)
    expect(summary.entries).toHaveLength(1)
  })
})

describe('HeuristicProvider', () => {
  it('is always available', async () => {
    const provider = new HeuristicProvider()
    expect(await provider.available()).toBe(true)
  })

  it('returns heuristic result with zero tokens', async () => {
    const provider = new HeuristicProvider()
    const result = await provider.complete({ prompt: 'test input' })
    expect(result.provider).toBe('heuristic')
    expect(result.tokensUsed).toBe(0)
    expect(result.text).toContain('[heuristic]')
  })
})

describe('LLMBridge', () => {
  it('falls through to heuristic', async () => {
    const bridge = new LLMBridge([new HeuristicProvider()])
    const result = await bridge.complete({ prompt: 'test' })
    expect(result.provider).toBe('heuristic')
  })

  it('tracks costs after completion', async () => {
    const bridge = new LLMBridge([new HeuristicProvider()])
    await bridge.complete({ prompt: 'test' })
    expect(bridge.getCostTracker().summary().totalCalls).toBe(1)
  })

  it('skips unavailable providers', async () => {
    const unavailable = { name: 'u', available: async () => false, complete: async () => { throw new Error('x') } }
    const bridge = new LLMBridge([unavailable, new HeuristicProvider()])
    const result = await bridge.complete({ prompt: 'test' })
    expect(result.provider).toBe('heuristic')
  })

  it('throws when all providers fail', async () => {
    const failing = { name: 'f', available: async () => true, complete: async () => { throw new Error('fail') } }
    const bridge = new LLMBridge([failing])
    await expect(bridge.complete({ prompt: 'test' })).rejects.toThrow('All LLM providers failed')
  })
})
