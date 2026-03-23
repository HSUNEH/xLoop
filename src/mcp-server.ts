import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { z } from 'zod'
import { readState, writeState, clearState, listActiveSessions } from './state.js'
import { generatePrd } from './prd.js'
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname } from 'node:path'

const NOTEPAD_PATH = '.xloop/notepad.md'

const server = new McpServer({
  name: 'xloop',
  version: '0.1.0'
})

// --- State tools ---

server.tool(
  'xloop_state_read',
  'Read state for a mode in a session',
  { session_id: z.string(), mode: z.string() },
  async ({ session_id, mode }) => {
    const state = readState(session_id, mode)
    return { content: [{ type: 'text' as const, text: state ? JSON.stringify(state, null, 2) : 'No state found' }] }
  }
)

server.tool(
  'xloop_state_write',
  'Write state for a mode in a session',
  { session_id: z.string(), mode: z.string(), data: z.string() },
  async ({ session_id, mode, data }) => {
    writeState(session_id, mode, JSON.parse(data))
    return { content: [{ type: 'text' as const, text: `State written for ${mode} in session ${session_id}` }] }
  }
)

server.tool(
  'xloop_state_clear',
  'Clear state for a mode in a session',
  { session_id: z.string(), mode: z.string() },
  async ({ session_id, mode }) => {
    clearState(session_id, mode)
    return { content: [{ type: 'text' as const, text: `State cleared for ${mode} in session ${session_id}` }] }
  }
)

server.tool(
  'xloop_state_list',
  'List all active sessions',
  {},
  async () => {
    const sessions = listActiveSessions()
    return { content: [{ type: 'text' as const, text: sessions.length > 0 ? sessions.join('\n') : 'No active sessions' }] }
  }
)

// --- Notepad tools ---

server.tool(
  'xloop_notepad_read',
  'Read the notepad contents',
  {},
  async () => {
    if (!existsSync(NOTEPAD_PATH)) return { content: [{ type: 'text' as const, text: '' }] }
    const text = readFileSync(NOTEPAD_PATH, 'utf-8')
    return { content: [{ type: 'text' as const, text }] }
  }
)

server.tool(
  'xloop_notepad_write',
  'Write to the notepad',
  { content: z.string() },
  async ({ content }) => {
    mkdirSync(dirname(NOTEPAD_PATH), { recursive: true })
    writeFileSync(NOTEPAD_PATH, content, 'utf-8')
    return { content: [{ type: 'text' as const, text: 'Notepad updated' }] }
  }
)

// --- PRD tool ---

server.tool(
  'xloop_prd_generate',
  'Generate a PRD scaffold from a task description',
  { task: z.string(), use_llm: z.boolean().optional() },
  async ({ task, use_llm }) => {
    const prd = generatePrd(task, { useLlm: use_llm })
    return { content: [{ type: 'text' as const, text: JSON.stringify(prd, null, 2) }] }
  }
)

// --- Start server ---

async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)
}

main().catch(console.error)
