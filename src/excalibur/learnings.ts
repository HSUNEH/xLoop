import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const LEARNINGS_DIR = '.xloop/learnings'

export interface LearningEntry {
  loopId: number
  technical: string[]
  process: string[]
  quality: string[]
  timestamp: string
}

export function saveLearnings(entry: LearningEntry): string {
  const dir = LEARNINGS_DIR
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })

  const path = join(dir, `loop-${entry.loopId}.json`)
  writeFileSync(path, JSON.stringify(entry, null, 2), 'utf-8')
  return path
}

export function loadLearnings(loopId: number): LearningEntry | null {
  const path = join(LEARNINGS_DIR, `loop-${loopId}.json`)
  if (!existsSync(path)) return null
  return JSON.parse(readFileSync(path, 'utf-8')) as LearningEntry
}

export function loadAllLearnings(): LearningEntry[] {
  if (!existsSync(LEARNINGS_DIR)) return []

  return readdirSync(LEARNINGS_DIR)
    .filter(f => f.startsWith('loop-') && f.endsWith('.json'))
    .map(f => JSON.parse(readFileSync(join(LEARNINGS_DIR, f), 'utf-8')) as LearningEntry)
    .sort((a, b) => a.loopId - b.loopId)
}

export function summarizeLearnings(entries: LearningEntry[]): string {
  if (entries.length === 0) return 'No prior learnings.'

  const latest = entries[entries.length - 1]!
  return [
    `Prior learnings from ${entries.length} loops:`,
    `Technical: ${latest.technical.join('; ')}`,
    `Process: ${latest.process.join('; ')}`,
    `Quality: ${latest.quality.join('; ')}`
  ].join('\n')
}
