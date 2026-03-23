// PostToolUseFailure: Recovery guidance on any failure
const toolName = process.env.CLAUDE_TOOL_NAME || ''
console.log(`Tool "${toolName}" failed. Analyze the error and fix.`)
