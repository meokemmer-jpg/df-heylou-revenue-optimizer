#!/bin/bash
# DF-HeyLou-Revenue-Optimizer Runner [CRUX-MK]
# K16 Concurrent-Spawn-Mutex Pattern (wrapper + engine layer)

set -euo pipefail

LOCK_DIR="/tmp/df-heylou-revenue-opt.lock"
LOCK_AGE_LIMIT_S=21600  # 6h stale-claim

# K16 Wrapper-Mutex (mkdir-atomic)
if [ -d "$LOCK_DIR" ]; then
  LOCK_AGE_S=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE_S" -gt "$LOCK_AGE_LIMIT_S" ]; then
    echo "Stale-Lock claimed (age=$LOCK_AGE_S s > limit=$LOCK_AGE_LIMIT_S)"
    rm -rf "$LOCK_DIR"
  else
    echo "K16-VETO: Lock active (age=$LOCK_AGE_S s)"
    exit 3
  fi
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "K16-VETO: Lock-Race lost"
  exit 3
fi

echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

# STOP.flag-Check
STOP_FLAG="/tmp/df-heylou-revenue-opt.stop"
if [ -f "$STOP_FLAG" ]; then
  echo "STOP.flag detected, exiting"
  exit 0
fi

# Run
cd "$(dirname "$0")/.."
python3 -m src.revenue_orchestrator "$@"
