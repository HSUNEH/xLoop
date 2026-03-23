import { createHash } from 'node:crypto'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'

const CHECKSUM_PATH = '.xloop-checksum'

function computeSha256(filePath: string): string {
  const content = readFileSync(filePath, 'utf-8')
  return createHash('sha256').update(content).digest('hex')
}

export function verifyChecksum(principlesPath: string): { valid: boolean; expected: string; actual: string } {
  if (!existsSync(principlesPath)) {
    return { valid: false, expected: '', actual: '[file not found]' }
  }

  if (!existsSync(CHECKSUM_PATH)) {
    return { valid: false, expected: '[no checksum file]', actual: computeSha256(principlesPath) }
  }

  const expected = readFileSync(CHECKSUM_PATH, 'utf-8').trim()
  const actual = computeSha256(principlesPath)

  return { valid: expected === actual, expected, actual }
}

export function updateChecksum(principlesPath: string): string {
  const hash = computeSha256(principlesPath)
  writeFileSync(CHECKSUM_PATH, hash, 'utf-8')
  return hash
}
