import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { homedir } from 'node:os'

const XLOOP_DIR = '.xloop'
const STATE_DIR = join(XLOOP_DIR, 'state', 'sessions')
const CONFIG_PATH = join(
  process.env['CLAUDE_CONFIG_DIR'] ?? join(homedir(), '.claude'),
  '.xloop-config.json'
)

function ensureDir(dirPath: string): void {
  if (!existsSync(dirPath)) {
    mkdirSync(dirPath, { recursive: true })
  }
}

function statePath(sessionId: string, mode: string): string {
  return join(STATE_DIR, sessionId, `${mode}-state.json`)
}

export function readState(sessionId: string, mode: string): unknown {
  const path = statePath(sessionId, mode)
  if (!existsSync(path)) return null
  const raw = readFileSync(path, 'utf-8')
  return JSON.parse(raw) as unknown
}

export function writeState(sessionId: string, mode: string, data: unknown): void {
  const path = statePath(sessionId, mode)
  ensureDir(dirname(path))
  writeFileSync(path, JSON.stringify(data, null, 2), 'utf-8')
}

export function clearState(sessionId: string, mode: string): void {
  const path = statePath(sessionId, mode)
  if (existsSync(path)) {
    unlinkSync(path)
  }
}

export function listActiveSessions(): string[] {
  if (!existsSync(STATE_DIR)) return []

  const sessions: string[] = []
  for (const sessionId of readdirSync(STATE_DIR)) {
    const sessionDir = join(STATE_DIR, sessionId)
    try {
      const files = readdirSync(sessionDir)
      const hasActive = files.some(f => {
        const filePath = join(sessionDir, f)
        const content = JSON.parse(readFileSync(filePath, 'utf-8'))
        return content?.active === true
      })
      if (hasActive) sessions.push(sessionId)
    } catch {
      // skip malformed session directories
    }
  }
  return sessions
}

export function readConfig(): Record<string, unknown> {
  if (!existsSync(CONFIG_PATH)) return {}
  const raw = readFileSync(CONFIG_PATH, 'utf-8')
  return JSON.parse(raw) as Record<string, unknown>
}

export function writeConfig(patch: Record<string, unknown>): void {
  const existing = readConfig()
  const merged = { ...existing, ...patch }
  ensureDir(dirname(CONFIG_PATH))
  writeFileSync(CONFIG_PATH, JSON.stringify(merged, null, 2), 'utf-8')
}
