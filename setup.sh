#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== xLoop setup ==="
echo ""

# 1. Install Python dependencies
echo "[1/6] Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"
echo ""

# 2. Verify yt-dlp installation
echo "[2/6] Verifying yt-dlp..."
if command -v yt-dlp &>/dev/null; then
    echo "  yt-dlp $(yt-dlp --version) installed"
else
    echo "  ERROR: yt-dlp not found after install. Check your PATH."
    exit 1
fi
echo ""

# 3. Install Playwright Chromium (required by notebooklm-py)
echo "[3/6] Installing Playwright Chromium..."
if command -v playwright &>/dev/null; then
    playwright install chromium
    echo "  Playwright Chromium installed"
else
    python -m playwright install chromium
    echo "  Playwright Chromium installed (via python -m)"
fi
echo ""

# 4. NotebookLM login guide
echo "[4/6] NotebookLM authentication..."
if command -v notebooklm &>/dev/null; then
    echo "  notebooklm CLI found"
    echo "  Run 'notebooklm login' to authenticate with your Google account (if not already done)."
else
    echo "  WARNING: notebooklm CLI not found. Try: pip install notebooklm-py[browser]"
fi
echo ""

# 5. Install NotebookLM skills for Claude Code
echo "[5/6] Installing NotebookLM skills..."
if command -v notebooklm &>/dev/null; then
    notebooklm skill install && echo "  NotebookLM skills installed" || echo "  WARNING: Failed to install NotebookLM skills. Run 'notebooklm skill install' manually."
else
    echo "  Skipped (notebooklm CLI not available)"
fi
echo ""

# 6. Link slash commands to .claude/commands/
echo "[6/6] Linking slash commands..."
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_COMMANDS_DIR="$PROJECT_ROOT/.claude/commands"

mkdir -p "$CLAUDE_COMMANDS_DIR"

for cmd_file in "$SCRIPT_DIR/commands/"*.md; do
    [ -f "$cmd_file" ] || continue
    cmd_name="$(basename "$cmd_file")"
    target="$CLAUDE_COMMANDS_DIR/$cmd_name"

    if [ -L "$target" ]; then
        echo "  $cmd_name: symlink already exists, updating..."
        rm "$target"
    elif [ -f "$target" ]; then
        echo "  $cmd_name: regular file exists, skipping (remove manually to use symlink)"
        continue
    fi

    ln -s "$cmd_file" "$target"
    echo "  $cmd_name: linked"
done
echo ""

echo "=== Setup complete ==="
echo "Use '/yt-search <query>' in Claude Code to search YouTube."
echo "Use '/notebooklm-add' to add sources to a NotebookLM notebook."
echo ""
echo "NOTE: Run 'notebooklm login' if you haven't authenticated yet."
