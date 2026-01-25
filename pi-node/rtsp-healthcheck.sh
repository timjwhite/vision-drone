#!/bin/bash
set -euo pipefail

URL=""
TIMEOUT_SECONDS=5
RESTART_SERVICE=""
RESTART_COOLDOWN_SECONDS=60
RESTART_STATE_FILE="/tmp/rtsp-healthcheck-restart.state"

usage() {
  cat <<EOF
Usage: rtsp-healthcheck.sh --url rtsp://host:8554/cam01 [--timeout 5]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url) URL="$2"; shift 2 ;;
    --timeout) TIMEOUT_SECONDS="$2"; shift 2 ;;
    --restart-service) RESTART_SERVICE="$2"; shift 2 ;;
    --restart-cooldown) RESTART_COOLDOWN_SECONDS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "${URL}" ]]; then
  echo "Missing --url"
  usage
  exit 2
fi

if ! command -v gst-launch-1.0 >/dev/null 2>&1; then
  echo "gst-launch-1.0 not found"
  exit 3
fi

if ! command -v timeout >/dev/null 2>&1; then
  echo "timeout not found"
  exit 4
fi

set +e
timeout "${TIMEOUT_SECONDS}" gst-launch-1.0 -q \
  rtspsrc location="${URL}" protocols=tcp latency=200 ! \
  rtph264depay ! h264parse ! fakesink sync=false
STATUS=$?
set -e

if [[ "${STATUS}" -eq 0 ]]; then
  echo "OK"
  exit 0
fi

if [[ -n "${RESTART_SERVICE}" ]] && command -v systemctl >/dev/null 2>&1; then
  NOW_EPOCH="$(date +%s)"
  LAST_RESTART=0
  if [[ -f "${RESTART_STATE_FILE}" ]]; then
    LAST_RESTART="$(cat "${RESTART_STATE_FILE}" 2>/dev/null || echo 0)"
  fi

  if [[ $((NOW_EPOCH - LAST_RESTART)) -ge "${RESTART_COOLDOWN_SECONDS}" ]]; then
    systemctl restart "${RESTART_SERVICE}" || true
    echo "${NOW_EPOCH}" > "${RESTART_STATE_FILE}"
  else
    echo "RESTART-SKIP (cooldown ${RESTART_COOLDOWN_SECONDS}s)"
  fi
fi

if [[ "${STATUS}" -eq 124 ]]; then
  echo "TIMEOUT"
  exit 1
fi

echo "FAIL (${STATUS})"
exit 1
