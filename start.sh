#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start backend
(cd "$ROOT_DIR/backend" && uv run uvicorn app.main:app --reload --port 8000 2>&1 | sed 's/^/[backend] /') &
BACKEND_PID=$!

# Start frontend
(cd "$ROOT_DIR/frontend" && npm run dev 2>&1 | sed 's/^/[frontend] /') &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" EXIT INT TERM

echo "[start.sh] Backend PID: $BACKEND_PID  |  Frontend PID: $FRONTEND_PID"
echo "[start.sh] Press Ctrl+C to stop both services."
wait
