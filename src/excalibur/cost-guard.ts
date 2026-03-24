import type { CostTracker } from '../llm-bridge.js'

export interface CostGuardConfig {
  maxTokensPerLoop: number    // default: 50000
  maxTokensPerSession: number // default: 500000
  maxLoops: number            // default: 10
}

export const DEFAULT_COST_GUARD: CostGuardConfig = {
  maxTokensPerLoop: 50_000,
  maxTokensPerSession: 500_000,
  maxLoops: 10
}

export function checkCostGuard(
  tracker: CostTracker,
  currentLoop: number,
  config: CostGuardConfig = DEFAULT_COST_GUARD
): { allowed: boolean; reason?: string } {
  if (currentLoop >= config.maxLoops) {
    return { allowed: false, reason: `Max loops reached (${config.maxLoops})` }
  }

  const total = tracker.totalTokens()
  if (total >= config.maxTokensPerSession) {
    return { allowed: false, reason: `Session token budget exceeded (${total}/${config.maxTokensPerSession})` }
  }

  return { allowed: true }
}
