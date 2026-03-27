# Phase 2: Configure

## Step 2.1: Plugin Verification

Verify xLoop plugin is properly installed before proceeding:
```
"xLoop plugin status:"
  - Marketplace: xloop (HSUNEH/xLoop)
  - Plugin: xloop@xloop
  - Version: {current version}
  - Skills: {count} loaded
  - Hooks: {count} registered
  - HUD: available (requires StatusLine hook, e.g. OMC)
```

If not installed: "Run `/plugin marketplace add HSUNEH/xLoop` then `/plugin install xloop@xloop`"

## Step 2.2: Test Mode

```
"Select test mode for after Ralph completion:"
1. B (semi-auto) — Auto-verify + user approves upgrade [Recommended]
2. C (full-auto) — Threshold-based auto-upgrade (max 3 cycles per session)
```

Save to `~/.claude/.xloop-config.json` → `{ "testMode": "B" | "C" }`

## Step 2.3: MCP Server

MCP server is **auto-registered** via `.mcp.json` on plugin install. No manual steps required.

Verify it's connected:
```
/plugin  →  xloop should show "MCP · ✓ connected"
```

Provides tools: xloop_state_read/write/clear/list, xloop_notepad_read/write, xloop_prd_generate

## Step 2.4: NotebookLM (core feature)

1. Check `pip install notebooklm-py[browser]` (install if missing)
2. Check `playwright install chromium` (install if missing)
3. Run `notebooklm login` (browser popup for Google auth)
4. Verify: `notebooklm list`
5. On failure: "NotebookLM auth failed. Run `xloop notebooklm-setup` later."

Save: `{ "notebooklm": { "authenticated": true } }`

## Step 2.5: Complexity Gate

Display defaults (no question):
```
Complexity Gate defaults:
  score 1 (simple, executor direct): complexity 1.0–1.5
  score 2 (medium, ralph only): complexity 1.6–2.2
  score 3 (complex, ralplan+ralph): complexity 2.3–3.0
```

Save: `{ "gate": { "simple": 1.5, "medium": 2.2 } }`

## Save progress

`.xloop/setup-state.json` → `{ "lastStep": 2, ... }`
