#!/bin/bash
set -euo pipefail

CAM_ID="${CAM_ID:-cam01}"
DEST_IP="${DEST_IP:-ambient-host}"
DEST_PORT="${DEST_PORT:-5001}"

BITRATE=2000000
FRAMERATE=15
KEYFRAME_INTERVAL=30

CAMERA_CMD=""
if command -v rpicam-vid >/dev/null 2>&1; then
  CAMERA_CMD="rpicam-vid"
elif command -v libcamera-vid >/dev/null 2>&1; then
  CAMERA_CMD="libcamera-vid"
else
  echo "Missing camera app: install rpicam-vid or libcamera-vid"
  exit 1
fi

exec "${CAMERA_CMD}" \
  -t 0 \
  --width 1280 \
  --height 720 \
  --framerate ${FRAMERATE} \
  --codec h264 \
  --bitrate ${BITRATE} \
  --inline \
  --keyframe ${KEYFRAME_INTERVAL} \
  --flush \
  -o - | \
  gst-launch-1.0 -v \
    fdsrc ! h264parse config-interval=1 ! \
    udpsink host=${DEST_IP} port=${DEST_PORT}
