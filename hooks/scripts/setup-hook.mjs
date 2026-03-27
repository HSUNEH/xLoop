// Setup: Runs once on plugin install — create .xloop/ directories
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

console.log('hook success: xLoop setup complete')
