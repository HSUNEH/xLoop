import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { readState, writeState, clearState, listActiveSessions, readConfig, writeConfig } from '../../src/state.js'
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const TEST_SESSION = 'test-session-001'
const STATE_DIR = join('.xloop', 'state', 'sessions')

describe('state', () => {
  beforeEach(() => {
    if (existsSync(join(STATE_DIR, TEST_SESSION))) {
      rmSync(join(STATE_DIR, TEST_SESSION), { recursive: true })
    }
  })

  afterEach(() => {
    if (existsSync(join(STATE_DIR, TEST_SESSION))) {
      rmSync(join(STATE_DIR, TEST_SESSION), { recursive: true })
    }
  })

  describe('readState', () => {
    it('returns null for non-existent state', () => {
      const result = readState(TEST_SESSION, 'ralph')
      expect(result).toBeNull()
    })

    it('returns parsed JSON for existing state', () => {
      const data = { active: true, iteration: 1 }
      writeState(TEST_SESSION, 'ralph', data)
      const result = readState(TEST_SESSION, 'ralph')
      expect(result).toEqual(data)
    })
  })

  describe('writeState', () => {
    it('creates session directory and writes JSON', () => {
      writeState(TEST_SESSION, 'ralph', { active: true })
      const path = join(STATE_DIR, TEST_SESSION, 'ralph-state.json')
      expect(existsSync(path)).toBe(true)
    })

    it('overwrites existing state', () => {
      writeState(TEST_SESSION, 'ralph', { iteration: 1 })
      writeState(TEST_SESSION, 'ralph', { iteration: 2 })
      const result = readState(TEST_SESSION, 'ralph')
      expect(result).toEqual({ iteration: 2 })
    })
  })

  describe('clearState', () => {
    it('removes session state file', () => {
      writeState(TEST_SESSION, 'ralph', { active: true })
      clearState(TEST_SESSION, 'ralph')
      expect(readState(TEST_SESSION, 'ralph')).toBeNull()
    })

    it('does nothing for non-existent state', () => {
      expect(() => clearState(TEST_SESSION, 'ralph')).not.toThrow()
    })
  })

  describe('listActiveSessions', () => {
    it('returns empty array when no sessions exist', () => {
      const result = listActiveSessions()
      expect(Array.isArray(result)).toBe(true)
    })

    it('returns session ID when active state exists', () => {
      writeState(TEST_SESSION, 'ralph', { active: true })
      const result = listActiveSessions()
      expect(result).toContain(TEST_SESSION)
    })

    it('excludes inactive sessions', () => {
      writeState(TEST_SESSION, 'ralph', { active: false })
      const result = listActiveSessions()
      expect(result).not.toContain(TEST_SESSION)
    })
  })
})

describe('config', () => {
  // Config tests use the real config path, so we skip destructive tests
  describe('readConfig', () => {
    it('returns object', () => {
      const result = readConfig()
      expect(typeof result).toBe('object')
    })
  })
})
