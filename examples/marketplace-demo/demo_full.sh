#!/usr/bin/env bash
# =============================================================================
# Self-contained end-to-end runner:
#   1. cleans previous generated outputs (keys are kept if present)
#   2. starts the mock Collibra API on :8580 in the background
#   3. runs the viewer-facing demo (demo_script.sh)
#   4. stops the mock server
# =============================================================================
set -e
cd "$(dirname "$0")"

# 1. Clean generated outputs for a deterministic re-run
rm -rf schemas/custom odgs_project audit mock_collibra.log

# 2. Start mock Collibra
python3 mock_collibra.py > mock_collibra.log 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
    if curl -s -o /dev/null http://localhost:8580/; then break; fi
    sleep 0.3
done
echo "[demo_full] mock Collibra up on http://localhost:8580 (pid $MOCK_PID)"

# 3. Run the demo
bash demo_script.sh

# 4. Stop mock server (trap handles it)
echo "[demo_full] stopping mock Collibra"
