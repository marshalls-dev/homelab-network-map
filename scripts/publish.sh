#!/bin/bash
# Create GitHub repo and push (run once from Terminal on your Mac).
set -euo pipefail
cd "$(dirname "$0")/.."
REPO_NAME="${1:-homelab-network-map}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh && gh auth login"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login"
  exit 1
fi

if ! gh repo view "$REPO_NAME" >/dev/null 2>&1; then
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --description "Live 3D homelab network map + Obsidian vault (Home Assistant, Helix router, LAN ARP)"
  echo "Created https://github.com/$(gh api user -q .login)/$REPO_NAME"
else
  git remote add origin "https://github.com/$(gh api user -q .login)/$REPO_NAME.git" 2>/dev/null || true
fi

git push -u origin main
echo "Done."
