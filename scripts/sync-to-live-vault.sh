#!/usr/bin/env bash
# Push homelab-network-map repo → ~/HomelabNetwork (the live Obsidian vault + :8765 server).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LIVE="${HOMELAB_VAULT:-$HOME/HomelabNetwork}"

if [[ ! -d "$LIVE" ]]; then
  echo "Live vault not found: $LIVE"
  echo "Set HOMELAB_VAULT or create ~/HomelabNetwork"
  exit 1
fi

echo "Syncing $REPO → $LIVE"
rsync -av \
  --exclude '.git' \
  --exclude '.obsidian' \
  --exclude '__pycache__' \
  --exclude 'ha-token.local' \
  --exclude 'jellyfin.local' \
  --exclude 'node-positions.json' \
  --exclude 'router-online.json' \
  --exclude 'router-clients.json' \
  --exclude '.DS_Store' \
  "$REPO/" "$LIVE/"

echo "Regenerating map in live vault…"
(cd "$LIVE" && python3 generate_network_map.py)

echo "Done. Restart the :8765 dashboard (or hard-refresh) to pick up Basement media + projector layout."
