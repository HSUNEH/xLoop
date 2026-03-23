import { describe, it, expect } from 'vitest'
import { selectTier } from '../../src/router.js'

describe('selectTier', () => {
  it('returns haiku for lookup tasks', () => {
    const result = selectTier('lookup')
    expect(result.tier).toBe('haiku')
    expect(result.model).toContain('haiku')
  })

  it('returns haiku for explore tasks', () => {
    const result = selectTier('explore')
    expect(result.tier).toBe('haiku')
  })

  it('returns sonnet for implementation tasks', () => {
    const result = selectTier('implementation')
    expect(result.tier).toBe('sonnet')
    expect(result.model).toContain('sonnet')
  })

  it('returns sonnet for coding tasks', () => {
    const result = selectTier('coding')
    expect(result.tier).toBe('sonnet')
  })

  it('returns sonnet for research tasks', () => {
    const result = selectTier('research')
    expect(result.tier).toBe('sonnet')
  })

  it('returns opus for architecture tasks', () => {
    const result = selectTier('architecture')
    expect(result.tier).toBe('opus')
    expect(result.model).toContain('opus')
  })

  it('returns opus for planning tasks', () => {
    const result = selectTier('planning')
    expect(result.tier).toBe('opus')
  })

  it('returns opus for review tasks', () => {
    const result = selectTier('review')
    expect(result.tier).toBe('opus')
  })

  it('defaults to sonnet for unknown task types', () => {
    const result = selectTier('unknown-task')
    expect(result.tier).toBe('sonnet')
  })

  it('returns model and tier fields', () => {
    const result = selectTier('implementation')
    expect(result).toHaveProperty('model')
    expect(result).toHaveProperty('tier')
    expect(typeof result.model).toBe('string')
  })

  it('default model IDs match expected values', () => {
    expect(selectTier('lookup').model).toBe('claude-haiku-4-5-20251001')
    expect(selectTier('implementation').model).toBe('claude-sonnet-4-6')
    expect(selectTier('architecture').model).toBe('claude-opus-4-6')
  })
})
