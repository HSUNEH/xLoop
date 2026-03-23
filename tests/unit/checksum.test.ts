import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { verifyChecksum, updateChecksum } from '../../src/checksum.js'
import { writeFileSync, unlinkSync, existsSync } from 'node:fs'

const TEST_FILE = '.test-principles.md'
const CHECKSUM_FILE = '.xloop-checksum'

describe('checksum', () => {
  beforeEach(() => {
    writeFileSync(TEST_FILE, '# Test Principles\n1. Be good\n', 'utf-8')
  })

  afterEach(() => {
    if (existsSync(TEST_FILE)) unlinkSync(TEST_FILE)
    if (existsSync(CHECKSUM_FILE)) unlinkSync(CHECKSUM_FILE)
  })

  describe('updateChecksum', () => {
    it('creates checksum file and returns hash', () => {
      const hash = updateChecksum(TEST_FILE)
      expect(typeof hash).toBe('string')
      expect(hash.length).toBe(64)
      expect(existsSync(CHECKSUM_FILE)).toBe(true)
    })
  })

  describe('verifyChecksum', () => {
    it('returns valid:true when checksum matches', () => {
      updateChecksum(TEST_FILE)
      const result = verifyChecksum(TEST_FILE)
      expect(result.valid).toBe(true)
      expect(result.expected).toBe(result.actual)
    })

    it('returns valid:false when file modified', () => {
      updateChecksum(TEST_FILE)
      writeFileSync(TEST_FILE, '# Modified\n', 'utf-8')
      const result = verifyChecksum(TEST_FILE)
      expect(result.valid).toBe(false)
    })

    it('returns valid:false when file not found', () => {
      const result = verifyChecksum('nonexistent.md')
      expect(result.valid).toBe(false)
      expect(result.actual).toBe('[file not found]')
    })

    it('returns valid:false when checksum file missing', () => {
      const result = verifyChecksum(TEST_FILE)
      expect(result.valid).toBe(false)
      expect(result.expected).toBe('[no checksum file]')
    })
  })
})
