#!/bin/bash
set -euo pipefail

CAM_ID="${CAM_ID:-cam01}"
DEST_IP="${DEST_IP:-ambient-host}"
DEST_PORT="${DEST_PORT:-5001}"

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
    rtph264pay pt=96 config-interval=1 ! \
    udpsink host=${DEST_IP} port=${DEST_PORT}
