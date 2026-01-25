#!/bin/bash
set -euo pipefail

COUNT=1
DEST_IP="mac.local"
DEST_PORT="8554"
OUT_DIR="./out"

usage() {
  cat <<EOF
Usage: generate-cam-configs.sh --count N [--dest-ip mac.local] [--dest-port 8554] [--out-dir ./out]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count) COUNT="$2"; shift 2 ;;
    --dest-ip) DEST_IP="$2"; shift 2 ;;
    --dest-port) DEST_PORT="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

mkdir -p "${OUT_DIR}"

for i in $(seq -w 1 "${COUNT}"); do
  CAM_ID="cam${i}"
  HOSTNAME="cam-${i}"
  CAM_DIR="${OUT_DIR}/${CAM_ID}"
  mkdir -p "${CAM_DIR}"

  cat > "${CAM_DIR}/env.sh" <<EOF
CAM_ID="${CAM_ID}"
DEST_IP="${DEST_IP}"
DEST_PORT="${DEST_PORT}"
HOSTNAME="${HOSTNAME}"
EOF

  cat > "${CAM_DIR}/install.sh" <<EOF
#!/bin/bash
set -euo pipefail
sudo /home/pi/pi-node/install.sh --cam-id ${CAM_ID} --hostname ${HOSTNAME} --dest-ip ${DEST_IP} --dest-port ${DEST_PORT}
EOF

  chmod +x "${CAM_DIR}/install.sh"
done

echo "Wrote ${COUNT} configs to ${OUT_DIR}"
