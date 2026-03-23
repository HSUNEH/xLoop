import { describe, it, expect } from 'vitest'
import { generatePrd } from '../../src/prd.js'

describe('generatePrd', () => {
  it('returns valid PRD structure', () => {
    const prd = generatePrd('build a chat app')
    expect(prd).toHaveProperty('project')
    expect(prd).toHaveProperty('phase')
    expect(prd).toHaveProperty('stories')
    expect(Array.isArray(prd.stories)).toBe(true)
  })

  it('generates project name from task', () => {
    const prd = generatePrd('Build a Real-Time Chat App!')
    expect(prd.project).toBe('build-a-real-time-chat-app')
  })

  it('creates 1-story scaffold without LLM', () => {
    const prd = generatePrd('implement login')
    expect(prd.stories).toHaveLength(1)
    expect(prd.stories[0]!.id).toBe('US-001')
    expect(prd.stories[0]!.passes).toBe(false)
  })

  it('story has acceptance criteria array', () => {
    const prd = generatePrd('fix the bug')
    expect(Array.isArray(prd.stories[0]!.acceptanceCriteria)).toBe(true)
    expect(prd.stories[0]!.acceptanceCriteria.length).toBeGreaterThan(0)
  })

  it('story title is derived from task', () => {
    const prd = generatePrd('add user authentication')
    expect(prd.stories[0]!.title).toContain('add user authentication')
  })

  it('handles empty task gracefully', () => {
    const prd = generatePrd('')
    expect(prd.project).toBe('unnamed-project')
    expect(prd.stories).toHaveLength(1)
  })

  it('with useLlm option still returns valid structure', () => {
    const prd = generatePrd('complex task', { useLlm: true })
    expect(prd).toHaveProperty('project')
    expect(prd.stories).toHaveLength(1)
  })

  it('phase defaults to Phase 1', () => {
    const prd = generatePrd('anything')
    expect(prd.phase).toBe('Phase 1')
  })
})
