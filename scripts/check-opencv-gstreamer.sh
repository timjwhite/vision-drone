#!/bin/bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"

if [[ -d "${VENV_DIR}" ]]; then
  source "${VENV_DIR}/bin/activate"
fi

python3 - <<'PY'
import cv2
info = cv2.getBuildInformation()
has_gst = "GStreamer" in info and "YES" in info.split("GStreamer")[1][:60]
print("OpenCV version:", cv2.__version__)
print("GStreamer enabled:", "YES" if has_gst else "NO")
PY
