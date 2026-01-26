#!/bin/bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
INSTALL_SYSTEM_DEPS="${INSTALL_SYSTEM_DEPS:-1}"

usage() {
  cat <<EOF
Usage: setup-venv.sh [--python python3.12] [--venv .venv] [--no-system-deps]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON_BIN="$2"; shift 2 ;;
    --venv) VENV_DIR="$2"; shift 2 ;;
    --no-system-deps) INSTALL_SYSTEM_DEPS="0"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if [[ "${INSTALL_SYSTEM_DEPS}" == "1" ]]; then
  if command -v brew >/dev/null 2>&1; then
    brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly opencv
  else
    echo "Homebrew not found. Install GStreamer and OpenCV manually, or re-run with --no-system-deps."
  fi
fi

${PYTHON_BIN} -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r mac/requirements.txt

echo "Done. Activate with: source ${VENV_DIR}/bin/activate"
