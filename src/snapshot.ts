import { existsSync, mkdirSync, cpSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const SNAPSHOTS_DIR = '.xloop/snapshots'
const SNAPSHOT_DIRS = ['agents', 'skills', 'hooks', 'src', 'templates']

export function createSnapshot(version: string): string {
  const snapshotPath = join(SNAPSHOTS_DIR, version)
  mkdirSync(snapshotPath, { recursive: true })

  for (const dir of SNAPSHOT_DIRS) {
    if (existsSync(dir)) {
      cpSync(dir, join(snapshotPath, dir), { recursive: true })
    }
  }

  return snapshotPath
}

export function restoreSnapshot(version: string): boolean {
  const snapshotPath = join(SNAPSHOTS_DIR, version)
  if (!existsSync(snapshotPath)) return false

  for (const dir of SNAPSHOT_DIRS) {
    const source = join(snapshotPath, dir)
    if (existsSync(source)) {
      cpSync(source, dir, { recursive: true, force: true })
    }
  }

  return true
}

export function listSnapshots(): Array<{ version: string; date: Date }> {
  if (!existsSync(SNAPSHOTS_DIR)) return []

  return readdirSync(SNAPSHOTS_DIR)
    .filter(name => {
      const full = join(SNAPSHOTS_DIR, name)
      return statSync(full).isDirectory()
    })
    .map(version => ({
      version,
      date: statSync(join(SNAPSHOTS_DIR, version)).mtime
    }))
    .sort((a, b) => b.date.getTime() - a.date.getTime())
}
