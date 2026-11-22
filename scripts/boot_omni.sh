cp scripts/boot_omni.sh scripts/boot_omni.sh.bak 2>/dev/null || true

cat << 'EOF' > scripts/boot_omni.sh
#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Kryptic Omni-Core Unified Boot Orchestrator
# Initializes OmniBridge (IF-01/03/04), runs pre-flight checks, and launches UI.
# ==============================================================================

MOCK_FLAG=""
LAUNCH_DASHBOARD=true

for arg in "$@"; do
  case $arg in
    --mock)
      MOCK_FLAG="--mock"
      export OMNI_MOCK_MODE=1
      shift
      ;;
    --no-dashboard)
      LAUNCH_DASHBOARD=false
      shift
      ;;
    *)
      ;;
  esac
done

echo "============================================================"
echo " Booting Kryptic Omni-Core"
echo " Mode: $([ -n "$MOCK_FLAG" ] && echo "SIMULATION (--mock)" || echo "HARDWARE-IN-THE-LOOP")"
echo "============================================================"

# 1. Initialize OmniBridge & probe IF-01 / IF-03 / IF-04
echo "[1/3] Probing OmniBridge subsystems..."
python3 -m core.omni_bridge

# 2. Run Systems Engineering Verification Suite (REQ-01 through REQ-06)
echo "[2/3] Running pre-flight verification..."
./scripts/verify_omni.sh $MOCK_FLAG

# 3. Launch Live Telemetry Dashboard (or exit cleanly in headless mode)
if [ "$LAUNCH_DASHBOARD" = true ]; then
  echo "[3/3] Launching Live Telemetry Dashboard..."
  exec python3 scripts/dashboard.py $MOCK_FLAG
else
  echo "[3/3] Headless boot complete (--no-dashboard)."
fi
EOF

chmod +x scripts/boot_omni.sh
