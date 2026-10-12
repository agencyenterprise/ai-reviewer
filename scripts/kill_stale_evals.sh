#!/bin/sh
# Stop stale processes created by scripts/run_all_evals.sh.

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
EVAL_PORT=${EVAL_PORT:-8010}
PIDS=""

add_pid() {
    candidate=$1
    case " $PIDS " in
        *" $candidate "*) ;;
        *) PIDS="$PIDS $candidate" ;;
    esac
}

for pattern in \
    "scripts/run_all_evals.sh" \
    "flow run $PROJECT_ROOT/evals_inspectai/flow_config/run_all_evals.py" \
    "flow run evals_inspectai/flow_config/run_all_evals.py"
do
    for pid in $(pgrep -f "$pattern" 2>/dev/null || true); do
        [ "$pid" = "$$" ] || add_pid "$pid"
    done
done

if command -v lsof >/dev/null 2>&1; then
    for pid in $(lsof -tiTCP:"$EVAL_PORT" -sTCP:LISTEN 2>/dev/null || true); do
        add_pid "$pid"
    done
fi

if [ -z "${PIDS# }" ]; then
    echo "No stale all-evals processes found."
    exit 0
fi

echo "Stopping stale all-evals processes:$PIDS"
for pid in $PIDS; do
    kill -TERM "$pid" 2>/dev/null || true
done

attempt=0
while [ "$attempt" -lt 20 ]; do
    remaining=""
    for pid in $PIDS; do
        if kill -0 "$pid" 2>/dev/null; then
            remaining="$remaining $pid"
        fi
    done
    [ -z "${remaining# }" ] && break
    PIDS=$remaining
    attempt=$((attempt + 1))
    sleep 0.25
done

for pid in $PIDS; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "Force-stopping PID $pid"
        kill -KILL "$pid" 2>/dev/null || true
    fi
done

echo "Stale all-evals processes stopped."
