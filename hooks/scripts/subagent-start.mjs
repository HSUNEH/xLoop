// SubagentStart: Track spawned agent for duration measurement
const agentId = process.env.CLAUDE_AGENT_ID || 'unknown'
// Lightweight — just acknowledge, no file I/O
console.log(`subagent started: ${agentId}`)
