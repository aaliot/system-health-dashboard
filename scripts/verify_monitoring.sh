#!/usr/bin/env bash
# Usage: scripts/verify_monitoring.sh <environment> [prometheus_url]
# Confirms Prometheus reports the environment's target as UP.
set -euo pipefail

ENVIRONMENT="${1:?usage: verify_monitoring.sh <environment> [prometheus_url]}"
PROM_URL="${2:-http://prometheus:9090}"
QUERY="up{job=\"system-health\",environment=\"${ENVIRONMENT}\"}"

for attempt in $(seq 1 12); do
  VALUE="$(curl -fsS -G "$PROM_URL/api/v1/query" --data-urlencode "query=$QUERY" \
    | python3 -c 'import sys, json; r = json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else "none")')" || VALUE="error"
  echo "Attempt $attempt: up{environment=\"$ENVIRONMENT\"} = $VALUE"
  if [ "$VALUE" = "1" ]; then
    echo "PASS: Prometheus reports the $ENVIRONMENT target UP"
    exit 0
  fi
  sleep 5
done

echo "FAIL: Prometheus does not report the $ENVIRONMENT target UP"
exit 1
