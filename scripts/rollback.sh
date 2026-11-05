#!/usr/bin/env bash
# Usage: scripts/rollback.sh <staging|production>
# Redeploys the previously recorded image tag.
set -euo pipefail

ENV_NAME="${1:?usage: rollback.sh <staging|production>}"
STATE_DIR="${STATE_DIR:-.release-state}"
PREV_FILE="$STATE_DIR/${ENV_NAME}.previous"

if [ ! -s "$PREV_FILE" ]; then
  echo "No previous tag recorded for $ENV_NAME, cannot roll back"
  exit 1
fi

PREV_TAG="$(cat "$PREV_FILE")"
echo "Rolling back $ENV_NAME to system-health-dashboard:$PREV_TAG"
"$(dirname "$0")/deploy.sh" "$ENV_NAME" "$PREV_TAG"
echo "Running image after rollback: $(docker inspect --format '{{.Config.Image}}' "app-${ENV_NAME}")"
