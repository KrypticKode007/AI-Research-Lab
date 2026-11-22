#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd)"
cd "$ROOT_DIR"

echo "🌿 [1/5] Configuring Git branch topology across master repo & all submodules..."
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

echo "🔍 [2/5] Creating dynamic entry-point resolver (core/entry_resolver.py)..."
cat > core/entry_resolver.py <<'PYEOF'
from pathlib import Path
from typing import Optional

CANDIDATES = [
    "main.py", "app.py", "server.py", "cli.py",
    "bridge.py", "orchestrator.py", "hunter.py", "run.py"
]

def resolve_entrypoint(repo_path: Path) -> Optional[Path]:
    """Locate the primary executable Python file inside a submodule."""
    if not repo_path.exists():
        return None
    for name in CANDIDATES:
        direct = repo_path / name
        if direct.is_file():
            return direct
    for sub in ("src", "app", "core"):
        sub_dir = repo_path / sub
        if sub_dir.is_dir():
            for name in CANDIDATES:
                nested = sub_dir / name
                if nested.is_file():
                    return nested
    py_files = sorted(repo_path.glob("*.py"))
    return py_files[0] if py_files else None
PYEOF

echo "🛡️ [3/5] Installing unified GitHub Actions CI/CD (.github/workflows/omni-fortress.yml)..."
mkdir -p .github/workflows
cat > .github/workflows/omni-fortress.yml <<'YMLEOF'
name: Omni-Core Fortress & Self-Healing Pipeline

on:
  push:
    branches: [main, dev, "feat/**", "fix/**"]
  pull_request:
    branches: [main, dev]

jobs:
  audit-and-fortify:
    runs-on: macos-latest
    steps:
      - name: Checkout Master & Submodules
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Run Silent-Failure-Hunter Across Workspace
        run: |
          python3 -c '
          from pathlib import Path
          from core.entry_resolver import resolve_entrypoint
          hunter = resolve_entrypoint(Path("devops/Silent-failure-hunter"))
          print(f"Resolved Hunter Entrypoint: {hunter}")
          '
          if [ -f "devops/Silent-failure-hunter/cli.py" ]; then
            python3 devops/Silent-failure-hunter/cli.py ./core ./services ./edge
          fi

      - name: Execute Bug-Away Quality Gates
        run: |
          if [ -f "devops/Bug-away/run.sh" ]; then
            bash devops/Bug-away/run.sh
          fi
YMLEOF

echo "🍎 [4/5] Installing macOS LaunchAgent daemon for always-on background orchestration..."
PLIST_PATH="$HOME/Library/LaunchAgents/com.kryptic.omni-orchestrator.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$ROOT_DIR/logs"

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

echo "📦 [5/5] Committing initial master orchestration state to 'dev' branch..."
git add .
git commit -m "feat(orchestrator): initialize unified MCP bridge, branch topology, CI/CD & macOS daemon" || true

echo "✅ Complete: All branches created, CI/CD armed, and macOS LaunchAgent active on 'dev'."
