#!/usr/bin/env bash
set -euo pipefail

mkdir -p kryptic-omni-core/{core,interfaces,services,edge,devops,config,scripts}
cd kryptic-omni-core
git init

# 1. Core Cognitive & Orchestration Layer
git submodule add https://github.com core/Golden-Agent
git submodule add https://github.com core/Holonomic-Sentience
git submodule add https://github.com core/Advanced-Ai-Model

# 2. User Interface & Device Control Layer
git submodule add https://github.com interfaces/kai-007
git submodule add https://github.com interfaces/scrcpy

# 3. Domain Microservices Layer
git submodule add https://github.com services/PatchPilot
git submodule add https://github.com services/nkryptd
git submodule add https://github.com services/root

# 4. Edge, Robotics & Hardware Telemetry Layer
git submodule add https://github.com edge/golden-rosa-template
git submodule add https://github.com edge/bio-edge-organism
git submodule add https://github.com edge/Autonomous-Battery
git submodule add https://github.com edge/self-healing-battery

# 5. Self-Healing DevOps & QA Layer
git submodule add https://github.com devops/Bug-away
git submodule add https://github.com devops/Silent-failure-hunter
git submodule add https://github.com devops/claude-code

git submodule update --init --recursive
echo "✅ All 15 repositories mounted into kryptic-omni-core."
