#!/bin/sh
# Start the local dependencies and run every E2E benchmark through Inspect Flow.

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

# Keep the large suite isolated from the ordinary dev server on port 8000.
EVAL_PORT=${EVAL_PORT:-8010}
EVAL_API_BASE_URL="http://127.0.0.1:$EVAL_PORT"
EVAL_EPOCHS=5
AUTH_GOOGLE_ID=${AUTH_GOOGLE_ID:-local-eval}
AUTH_GOOGLE_SECRET=${AUTH_GOOGLE_SECRET:-local-eval}
MCP_BASE_URL=${MCP_BASE_URL:-"$EVAL_API_BASE_URL/mcp"}
ALLOW_WORKFLOW_MODEL_OVERRIDE=true
UV_NATIVE_TLS=true

export EVAL_API_BASE_URL AUTH_GOOGLE_ID AUTH_GOOGLE_SECRET MCP_BASE_URL
export ALLOW_WORKFLOW_MODEL_OVERRIDE UV_NATIVE_TLS

case "${1:-}" in
    --epochs)
        if [ "$#" -lt 2 ]; then
            echo "--epochs requires a positive integer." >&2
            exit 2
        fi
        EVAL_EPOCHS=$2
        shift 2
        ;;
    --epochs=*)
        EVAL_EPOCHS=${1#--epochs=}
        shift
        ;;
esac

case "$EVAL_EPOCHS" in
    ''|*[!0-9]*|0)
        echo "--epochs requires a positive integer." >&2
        exit 2
        ;;
esac

API_LOG=$(mktemp "${TMPDIR:-/tmp}/draft-detective-all-evals-api.XXXXXX")
API_PID=""

cleanup() {
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
    fi
    if [ "${KEEP_API_LOG:-0}" = "1" ]; then
        echo "API log retained at $API_LOG" >&2
    else
        rm -f "$API_LOG"
    fi
}
trap cleanup EXIT INT TERM

echo "Starting PostgreSQL..."
docker compose up -d --wait db

echo "Applying database migrations..."
uv --native-tls run alembic upgrade head

if curl -fsS "http://127.0.0.1:$EVAL_PORT/api/health" >/dev/null 2>&1; then
    echo "Port $EVAL_PORT already has a Draft Detective API server." >&2
    echo "Stop it or choose another port with EVAL_PORT=<port>." >&2
    exit 1
fi

echo "Starting API at $EVAL_API_BASE_URL..."
uv --native-tls run uvicorn lib.api.main:app \
    --host 127.0.0.1 \
    --port "$EVAL_PORT" \
    >"$API_LOG" 2>&1 &
API_PID=$!

attempt=0
while [ "$attempt" -lt 60 ]; do
    if curl -fsS "$EVAL_API_BASE_URL/api/health" >/dev/null 2>&1; then
        # Ensure this script's child owns the healthy listener; an existing
        # server must never be mistaken for the configured eval server.
        if kill -0 "$API_PID" 2>/dev/null; then
            break
        fi
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "API exited during startup:" >&2
        tail -n 100 "$API_LOG" >&2
        exit 1
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if ! curl -fsS "$EVAL_API_BASE_URL/api/health" >/dev/null 2>&1; then
    echo "API did not become healthy within 60 seconds:" >&2
    tail -n 100 "$API_LOG" >&2
    exit 1
fi

echo "Running all benchmarks for $EVAL_EPOCHS epochs..."
if ! uv --native-tls run flow run \
    evals_inspectai/flow_config/run_all_evals.py \
    --arg "api_base_url=$EVAL_API_BASE_URL" \
    --arg "epochs=$EVAL_EPOCHS" \
    "$@"; then
    KEEP_API_LOG=1
    echo "Flow failed. Last 200 lines from the API process:" >&2
    tail -n 200 "$API_LOG" >&2
    exit 1
fi
