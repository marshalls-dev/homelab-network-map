#!/usr/bin/env bash
# Sync repo → live vault, restart the :8765 network map server.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8765
LIVE="${HOMELAB_VAULT:-$HOME/HomelabNetwork}"

bash "$SCRIPT_DIR/sync-to-live-vault.sh"

pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  echo "Stopping dashboard on :$PORT (PIDs: $pids)…"
  kill $pids 2>/dev/null || true
  sleep 1
  pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -z "$pids" ]] || kill -9 $pids 2>/dev/null || true
fi

echo "Starting dashboard on http://127.0.0.1:$PORT/network-graph.html"
cd "$LIVE"
exec python3 generate_network_map.py --serve --bind 127.0.0.1
