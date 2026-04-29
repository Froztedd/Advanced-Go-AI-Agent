#!/usr/bin/env bash
# Start the FastAPI backend and the Vite frontend together for local development.
# Both processes run in the foreground; Ctrl-C kills both.

set -euo pipefail

cd "$(dirname "$0")/.."

cleanup() {
  echo ""
  echo "stopping..."
  kill "$API_PID" 2>/dev/null || true
  kill "$WEB_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "→ starting FastAPI on http://localhost:8000"
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

echo "→ starting Vite on http://localhost:5173"
(cd web && npm run dev) &
WEB_PID=$!

wait
