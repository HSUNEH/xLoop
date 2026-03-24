#!/usr/bin/env node

import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

function getVersion(): string {
  try {
    const pkg = JSON.parse(readFileSync(join(__dirname, '..', '..', 'package.json'), 'utf-8'))
    return pkg.version ?? '0.0.0'
  } catch {
    return '0.0.0'
  }
}

const COMMANDS: Record<string, { description: string; usage: string }> = {
  setup:     { description: 'Install and configure xLoop',          usage: 'xloop setup [--local|--global|--force]' },
  excalibur: { description: 'Full project orchestration (the essence of xLoop)', usage: 'xloop excalibur [autohunt|grab] <description>' },
  ralph:     { description: 'PRD-driven implementation loop',       usage: 'xloop ralph <task>' },
  ralplan:   { description: '4-agent consensus planning',           usage: 'xloop ralplan <task>' },
  research:  { description: 'Multi-source research',                usage: 'xloop research <topic>' },
  upgrade:   { description: 'Self-improvement cycle',               usage: 'xloop upgrade' },
  rollback:  { description: 'Restore from snapshot',                usage: 'xloop rollback [version]' },
  status:    { description: 'Show current state',                   usage: 'xloop status' },
  prd:       { description: 'Generate PRD scaffold',                usage: 'xloop prd <task>' },
}

function showHelp(): void {
  console.log(`
xLoop — Agent Harness v${getVersion()}

USAGE:
  xloop <command> [args]

COMMANDS:`)

  for (const [name, cmd] of Object.entries(COMMANDS)) {
    console.log(`  ${name.padEnd(12)} ${cmd.description}`)
  }

  console.log(`
FLAGS:
  --help       Show this help
  --version    Show version

EXAMPLES:
  xloop setup                          # First-time setup
  xloop excalibur "chat app"           # Full project orchestration (autohunt mode)
  xloop excalibur grab "chat app"      # Grab-and-go mode
  xloop excalibur autohunt "chat app"  # Auto-hunt mode (explicit)
  xloop ralph "fix auth bug"           # Implementation loop
  xloop ralplan "new feature"          # Consensus planning
  xloop research "WebSocket"           # Standalone research

KEYWORDS (use naturally in Claude Code):
  "excalibur ..."        → full project orchestration
  "excalibur autohunt"   → auto-hunt mode (iterates until goal met)
  "excalibur grab"       → grab-and-go mode (single-pass)
  "ralph ..."            → implementation loop
  "ralplan ..."          → consensus planning
`)
}

function showVersion(): void {
  console.log(`xloop v${getVersion()}`)
}

function main(): void {
  const args = process.argv.slice(2)

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp()
    return
  }

  if (args.includes('--version') || args.includes('-v')) {
    showVersion()
    return
  }

  const command = args[0]!
  const commandArgs = args.slice(1)

  if (!(command in COMMANDS)) {
    console.error(`Unknown command: ${command}`)
    console.error(`Run 'xloop --help' for available commands`)
    process.exit(1)
  }

  const cmd = COMMANDS[command]!
  console.log(`xloop ${command}: ${cmd.description}`)
  console.log(`Usage: ${cmd.usage}`)

  if (command === 'excalibur') {
    const mode = commandArgs[0] === 'grab' ? 'grab' : 'autohunt'
    const description = commandArgs.slice(mode === commandArgs[0] ? 1 : 0).join(' ')
    console.log(`\nMode: ${mode}`)
    console.log(`Description: ${description || '(none)'}`)
    console.log(`\nTo run in Claude Code, use: "excalibur ${mode} ${description}"`)
    console.log('The keyword detector hook will invoke the appropriate skill.')
    return
  }

  if (commandArgs.length > 0) {
    console.log(`Args: ${commandArgs.join(' ')}`)
  }

  console.log(`\nTo run in Claude Code, say: "${command} ${commandArgs.join(' ')}"`)
  console.log(`The keyword detector hook will invoke skills/${command}/SKILL.md`)
}

main()
