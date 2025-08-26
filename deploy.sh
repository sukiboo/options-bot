#!/usr/bin/env bash
set -euo pipefail


SERVER_USER="suki"
SERVER_HOST="vultr"
REPO_URL="git@github.com:sukiboo/options-bot.git"
IMAGE_NAME="options-bot"
ENV_LOCAL_PATH="./.env"


if [[ ! -f "$ENV_LOCAL_PATH" ]]; then
  echo "ERROR: $ENV_LOCAL_PATH not found."
  exit 1
fi

echo "==> Ensure remote dirs exist"
ssh "${SERVER_USER}@${SERVER_HOST}" 'mkdir -p ~/scripts/options-bot'

echo "==> Copy .env to server"
scp "$ENV_LOCAL_PATH" "${SERVER_USER}@${SERVER_HOST}:~/scripts/options-bot/.env"
ssh "${SERVER_USER}@${SERVER_HOST}" 'chmod 600 ~/scripts/options-bot/.env'

echo "==> Pull latest code on server & build/run"
ssh "${SERVER_USER}@${SERVER_HOST}" bash -lc '
  set -euo pipefail
  APPDIR="$HOME/apps/options-bot"
  SCRIPTDIR="$HOME/scripts/options-bot"

  # Clone or update repo
  if [[ ! -d "$APPDIR/.git" ]]; then
    git clone "'"$REPO_URL"'" "$APPDIR"
  fi
  git -C "$APPDIR" fetch --prune --tags
  # checkout default branch (origin/HEAD) and pull
  DEFAULT_BRANCH=$(git -C "$APPDIR" rev-parse --abbrev-ref origin/HEAD | sed "s|origin/||")
  git -C "$APPDIR" checkout -q "$DEFAULT_BRANCH"
  git -C "$APPDIR" pull --ff-only

  # Build fresh image
  docker rm -f "'"$IMAGE_NAME"'" >/dev/null 2>&1 || true
  cd "$APPDIR"
  docker build -t "'"$IMAGE_NAME"':latest" .

  # One-shot run: sends message then exits; --rm cleans container
  docker run --rm \
    --name "'"$IMAGE_NAME"'" \
    --env-file "$SCRIPTDIR/.env" \
    -v "$APPDIR/logs:/app/logs" \
    "'"$IMAGE_NAME"':latest"
'

echo "==> Done."
