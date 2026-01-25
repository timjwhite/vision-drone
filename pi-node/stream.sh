#!/bin/bash

CAM_ID="cam01"
DEST_IP="mac.local"
DEST_PORT=8554
STREAM_PATH="/${CAM_ID}"

exec gst-launch-1.0 \
  libcamerasrc ! \
  video/x-raw,width=1280,height=720,framerate=15/1 ! \
  v4l2h264enc extra-controls="controls,repeat_sequence_header=1" ! \
  h264parse config-interval=1 ! \
  rtspclientsink location=rtsp://${DEST_IP}:${DEST_PORT}${STREAM_PATH}
