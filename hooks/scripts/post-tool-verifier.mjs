// PostToolUse: Validation — only inject when relevant
const toolName = process.env.CLAUDE_TOOL_NAME || ''

if (toolName === 'Write' || toolName === 'Edit') {
  console.log('Verify changes work after editing.')
}
// No output for read-only tools
