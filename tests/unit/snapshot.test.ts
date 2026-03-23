import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createSnapshot, restoreSnapshot, listSnapshots } from '../../src/snapshot.js'
import { existsSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const SNAPSHOTS_DIR = '.xloop/snapshots'
const TEST_VERSION = 'test-0.0.1'

describe('snapshot', () => {
  afterEach(() => {
    const path = join(SNAPSHOTS_DIR, TEST_VERSION)
    if (existsSync(path)) rmSync(path, { recursive: true })
  })

  describe('createSnapshot', () => {
    it('creates snapshot directory with version', () => {
      const path = createSnapshot(TEST_VERSION)
      expect(existsSync(path)).toBe(true)
    })

    it('copies agents/ to snapshot', () => {
      createSnapshot(TEST_VERSION)
      expect(existsSync(join(SNAPSHOTS_DIR, TEST_VERSION, 'agents'))).toBe(true)
    })

    it('copies skills/ to snapshot', () => {
      createSnapshot(TEST_VERSION)
      expect(existsSync(join(SNAPSHOTS_DIR, TEST_VERSION, 'skills'))).toBe(true)
    })
  })

  describe('restoreSnapshot', () => {
    it('returns false for non-existent version', () => {
      expect(restoreSnapshot('nonexistent')).toBe(false)
    })

    it('restores files from snapshot', () => {
      createSnapshot(TEST_VERSION)
      const result = restoreSnapshot(TEST_VERSION)
      expect(result).toBe(true)
    })
  })

  describe('listSnapshots', () => {
    it('returns array', () => {
      const list = listSnapshots()
      expect(Array.isArray(list)).toBe(true)
    })

    it('includes created snapshot', () => {
      createSnapshot(TEST_VERSION)
      const list = listSnapshots()
      expect(list.some(s => s.version === TEST_VERSION)).toBe(true)
    })

    it('has version and date fields', () => {
      createSnapshot(TEST_VERSION)
      const list = listSnapshots()
      const snap = list.find(s => s.version === TEST_VERSION)
      expect(snap).toBeDefined()
      expect(snap!.date).toBeInstanceOf(Date)
    })
  })
})
