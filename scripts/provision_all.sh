#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "🌿 [1/4] Configuring Git branch topology across master repo & all submodules..."
BRANCHES=("dev" "feat/mcp-bridge" "feat/edge-telemetry" "fix/self-healing")

git checkout -B main
for br in "${BRANCHES[@]}"; do
  git checkout -B "$br"
done
git checkout dev

git submodule foreach --recursive '
  git fetch --all --quiet || true
  MAIN_BR=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed "s@^refs/remotes/origin/@@" || echo "main")
  git checkout -B "$MAIN_BR" 2>/dev/null || git checkout -B main
  for br in dev feat/mcp-bridge feat/edge-telemetry fix/self-healing; do
    git checkout -B "$br"
  done
  git checkout dev
'

echo "⚒️ [2/4] Ensuring Capability Forge & log directories exist..."
mkdir -p "$ROOT_DIR/core/forged_skills" "$ROOT_DIR/logs"
touch "$ROOT_DIR/core/forged_skills/__init__.py"

echo "🍎 [3/4] Installing macOS LaunchAgent daemon for always-on background orchestration..."
PLIST_PATH="$HOME/Library/LaunchAgents/com.kryptic.omni-orchestrator.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kryptic.omni-orchestrator</string>
    <key>ProgramArguments</key>
    <array>
        <string>$ROOT_DIR/.venv/bin/python</string>
        <string>$ROOT_DIR/core/omni_bridge.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$ROOT_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$ROOT_DIR</string>
        <key>OMNI_ENV</key>
        <string>macos</string>
        <key>OMNI_FORGE_DIR</key>
        <string>$ROOT_DIR/core/forged_skills</string>
        <key>OMNI_AUTO_HEAL</key>
        <string>true</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$ROOT_DIR/logs/omni_bridge.out.log</string>
    <key>StandardErrorPath</key>
    <string>$ROOT_DIR/logs/omni_bridge.err.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "📦 [4/4] Committing initial master orchestration state to 'dev' branch..."
git add .
git commit -m "feat(orchestrator): initialize universal MCP bridge, capability forge, branch topology & macOS daemon" || true

echo "✅ Complete: All branches created, Capability Forge ready, and macOS LaunchAgent active on 'dev'."
