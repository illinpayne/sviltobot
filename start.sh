#!/usr/bin/env bash
set -euo pipefail

cd /app

# Forward SIGTERM/SIGINT to children so `docker stop` works correctly.
pids=()
terminate() {
  for pid in "${pids[@]:-}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
}
trap terminate TERM INT

python -u /app/main.py &
pids+=("$!")

python -u -m parser.run &
pids+=("$!")

wait -n
terminate
wait || true