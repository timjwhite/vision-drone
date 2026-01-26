#!/bin/bash
set -euo pipefail

STREAM_SERVICE="${1:-stream.service}"
RESTART_COOLDOWN_SECONDS=60
RESTART_STATE_FILE="/tmp/stream-healthcheck-restart.state"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found"
  exit 3
fi

set +e
systemctl is-active --quiet "${STREAM_SERVICE}"
STATUS=$?
set -e

if [[ "${STATUS}" -eq 0 ]]; then
  echo "OK"
  exit 0
fi

NOW_EPOCH="$(date +%s)"
LAST_RESTART=0
if [[ -f "${RESTART_STATE_FILE}" ]]; then
  LAST_RESTART="$(cat "${RESTART_STATE_FILE}" 2>/dev/null || echo 0)"
fi

if [[ $((NOW_EPOCH - LAST_RESTART)) -ge "${RESTART_COOLDOWN_SECONDS}" ]]; then
  systemctl restart "${STREAM_SERVICE}" || true
  echo "${NOW_EPOCH}" > "${RESTART_STATE_FILE}"
  echo "RESTART"
else
  echo "RESTART-SKIP (cooldown ${RESTART_COOLDOWN_SECONDS}s)"
fi

exit 1
