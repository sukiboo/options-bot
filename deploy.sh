#!/usr/bin/env bash
set -euo pipefail

ENV_LOCAL_PATH="./.env"
SETTINGS_PATH="./settings.yaml"

if [[ ! -f "$ENV_LOCAL_PATH" ]]; then
  echo "ERROR: $ENV_LOCAL_PATH not found."
  exit 1
fi

if [[ ! -f "$SETTINGS_PATH" ]]; then
  echo "ERROR: $SETTINGS_PATH not found."
  exit 1
fi

# Load environment variables from .env
set -a
source "$ENV_LOCAL_PATH"
set +a

# Validate required variables
REQUIRED_VARS=("SERVER_USER" "SERVER_HOST" "SERVER_PATH" "REPO_URL")
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    MISSING_VARS+=("$var")
  fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
  echo "ERROR: Missing required environment variables:"
  printf '  - %s\n' "${MISSING_VARS[@]}"
  exit 1
fi

# Derive IMAGE_NAME and APP_PATH from bot_name in settings.yaml
BOT_NAME=$(grep -E "^bot_name:" "$SETTINGS_PATH" | sed 's/bot_name:[[:space:]]*//' | sed 's/#.*//' | tr -d '[:space:]')
if [[ -z "$BOT_NAME" ]]; then
  echo "ERROR: bot_name not found in $SETTINGS_PATH"
  exit 1
fi
IMAGE_NAME="$BOT_NAME"
APP_PATH="${SERVER_PATH%/}/${BOT_NAME}"

echo "==> 📦 Pull latest code on server"
ssh "${SERVER_USER}@${SERVER_HOST}" << EOF >/dev/null 2>&1
set -euo pipefail
APPDIR="\$HOME/${APP_PATH}"

# Clone or update repo
if [[ ! -d "\$APPDIR/.git" ]]; then
  mkdir -p "\$(dirname "\$APPDIR")"
  git clone "${REPO_URL}" "\$APPDIR" >/dev/null
else
  # Only do git operations if repo already exists
  git -C "\$APPDIR" fetch --prune --tags >/dev/null
  # checkout default branch (origin/HEAD) and pull
  DEFAULT_BRANCH=\$(git -C "\$APPDIR" rev-parse --abbrev-ref origin/HEAD | sed "s|origin/||")
  git -C "\$APPDIR" checkout -q "\$DEFAULT_BRANCH"
  git -C "\$APPDIR" pull --ff-only >/dev/null
fi
EOF

echo "==> 🔑 Copy \`.env\` and \`settings.yaml\` to server"
scp "$ENV_LOCAL_PATH" "${SERVER_USER}@${SERVER_HOST}:~/${APP_PATH}/.env" >/dev/null 2>&1
ssh "${SERVER_USER}@${SERVER_HOST}" "chmod 600 ~/${APP_PATH}/.env" >/dev/null 2>&1
scp "$SETTINGS_PATH" "${SERVER_USER}@${SERVER_HOST}:~/${APP_PATH}/settings.yaml" >/dev/null 2>&1

echo "==> 🚀 Build and run the container"

ssh "${SERVER_USER}@${SERVER_HOST}" << EOF >/dev/null 2>&1
set -euo pipefail
APPDIR="\$HOME/${APP_PATH}"

# Determine Docker command and install if needed
DOCKER_CMD="docker"
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
  DOCKER_CMD="docker"
elif command -v docker &> /dev/null && sudo docker info &> /dev/null 2>&1; then
  DOCKER_CMD="sudo docker"
else
  sudo apt-get update -qq
  sudo apt-get install -y -qq ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo "\$VERSION_CODENAME") stable" | \\
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "\$USER"
  DOCKER_CMD="sudo docker"
fi

# Build fresh image
\$DOCKER_CMD rm -f "${IMAGE_NAME}" >/dev/null 2>&1 || true
cd "\$APPDIR"
\$DOCKER_CMD build -t "${IMAGE_NAME}:latest" . >/dev/null 2>&1

# Run continuously with auto-restart
\$DOCKER_CMD run -d --name "${IMAGE_NAME}" \\
  --restart unless-stopped \\
  --env-file "\$APPDIR/.env" \\
  -v "\$APPDIR/logs:/app/logs" \\
  "${IMAGE_NAME}:latest" >/dev/null 2>&1
EOF

echo "==> ✅ Success"
