#!/bin/bash
set -euo pipefail

CAM_ID="cam01"
HOSTNAME="cam-01"
DEST_IP="ambient-host"
DEST_PORT="5001"

usage() {
  cat <<EOF
Usage: install.sh [--cam-id cam01] [--hostname cam-01] [--dest-ip mac.local] [--dest-port 8554]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cam-id) CAM_ID="$2"; shift 2 ;;
    --hostname) HOSTNAME="$2"; shift 2 ;;
    --dest-ip) DEST_IP="$2"; shift 2 ;;
    --dest-port) DEST_PORT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo $0 ..."
  exit 1
fi

hostnamectl set-hostname "${HOSTNAME}"

mkdir -p /home/pi/pi-node
cp -r "${SCRIPT_DIR}/"* /home/pi/pi-node/

sed -i "s/^CAM_ID=.*/CAM_ID=\"${CAM_ID}\"/" /home/pi/pi-node/stream.sh
sed -i "s/^DEST_IP=.*/DEST_IP=\"${DEST_IP}\"/" /home/pi/pi-node/stream.sh
sed -i "s/^DEST_PORT=.*/DEST_PORT=\"${DEST_PORT}\"/" /home/pi/pi-node/stream.sh

sed -i "s/^Environment=CAM_ID=.*/Environment=CAM_ID=${CAM_ID}/" /home/pi/pi-node/stream.service
sed -i "s/^Environment=DEST_IP=.*/Environment=DEST_IP=${DEST_IP}/" /home/pi/pi-node/stream.service
sed -i "s/^Environment=DEST_PORT=.*/Environment=DEST_PORT=${DEST_PORT}/" /home/pi/pi-node/stream.service

cat > /home/pi/pi-node/healthcheck.env <<EOF
STREAM_SERVICE=stream.service
EOF

cp /home/pi/pi-node/stream.service /etc/systemd/system/stream.service
cp /home/pi/pi-node/stream-healthcheck.service /etc/systemd/system/stream-healthcheck.service
cp /home/pi/pi-node/stream-healthcheck.timer /etc/systemd/system/stream-healthcheck.timer
systemctl daemon-reload
systemctl enable --now stream.service
systemctl enable --now stream-healthcheck.timer

echo "Installed. Stream URL: udp://${DEST_IP}:${DEST_PORT} (${CAM_ID})"
