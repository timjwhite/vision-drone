#!/bin/bash
set -euo pipefail

CAM_ID="${CAM_ID:-cam01}"
DEST_IP="${DEST_IP:-mac.local}"
DEST_PORT="${DEST_PORT:-8554}"
STREAM_PATH="/${CAM_ID}"

BITRATE=2000000
FRAMERATE=15
KEYFRAME_INTERVAL=30

exec libcamera-vid \
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
    rtspclientsink location=rtsp://${DEST_IP}:${DEST_PORT}${STREAM_PATH}
