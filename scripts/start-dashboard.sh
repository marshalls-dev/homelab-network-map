#!/bin/bash
# Start the live network map, or open it if already healthy.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
VAULT="${HOMELAB_VAULT:-$HOME/HomelabNetwork}"
PORT=8765
URL="http://127.0.0.1:${PORT}/network-graph.html"

# If repo and live vault differ, offer sync when template is newer.
if [[ "$REPO" != "$VAULT" && -f "$REPO/network-graph-template.html" && -f "$VAULT/network-graph-template.html" ]]; then
  if [[ "$REPO/network-graph-template.html" -nt "$VAULT/network-graph-template.html" ]]; then
    echo "Repo is newer than $VAULT — syncing before start…"
    bash "$SCRIPT_DIR/sync-to-live-vault.sh"
  fi
fi

cd "$VAULT" || {
  echo "HomelabNetwork folder not found at $VAULT"
  read -r -p "Press Enter to close..."
  exit 1
}

is_healthy() {
  curl -sf --max-time 3 "$URL" >/dev/null 2>&1
}

listeners() {
  lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true
}

stop_listeners() {
  local pids
  pids="$(listeners)"
  if [ -z "$pids" ]; then
    return 0
  fi
  echo "Stopping stale server(s) on port $PORT (PIDs: $pids)..."
  kill $pids 2>/dev/null || true
  sleep 1
  pids="$(listeners)"
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || true
    sleep 0.5
  fi
}

if is_healthy; then
  if ! curl -sf --max-time 3 "$URL" | grep -q 'basement-media'; then
    echo "Dashboard on :$PORT is stale (missing Basement media preset) — syncing and restarting…"
    bash "$SCRIPT_DIR/sync-to-live-vault.sh"
    stop_listeners
  else
    echo "Homelab Network Map is already running."
    echo "Opening: $URL"
    open "$URL"
    read -r -p "Press Enter to close..."
    exit 0
  fi
fi

if [ -n "$(listeners)" ]; then
  echo "Port $PORT is in use but not responding — restarting..."
  stop_listeners
fi

echo "Homelab Network Map — live dashboard"
echo "Opening: $URL"
echo "Leave this window open. Press Ctrl+C to stop the server."
echo ""

exec python3 generate_network_map.py --serve --bind 127.0.0.1
