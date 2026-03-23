import { readConfig } from './state.js'

interface TierResult {
  model: string
  tier: 'haiku' | 'sonnet' | 'opus'
}

const DEFAULT_MODELS: Record<string, string> = {
  haiku: 'claude-haiku-4-5-20251001',
  sonnet: 'claude-sonnet-4-6',
  opus: 'claude-opus-4-6'
}

const TASK_TIER_MAP: Record<string, 'haiku' | 'sonnet' | 'opus'> = {
  lookup: 'haiku',
  explore: 'haiku',
  search: 'haiku',
  implementation: 'sonnet',
  execution: 'sonnet',
  coding: 'sonnet',
  research: 'sonnet',
  verification: 'sonnet',
  debugging: 'sonnet',
  architecture: 'opus',
  planning: 'opus',
  review: 'opus',
  analysis: 'opus',
  critic: 'opus'
}

export function selectTier(taskType: string): TierResult {
  const lower = taskType.toLowerCase()
  const tier = TASK_TIER_MAP[lower] ?? 'sonnet'

  const config = readConfig()
  const palConfig = (config['pal'] ?? {}) as Record<string, string>

  const model = palConfig[tier] ?? DEFAULT_MODELS[tier] ?? DEFAULT_MODELS['sonnet']!

  return { model, tier }
}
