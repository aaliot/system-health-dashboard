#!/usr/bin/env bash
# Usage: scripts/deploy.sh <staging|production> <image_tag>
# Deploys an existing image tag to the environment's Compose project and
# records the tag that was running before, so rollback is possible.
set -euo pipefail

ENV_NAME="${1:?usage: deploy.sh <staging|production> <image_tag>}"
TAG="${2:?usage: deploy.sh <staging|production> <image_tag>}"
STATE_DIR="${STATE_DIR:-.release-state}"
COMPOSE_FILE="docker-compose.${ENV_NAME}.yml"
CONTAINER="app-${ENV_NAME}"

mkdir -p "$STATE_DIR"

# Only one deploy per environment at a time, even across different branch builds.
# The lock is released automatically when this script exits.
exec 9>"$STATE_DIR/${ENV_NAME}.lock"
flock 9

if docker inspect "$CONTAINER" > /dev/null 2>&1; then
  RUNNING_IMAGE="$(docker inspect --format '{{.Config.Image}}' "$CONTAINER")"
  RUNNING_TAG="${RUNNING_IMAGE##*:}"
  if [ "$RUNNING_TAG" != "$TAG" ]; then
    echo "$RUNNING_TAG" > "$STATE_DIR/${ENV_NAME}.previous"
    echo "Recorded previous $ENV_NAME tag: $RUNNING_TAG"
  fi
fi

export IMAGE_TAG="$TAG"
docker compose -p "$ENV_NAME" -f "$COMPOSE_FILE" up -d
echo "$TAG" > "$STATE_DIR/${ENV_NAME}.current"
echo "Deployed system-health-dashboard:$TAG to $ENV_NAME"
