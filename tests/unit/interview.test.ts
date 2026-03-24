import { describe, it, expect } from 'vitest'
import { createProjectSpec, InterviewEngine } from '../../src/interview.js'

describe('createProjectSpec', () => {
  it('creates spec with default values', () => {
    const spec = createProjectSpec()
    expect(spec.name).toBe('')
    expect(spec.testMode).toBe('B')
    expect(spec.features).toEqual([])
    expect(spec.milestones).toEqual([])
  })

  it('applies overrides', () => {
    const spec = createProjectSpec({ name: 'test', testMode: 'C' })
    expect(spec.name).toBe('test')
    expect(spec.testMode).toBe('C')
  })

  it('returns ProjectSpec interface shape', () => {
    const spec = createProjectSpec()
    expect(spec).toHaveProperty('name')
    expect(spec).toHaveProperty('vision')
    expect(spec).toHaveProperty('techStack')
    expect(spec).toHaveProperty('features')
    expect(spec).toHaveProperty('milestones')
    expect(spec).toHaveProperty('testMode')
    expect(spec).toHaveProperty('createdAt')
  })
})

describe('InterviewEngine', () => {
  it('starts with ambiguity 1.0', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    expect(engine.getState().currentAmbiguity).toBe(1.0)
  })

  it('reduces ambiguity after recording answers', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    engine.recordAnswer('What is the goal?', 'Build a todo app with CRUD')
    expect(engine.getState().currentAmbiguity).toBeLessThan(1.0)
  })

  it('targets weakest dimension', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    expect(['goal', 'constraints', 'criteria', 'context']).toContain(engine.getWeakestDimension())
  })

  it('generates deterministic questions without LLM', async () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    const q = await engine.generateQuestion('build a chat app')
    expect(typeof q).toBe('string')
    expect(q.length).toBeGreaterThan(0)
  })

  it('crystallizes to ProjectSpec', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    const spec = engine.crystallize('test', 'test vision')
    expect(spec.name).toBe('test')
    expect(spec.vision).toBe('test vision')
  })

  it('isReady returns false at start', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    expect(engine.isReady()).toBe(false)
  })

  it('tracks rounds immutably', () => {
    const engine = new InterviewEngine({ projectType: 'greenfield' })
    const state1 = engine.getState()
    engine.recordAnswer('Q1?', 'A1')
    const state2 = engine.getState()
    expect(state1.rounds).toHaveLength(0)
    expect(state2.rounds).toHaveLength(1)
  })
})
