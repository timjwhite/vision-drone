#!/bin/bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"
CONFIG_PATH="${CONFIG_PATH:-mac/config/ingest.yaml}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Venv not found at ${VENV_DIR}. Run: ./scripts/setup-venv.sh --python python3.12"
  exit 1
fi

source "${VENV_DIR}/bin/activate"

exec python3 mac/main.py --ingest-only --config "${CONFIG_PATH}"
