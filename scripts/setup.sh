#!/usr/bin/env bash
set -euo pipefail

mkdir -p core interfaces services edge devops config scripts logs

add_sub() {
  local url="$1"
  local path="$2"
  if [ ! -d "$path/.git" ]; then
    git submodule add "$url" "$path" || true
  fi
}

# 1. Cognitive Core
add_sub https://github.com core/Golden-Agent
add_sub https://github.com core/Holonomic-Sentience
add_sub https://github.com core/Advanced-Ai-Model

# 2. Interfaces
add_sub https://github.com interfaces/kai-007
add_sub https://github.com interfaces/scrcpy

# 3. Domain Microservices
add_sub https://github.com services/PatchPilot
add_sub https://github.com services/nkryptd
add_sub https://github.com services/root

# 4. Edge & Robotics
add_sub https://github.com edge/golden-rosa-template
add_sub https://github.com edge/bio-edge-organism
add_sub https://github.com edge/Autonomous-Battery
add_sub https://github.com edge/self-healing-battery

# 5. Self-Healing DevOps
add_sub https://github.com devops/Bug-away
add_sub https://github.com devops/Silent-failure-hunter
add_sub https://github.com devops/claude-code

git submodule update --init --recursive
echo "✅ All 15 repositories mounted."
