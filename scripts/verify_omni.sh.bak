#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd)"
cd "$ROOT_DIR"

echo "🔍 [1/5] Verifying Git branches..."
for br in main dev feat/mcp-bridge feat/edge-telemetry fix/self-healing; do
  git show-ref --verify --quiet "refs/heads/$br" && echo "  ✅ Branch ready: $br" || echo "  ❌ Missing branch: $br"
done

echo "📦 [2/5] Checking 15 submodule mounts..."
SUB_COUNT=$(git submodule status | wc -l | tr -d ' ')
echo "  -> Mounted submodules: $SUB_COUNT / 15"

echo "🐍 [3/5] Validating Python MCP Bridge, Entry Resolver & Capability Forge..."
source .venv/bin/activate
python3 -c '
import core.entry_resolver
import core.capability_forge
import core.omni_bridge
print("  ✅ All core orchestration modules imported cleanly.")
'

echo "🍎 [4/5] Checking macOS LaunchAgent daemon..."
if launchctl list | grep -q "com.kryptic.omni-orchestrator"; then
  echo "  ✅ macOS Background Orchestrator is LIVE."
else
  echo "  ⚠️ Daemon not loaded yet (run ./scripts/provision_all.sh)."
fi

echo "📊 [5/5] Launching Live Omni-Core Dashboard..."
python3 scripts/dashboard.py
