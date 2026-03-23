// PreToolUse: Lightweight guidance — only inject for Agent/Bash tools
const toolName = process.env.CLAUDE_TOOL_NAME || ''

if (toolName === 'Agent' || toolName === 'Bash') {
  console.log('Use parallel execution for independent tasks.')
}
// No output for other tools — zero token overhead
