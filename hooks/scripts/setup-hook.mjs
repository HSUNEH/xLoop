// Setup: Runs once on plugin install — registers MCP server
import { execSync } from 'node:child_process'

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT
if (!pluginRoot) {
  console.log('hook success: skipped (no CLAUDE_PLUGIN_ROOT)')
  process.exit(0)
}

try {
  // Check if xloop MCP server is already registered
  const list = execSync('claude mcp list', { encoding: 'utf8', timeout: 5000 })
  if (list.includes('xloop')) {
    console.log('hook success: xLoop MCP server already registered')
    process.exit(0)
  }
} catch {
  // claude CLI not available or mcp list failed — skip gracefully
}

try {
  execSync(
    `claude mcp add xloop -- node "${pluginRoot}/src/mcp-server.ts"`,
    { encoding: 'utf8', timeout: 10000 }
  )
  console.log('hook success: xLoop MCP server registered')
} catch (err) {
  console.error(`MCP registration failed: ${err.message}`)
  console.log('hook success: setup completed (MCP registration skipped)')
}
