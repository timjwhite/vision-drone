#!/bin/bash
set -euo pipefail

INPUT="${1:-mac/test.mp4}"
DEST_HOST="${2:-ambient-host}"
DEST_PORT="${3:-5001}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Install with: brew install ffmpeg"
  exit 1
fi

if [[ ! -f "${INPUT}" ]]; then
  echo "Input file not found: ${INPUT}"
  exit 1
fi

echo "Publishing ${INPUT} to rtp://${DEST_HOST}:${DEST_PORT}"

exec ffmpeg -re -stream_loop -1 -i "${INPUT}" \
  -an -c:v libx264 -preset veryfast -tune zerolatency \
  -x264-params keyint=30:min-keyint=30:scenecut=0:repeat-headers=1 \
  -pix_fmt yuv420p -payload_type 96 -f rtp \
  "rtp://${DEST_HOST}:${DEST_PORT}?pkt_size=1200" -loglevel info
