#!/bin/sh
# Run the abbreviation-checker E2E eval against a temporary local API process.
# Extra arguments are passed to `inspect eval`; without arguments, one sample runs.

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

EVAL_PORT=${EVAL_PORT:-8000}
EVAL_API_BASE_URL="http://127.0.0.1:$EVAL_PORT"
EVAL_MODEL=${EVAL_MODEL:-openai/gpt-5.6-terra-2026-07-09}
AUTH_GOOGLE_ID=${AUTH_GOOGLE_ID:-local-eval}
AUTH_GOOGLE_SECRET=${AUTH_GOOGLE_SECRET:-local-eval}
MCP_BASE_URL=${MCP_BASE_URL:-"$EVAL_API_BASE_URL/mcp"}
ALLOW_WORKFLOW_MODEL_OVERRIDE=true

export EVAL_API_BASE_URL EVAL_MODEL AUTH_GOOGLE_ID AUTH_GOOGLE_SECRET MCP_BASE_URL
export ALLOW_WORKFLOW_MODEL_OVERRIDE

API_LOG=$(mktemp "${TMPDIR:-/tmp}/draft-detective-eval-api.XXXXXX")
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

echo "Starting API at $EVAL_API_BASE_URL..."
uv --native-tls run uvicorn lib.api.main:app \
    --host 127.0.0.1 \
    --port "$EVAL_PORT" \
    >"$API_LOG" 2>&1 &
API_PID=$!

attempt=0
while [ "$attempt" -lt 60 ]; do
    if curl -fsS "$EVAL_API_BASE_URL/api/health" >/dev/null 2>&1; then
        break
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

if [ "$#" -eq 0 ]; then
    set -- --limit 1
fi

HAS_MODEL=0
for argument in "$@"; do
    case "$argument" in
        --model|--model=*) HAS_MODEL=1 ;;
    esac
done
if [ "$HAS_MODEL" -eq 0 ]; then
    set -- "$@" --model "$EVAL_MODEL"
fi

echo "Running abbreviation-checker eval..."
if ! uv --native-tls run inspect eval \
    evals_inspectai/e2e/abbreviation_checker/abbreviation_checker_e2e.py \
    "$@"; then
    KEEP_API_LOG=1
    echo "Eval failed. Last 200 lines from the API process:" >&2
    tail -n 200 "$API_LOG" >&2
    exit 1
fi
