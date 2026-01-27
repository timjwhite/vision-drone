#!/bin/bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"
CONFIG_PATH="${CONFIG_PATH:-mac/config/ingest.yaml}"
GST_FRAMEWORK="${GST_FRAMEWORK:-/Library/Frameworks/GStreamer.framework}"

if [[ -d "${GST_FRAMEWORK}" ]]; then
  export PATH="${GST_FRAMEWORK}/Commands:${PATH}"
  export DYLD_FALLBACK_LIBRARY_PATH="${GST_FRAMEWORK}/Libraries:${DYLD_FALLBACK_LIBRARY_PATH:-}"
  export GST_PLUGIN_PATH="${GST_FRAMEWORK}/Libraries/gstreamer-1.0"
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Venv not found at ${VENV_DIR}. Run: ./scripts/setup-venv.sh --python python3.12"
  exit 1
fi

source "${VENV_DIR}/bin/activate"

exec python3 mac/main.py --ingest-only --config "${CONFIG_PATH}"
