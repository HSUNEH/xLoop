// SessionStart: Initialize session state directory
import { mkdirSync, existsSync } from 'node:fs'

const dirs = [
  '.xloop/state/sessions',
  '.xloop/plans',
  '.xloop/research/cache',
  '.xloop/reports',
  '.xloop/snapshots',
  '.xloop/learnings',
  '.xloop/specs'
]

for (const dir of dirs) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
}

console.log('hook success: xLoop session initialized')
