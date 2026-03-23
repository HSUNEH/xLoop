import { describe, it, expect } from 'vitest'
import { assessComplexity } from '../../src/gate.js'

describe('assessComplexity', () => {
  describe('heuristic — simple tasks', () => {
    it('detects "fix" keyword as score 1', () => {
      const result = assessComplexity('fix the typo in README.md')
      expect(result.score).toBe(1)
      expect(result.method).toBe('heuristic')
    })

    it('detects "update" keyword as score 1', () => {
      const result = assessComplexity('update the version in package.json')
      expect(result.score).toBe(1)
      expect(result.method).toBe('heuristic')
    })

    it('detects "rename" keyword as score 1', () => {
      const result = assessComplexity('rename the function to camelCase')
      expect(result.score).toBe(1)
      expect(result.method).toBe('heuristic')
    })

    it('detects "translate" keyword as score 1', () => {
      const result = assessComplexity('translate this to Korean')
      expect(result.score).toBe(1)
      expect(result.method).toBe('heuristic')
    })

    it('detects "typo" keyword as score 1', () => {
      const result = assessComplexity('there is a typo here')
      expect(result.score).toBe(1)
      expect(result.method).toBe('heuristic')
    })
  })

  describe('heuristic — complex tasks', () => {
    it('detects "refactor" keyword as score 3', () => {
      const result = assessComplexity('refactor the authentication system')
      expect(result.score).toBe(3)
      expect(result.method).toBe('heuristic')
    })

    it('detects "design" keyword as score 3', () => {
      const result = assessComplexity('design a new caching layer')
      expect(result.score).toBe(3)
      expect(result.method).toBe('heuristic')
    })

    it('detects "architect" keyword as score 3', () => {
      const result = assessComplexity('architect the microservice boundary')
      expect(result.score).toBe(3)
      expect(result.method).toBe('heuristic')
    })

    it('detects "migrate" keyword as score 3', () => {
      const result = assessComplexity('migrate the database to PostgreSQL')
      expect(result.score).toBe(3)
      expect(result.method).toBe('heuristic')
    })
  })

  describe('heuristic — single file path biases toward simple', () => {
    it('file path with simple keyword returns score 1', () => {
      const result = assessComplexity('fix src/state.ts')
      expect(result.score).toBe(1)
    })
  })

  describe('micro-assessment — uncertain cases', () => {
    it('falls back to haiku method when uncertain', () => {
      const result = assessComplexity('do something with the code')
      expect(result.method).toBe('haiku')
    })

    it('vague multi-line prompt gets higher score', () => {
      const result = assessComplexity(
        'I want to improve the overall performance\noptimize the queries\nrestructure the modules\nand reconsider the approach'
      )
      expect(result.score).toBeGreaterThanOrEqual(2)
    })

    it('short prompt with file path gets lower score', () => {
      const result = assessComplexity('change src/index.ts')
      expect(result.score).toBeLessThanOrEqual(2)
    })
  })

  describe('return type', () => {
    it('returns score, method, and details', () => {
      const result = assessComplexity('fix the bug')
      expect(result).toHaveProperty('score')
      expect(result).toHaveProperty('method')
      expect(result).toHaveProperty('details')
      expect([1, 2, 3]).toContain(result.score)
      expect(['heuristic', 'haiku']).toContain(result.method)
      expect(typeof result.details).toBe('string')
    })
  })
})
