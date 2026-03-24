import { readConfig } from './state.js'
import type { LLMBridge } from './llm-bridge.js'

interface GateResult {
  score: 1 | 2 | 3
  method: 'heuristic' | 'haiku'
  details: string
}

const SIMPLE_KEYWORDS = ['fix', 'update', 'rename', 'translate', 'typo', 'add to', 'change to', 'replace']
const COMPLEX_KEYWORDS = ['refactor', 'architect', 'design', 'new system', 'redesign', 'migrate', 'overhaul']
const FILE_PATH_PATTERN = /(?:^|\s)([\w./\\-]+\.\w{1,6})(?:\s|$)/

function countLines(prompt: string): number {
  return prompt.split('\n').filter(l => l.trim().length > 0).length
}

function hasFilePath(prompt: string): boolean {
  return FILE_PATH_PATTERN.test(prompt)
}

function matchesKeywords(prompt: string, keywords: readonly string[]): boolean {
  const lower = prompt.toLowerCase()
  return keywords.some(k => lower.includes(k))
}

function heuristicScore(prompt: string): { score: 1 | 2 | 3; certain: boolean; details: string } {
  const isSimpleKeyword = matchesKeywords(prompt, SIMPLE_KEYWORDS)
  const isComplexKeyword = matchesKeywords(prompt, COMPLEX_KEYWORDS)
  const hasFile = hasFilePath(prompt)
  const lines = countLines(prompt)

  // Definitely simple: simple keyword + file path + short
  if (isSimpleKeyword && !isComplexKeyword && (hasFile || lines <= 1)) {
    return { score: 1, certain: true, details: `simple keyword + ${hasFile ? 'file path' : 'single line'}` }
  }

  // Definitely complex: complex keyword + no file path + multi-line
  if (isComplexKeyword && !isSimpleKeyword && !hasFile && lines > 1) {
    return { score: 3, certain: true, details: `complex keyword + multi-line + no file path` }
  }

  // Strong simple signal
  if (isSimpleKeyword && !isComplexKeyword) {
    return { score: 1, certain: true, details: 'simple keyword only' }
  }

  // Strong complex signal
  if (isComplexKeyword && !isSimpleKeyword) {
    return { score: 3, certain: true, details: 'complex keyword only' }
  }

  // Mixed or no signals — uncertain
  const tentativeScore = lines <= 1 && hasFile ? 1 : lines > 3 ? 3 : 2
  return {
    score: tentativeScore as 1 | 2 | 3,
    certain: false,
    details: `uncertain: lines=${lines}, hasFile=${hasFile}, simpleKw=${isSimpleKeyword}, complexKw=${isComplexKeyword}`
  }
}

function microAssessment(prompt: string): GateResult {
  // Step 2: 3-dimension scoring (would call Haiku in production)
  // For now: deterministic approximation based on text analysis
  const lines = countLines(prompt)
  const hasFile = hasFilePath(prompt)
  const words = prompt.split(/\s+/).length

  // Scope: 1=single file, 2=multi-file, 3=cross-system
  const scope = hasFile && lines <= 2 ? 1 : lines > 5 || words > 50 ? 3 : 2

  // Clarity: 1=specific, 2=some ambiguity, 3=only goal
  const clarity = hasFile && lines <= 1 ? 1 : words < 20 && !hasFile ? 3 : 2

  // Decision: 1=no choices, 2=some, 3=architectural
  const hasQuestionWords = /어떻게|how|which|should|선택|choose/i.test(prompt)
  const decision = hasQuestionWords ? 3 : lines > 3 ? 2 : 1

  const config = readConfig()
  const gateConfig = (config['gate'] ?? {}) as Record<string, number>
  const simpleThreshold = gateConfig['simple'] ?? 1.5
  const mediumThreshold = gateConfig['medium'] ?? 2.2

  const weighted = scope * 0.4 + clarity * 0.35 + decision * 0.25
  const score: 1 | 2 | 3 = weighted <= simpleThreshold ? 1 : weighted <= mediumThreshold ? 2 : 3

  return {
    score,
    method: 'heuristic',
    details: `scope=${scope} clarity=${clarity} decision=${decision} weighted=${weighted.toFixed(2)}`
  }
}

export function assessComplexity(prompt: string): GateResult {
  // Step 1: Structural heuristic
  const heuristic = heuristicScore(prompt)

  if (heuristic.certain) {
    return { score: heuristic.score, method: 'heuristic', details: heuristic.details }
  }

  // Step 2: deterministic micro-assessment (when heuristic is uncertain)
  return microAssessment(prompt)
}

export async function assessComplexityAsync(
  prompt: string,
  bridge?: LLMBridge
): Promise<GateResult> {
  const heuristic = heuristicScore(prompt)
  if (heuristic.certain) {
    return { score: heuristic.score, method: 'heuristic', details: heuristic.details }
  }

  if (!bridge) {
    return microAssessment(prompt)
  }

  try {
    const result = await bridge.complete({
      prompt: `Rate this task's complexity on 3 dimensions (scope, clarity, decision) each 1-3.\nTask: ${prompt}`,
      systemPrompt: 'You are a complexity assessor. Respond with JSON: {"scope":N,"clarity":N,"decision":N}',
      model: 'haiku',
      maxTokens: 100,
      temperature: 0.1
    })

    const parsed = JSON.parse(result.text) as { scope: number; clarity: number; decision: number }
    const weighted = (parsed.scope * 0.4) + (parsed.clarity * 0.35) + (parsed.decision * 0.25)
    const score: 1 | 2 | 3 = weighted <= 1.5 ? 1 : weighted <= 2.2 ? 2 : 3

    return {
      score,
      method: result.provider === 'heuristic' ? 'heuristic' : 'haiku',
      details: `scope=${parsed.scope} clarity=${parsed.clarity} decision=${parsed.decision} weighted=${weighted.toFixed(2)} (${result.provider})`
    }
  } catch {
    return microAssessment(prompt)
  }
}
