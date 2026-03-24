/**
 * LLM Bridge — MCP delegation-first LLM abstraction for xLoop.
 *
 * Provider priority:
 *   1. McpSamplingProvider — delegates to Claude Code host via MCP sampling
 *   2. HeuristicProvider  — deterministic fallback (no LLM, no API key)
 *
 * CostTracker accumulates token usage across all providers.
 */

export interface CompletionParams {
  prompt: string
  systemPrompt?: string
  model?: 'haiku' | 'sonnet' | 'opus'
  maxTokens?: number
  temperature?: number
}

export interface CompletionResult {
  text: string
  provider: 'mcp-sampling' | 'heuristic'
  tokensUsed: number
  durationMs: number
}

export interface LLMProvider {
  readonly name: string
  available(): Promise<boolean>
  complete(params: CompletionParams): Promise<CompletionResult>
}

// ---------------------------------------------------------------------------
// Cost Tracker
// ---------------------------------------------------------------------------

interface CostEntry {
  provider: string
  model: string
  tokensUsed: number
  timestamp: string
}

export class CostTracker {
  private entries: CostEntry[] = []
  private budget: number

  constructor(budget = Infinity) {
    this.budget = budget
  }

  record(entry: Omit<CostEntry, 'timestamp'>): void {
    this.entries = [
      ...this.entries,
      { ...entry, timestamp: new Date().toISOString() }
    ]
  }

  totalTokens(): number {
    return this.entries.reduce((sum, e) => sum + e.tokensUsed, 0)
  }

  withinBudget(additionalTokens = 0): boolean {
    return this.totalTokens() + additionalTokens <= this.budget
  }

  summary(): { totalTokens: number; totalCalls: number; entries: readonly CostEntry[] } {
    return {
      totalTokens: this.totalTokens(),
      totalCalls: this.entries.length,
      entries: this.entries
    }
  }
}

// ---------------------------------------------------------------------------
// MCP Sampling Provider
// ---------------------------------------------------------------------------

type McpServerRef = {
  server?: {
    requestSampling?: (params: unknown) => Promise<unknown>
  }
}

export class McpSamplingProvider implements LLMProvider {
  readonly name = 'mcp-sampling'
  private serverRef: McpServerRef

  constructor(serverRef: McpServerRef) {
    this.serverRef = serverRef
  }

  async available(): Promise<boolean> {
    return typeof this.serverRef.server?.requestSampling === 'function'
  }

  async complete(params: CompletionParams): Promise<CompletionResult> {
    const start = Date.now()
    const server = this.serverRef.server

    if (!server?.requestSampling) {
      throw new Error('MCP sampling not available')
    }

    const result = await server.requestSampling({
      messages: [
        ...(params.systemPrompt
          ? [{ role: 'user' as const, content: { type: 'text', text: `[System] ${params.systemPrompt}` } }]
          : []),
        { role: 'user' as const, content: { type: 'text', text: params.prompt } }
      ],
      modelPreferences: {
        hints: params.model ? [{ name: `claude-${params.model}` }] : undefined
      },
      maxTokens: params.maxTokens ?? 1024
    }) as { content?: { text?: string }; model?: string }

    const text = result?.content?.text ?? ''
    const tokensUsed = Math.ceil(text.length / 4) // rough estimate

    return {
      text,
      provider: 'mcp-sampling',
      tokensUsed,
      durationMs: Date.now() - start
    }
  }
}

// ---------------------------------------------------------------------------
// Heuristic Provider (deterministic fallback)
// ---------------------------------------------------------------------------

export class HeuristicProvider implements LLMProvider {
  readonly name = 'heuristic'

  async available(): Promise<boolean> {
    return true // always available
  }

  async complete(params: CompletionParams): Promise<CompletionResult> {
    const start = Date.now()

    // Deterministic text analysis — no LLM, zero cost
    const text = `[heuristic] No LLM available. Input: ${params.prompt.slice(0, 200)}`

    return {
      text,
      provider: 'heuristic',
      tokensUsed: 0,
      durationMs: Date.now() - start
    }
  }
}

// ---------------------------------------------------------------------------
// LLM Bridge (orchestrates providers + cost tracking)
// ---------------------------------------------------------------------------

export class LLMBridge {
  private providers: LLMProvider[]
  private costTracker: CostTracker

  constructor(providers: LLMProvider[], costTracker?: CostTracker) {
    this.providers = providers
    this.costTracker = costTracker ?? new CostTracker()
  }

  async complete(params: CompletionParams): Promise<CompletionResult> {
    if (!this.costTracker.withinBudget(params.maxTokens ?? 1024)) {
      // Budget exceeded — fall through to heuristic
      const heuristic = this.providers.find(p => p.name === 'heuristic')
      if (heuristic) return heuristic.complete(params)
      throw new Error('Token budget exceeded and no fallback provider available')
    }

    for (const provider of this.providers) {
      try {
        const isAvailable = await provider.available()
        if (!isAvailable) continue

        const result = await provider.complete(params)

        this.costTracker.record({
          provider: result.provider,
          model: params.model ?? 'default',
          tokensUsed: result.tokensUsed
        })

        return result
      } catch {
        // Provider failed — try next
        continue
      }
    }

    throw new Error('All LLM providers failed')
  }

  getCostTracker(): CostTracker {
    return this.costTracker
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

export function createDefaultBridge(serverRef?: McpServerRef): LLMBridge {
  const providers: LLMProvider[] = []

  if (serverRef) {
    providers.push(new McpSamplingProvider(serverRef))
  }

  providers.push(new HeuristicProvider())

  return new LLMBridge(providers, new CostTracker())
}
