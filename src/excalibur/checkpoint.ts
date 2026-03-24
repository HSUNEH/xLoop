import type { EvalMetrics } from './orchestrator.js'

export interface CheckpointConfig {
  mode: 'autohunt' | 'grab'
  autoDelayMs: number  // autohunt: time before auto-proceed (default 10000)
}

export interface CheckpointResult {
  action: 'continue' | 'pause' | 'abort'
  userFeedback?: string
}

export function shouldAutoProceed(config: CheckpointConfig, metrics: EvalMetrics): boolean {
  if (config.mode === 'autohunt') {
    return metrics.testPassRate >= 0.6 && metrics.buildSuccess
  }
  return false // grab mode always pauses
}

export function createCheckpointSummary(loop: number, metrics: EvalMetrics): string {
  return [
    `Loop ${loop} Checkpoint:`,
    `  Test Pass Rate: ${(metrics.testPassRate * 100).toFixed(1)}%`,
    `  Typecheck: ${metrics.typecheck ? 'PASS' : 'FAIL'}`,
    `  Build: ${metrics.buildSuccess ? 'PASS' : 'FAIL'}`,
    `  Coverage: ${(metrics.coverage * 100).toFixed(1)}%`,
    `  Acceptance: ${(metrics.acceptanceMet * 100).toFixed(1)}%`
  ].join('\n')
}
