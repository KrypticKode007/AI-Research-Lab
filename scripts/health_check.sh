#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running Silent-Failure-Hunter across all submodules..."
python3 devops/Silent-failure-hunter/cli.py ./core ./services ./edge || true

echo "🛡️ Verifying Git submodule integrity..."
git submodule status
