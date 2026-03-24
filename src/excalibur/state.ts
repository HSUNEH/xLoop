import { readState, writeState } from '../state.js'

export interface CompletedLoop {
  loop: number
  milestone: string
  plan: string
  report: string
  learnings: string
}

export interface ActiveLane {
  lane: string
  milestone: string
  status: 'pending' | 'in_progress' | 'completed'
}

export interface ExcaliburState {
  active: boolean
  projectSpec: string
  currentLoop: number
  activeLanes: ActiveLane[]
  completedLoops: CompletedLoop[]
  testMode: 'B' | 'C'
  parallelEnabled: boolean
  startedAt: string
  lastActivity: string
}

const MODE = 'excalibur'

export function readExcaliburState(sessionId: string): ExcaliburState | null {
  const state = readState(sessionId, MODE)
  return state as ExcaliburState | null
}

export function writeExcaliburState(sessionId: string, state: ExcaliburState): void {
  writeState(sessionId, MODE, { ...state, lastActivity: new Date().toISOString() })
}

export function getProjectProgress(state: ExcaliburState): {
  completedMilestones: number
  totalMilestones: number
  percentage: number
} {
  const completed = state.completedLoops.length
  const active = state.activeLanes.length
  const total = completed + active
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0

  return { completedMilestones: completed, totalMilestones: total, percentage }
}
