#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd)"
cd "$ROOT_DIR"

[ -f "assets/kryptic_omni_core.ascii" ] && cat assets/kryptic_omni_core.ascii
echo ""

echo "🍎 [1/6] Checking macOS system dependencies via Homebrew..."
BREW_PKGS=(python@3.12 node cmake scrcpy android-platform-tools)
for pkg in "${BREW_PKGS[@]}"; do
  brew list "$pkg" &>/dev/null || brew install "$pkg"
done

echo "🐍 [2/6] Building unified Python virtual environment..."
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install mcp fastapi uvicorn pydantic httpx

# Install dependencies across all Python submodules safely
find core interfaces services edge devops -maxdepth 2 -name "requirements.txt" | while read -r req; do
  echo "   -> Installing $req"
  pip install -r "$req" || echo "   ⚠️ Skipping conflicting dependency in $req"
done

echo "⚒️ [3/6] Initializing Capability Forge & runtime directories..."
mkdir -p core/forged_skills logs config
touch core/forged_skills/__init__.py

echo "⚙️ [4/6] Compiling C++11 Edge Neuromorphic Core (bio-edge-organism)..."
if [ -f "edge/bio-edge-organism/CMakeLists.txt" ]; then
  cmake -S edge/bio-edge-organism -B edge/bio-edge-organism/build
  cmake --build edge/bio-edge-organism/build -j"$(sysctl -n hw.ncpu)"
fi

echo "🔗 [5/6] Writing absolute macOS MCP configuration (config/mcp_hub.json)..."
cat > config/mcp_hub.json <<EOF
{
  "orchestrator": "Golden-Agent",
  "mode": "universal-autonomous",
  "version": "2.0.0",
  "capabilities": {
    "holonomic_memory": true,
    "capability_forge": true,
    "self_healing_immune_system": true,
    "edge_neuromorphic_bridge": true,
    "device_control": ["macos", "android-15+"]
  },
  "mcpServers": {
    "kryptic-omni-orchestrator": {
      "command": "$ROOT_DIR/.venv/bin/python",
      "args": ["$ROOT_DIR/core/omni_bridge.py"],
      "env": {
        "PYTHONPATH": "$ROOT_DIR",
        "OMNI_ENV": "macos",
        "OMNI_FORGE_DIR": "$ROOT_DIR/core/forged_skills",
        "OMNI_AUTO_HEAL": "true"
      }
    }
  }
}
EOF

echo "🚀 [6/6] Starting background microservices & launching Golden-Agent..."
if [ -f "services/PatchPilot/app.py" ]; then
  uvicorn services.PatchPilot.app:app --host 127.0.0.1 --port 8001 > logs/patchpilot.log 2>&1 &
  PATCHPILOT_PID=$!
  trap "kill $PATCHPILOT_PID 2>/dev/null || true" EXIT
fi

# Dynamically resolve Golden-Agent's entry point and boot with the unified MCP hub
GOLDEN_ENTRY=$(python3 -c '
from pathlib import Path
from core.entry_resolver import resolve_entrypoint
ep = resolve_entrypoint(Path("core/Golden-Agent"))
print(ep if ep else "core/Golden-Agent/main.py")
')

echo "🧠 Launching Orchestrator: $GOLDEN_ENTRY"
python3 "$GOLDEN_ENTRY" --mcp-config config/mcp_hub.json
