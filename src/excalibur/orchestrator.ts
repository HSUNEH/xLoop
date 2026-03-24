import type { ExcaliburState } from './state.js'
import type { ProjectSpec } from '../interview.js'
import type { LLMBridge } from '../llm-bridge.js'
import type { LearningEntry } from './learnings.js'

export type ExcaliburMode = 'autohunt' | 'grab'

export interface EvalMetrics {
  testPassRate: number   // 0-1
  typecheck: boolean
  buildSuccess: boolean
  coverage: number       // 0-1
  acceptanceMet: number  // 0-1
}

export interface LoopResult {
  loop: number
  milestone: string
  evalMetrics: EvalMetrics
  learnings: LearningEntry
  improved: boolean
}

export interface BigLoopConfig {
  mode: ExcaliburMode
  maxLoops: number
  sessionId: string
  projectSpec: ProjectSpec
  bridge?: LLMBridge
}

/**
 * Execute one iteration of the Big Loop:
 * 1. Ralplan: plan the current milestone
 * 2. Ralph: implement stories
 * 3. Eval: collect metrics
 * 4. Checkpoint: autohunt=auto-proceed, grab=pause for user
 * 5. Learnings: capture what was learned
 */
export async function executeLoop(
  state: ExcaliburState,
  config: BigLoopConfig,
  callbacks: {
    onRalplan: (milestone: string) => Promise<string>                          // returns plan path
    onRalph: (planPath: string) => Promise<string>                             // returns report path
    onEval: () => Promise<EvalMetrics>
    onCheckpoint?: (loop: number, metrics: EvalMetrics) => Promise<boolean>   // grab mode: returns continue?
    onLearnings: (loop: number) => Promise<LearningEntry>
  }
): Promise<LoopResult> {
  const milestone = getCurrentMilestone(state)

  // 1. Ralplan
  const planPath = await callbacks.onRalplan(milestone)

  // 2. Ralph
  const reportPath = await callbacks.onRalph(planPath)
  void reportPath // used by caller via side effects

  // 3. Eval
  const metrics = await callbacks.onEval()

  // 4. Checkpoint (grab mode only)
  if (config.mode === 'grab' && callbacks.onCheckpoint) {
    await callbacks.onCheckpoint(state.currentLoop, metrics)
  }

  // 5. Learnings
  const learnings = await callbacks.onLearnings(state.currentLoop)

  return {
    loop: state.currentLoop,
    milestone,
    evalMetrics: metrics,
    learnings,
    improved: metrics.testPassRate >= 0.8 && metrics.buildSuccess
  }
}

function getCurrentMilestone(state: ExcaliburState): string {
  const activeLane = state.activeLanes.find(l => l.status !== 'completed')
  return activeLane?.milestone ?? `milestone-${state.currentLoop + 1}`
}
