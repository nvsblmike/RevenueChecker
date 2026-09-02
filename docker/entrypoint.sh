#!/bin/sh
set -eu

shutdown() {
  kill -TERM "$frontend_pid" "$backend_pid" 2>/dev/null || true
  wait "$frontend_pid" "$backend_pid" 2>/dev/null || true
}

trap shutdown INT TERM EXIT

uvicorn api.index:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

npm start -- --hostname 0.0.0.0 --port 3000 &
frontend_pid=$!

while kill -0 "$frontend_pid" 2>/dev/null && kill -0 "$backend_pid" 2>/dev/null; do
  sleep 2
done

exit 1
