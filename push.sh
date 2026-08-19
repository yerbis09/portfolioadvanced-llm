#!/usr/bin/env bash
# push.sh — push to GitHub using token from local.settings
# Usage: bash push.sh [branch]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS="$SCRIPT_DIR/local.settings"

if [[ ! -f "$SETTINGS" ]]; then
  echo "ERROR: local.settings not found at $SETTINGS"
  exit 1
fi

# Load settings (ignore comment lines)
while IFS='=' read -r key value; do
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  export "${key}=${value}"
done < "$SETTINGS"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: GITHUB_TOKEN is empty in local.settings"
  exit 1
fi

BRANCH="${1:-master}"

git remote set-url origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
git push origin "$BRANCH"
git remote set-url origin "https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git"

echo "Pushed $BRANCH -> ${GITHUB_USER}/${GITHUB_REPO}"
