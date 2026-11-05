#!/usr/bin/env bash
# Usage: scripts/smoke_test.sh <base_url>
# Checks /health, /version and /metrics. Exits non-zero on the first failure.
set -euo pipefail

BASE_URL="${1:?usage: smoke_test.sh <base_url>}"

wait_for_health() {
  for _ in $(seq 1 30); do
    if curl -fsS "$BASE_URL/health" > /dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "FAIL: $BASE_URL/health not reachable after 60s"
  return 1
}

check() {
  local path="$1" expected="$2" body
  body="$(curl -fsS "$BASE_URL$path")" || { echo "FAIL: $path returned an error"; exit 1; }
  if echo "$body" | grep -q "$expected"; then
    echo "PASS: $path contains $expected"
  else
    echo "FAIL: $path did not contain $expected"
    exit 1
  fi
}

echo "Smoke testing $BASE_URL"
wait_for_health
check /health '"UP"'
check /version '"version"'
check /metrics 'http_requests_total'
echo "All smoke checks passed for $BASE_URL"
