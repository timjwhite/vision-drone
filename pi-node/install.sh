#!/bin/bash
set -euo pipefail

CAM_ID="cam01"
HOSTNAME="camera1"
DEST_IP="ambient-host"
DEST_PORT="5001"
INSTALL_USER="pi"

usage() {
  cat <<EOF
Usage: install.sh [--cam-id cam01] [--hostname camera1] [--dest-ip mac.local] [--dest-port 8554] [--user pi]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cam-id) CAM_ID="$2"; shift 2 ;;
    --hostname) HOSTNAME="$2"; shift 2 ;;
    --dest-ip) DEST_IP="$2"; shift 2 ;;
    --dest-port) DEST_PORT="$2"; shift 2 ;;
    --user) INSTALL_USER="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo $0 ..."
  exit 1
fi

missing=0
missing_names=()
if ! command -v gst-launch-1.0 >/dev/null 2>&1; then
  echo "Missing dependency: gst-launch-1.0 (gstreamer1.0)"
  missing=1
  missing_names+=("gstreamer")
fi

if ! command -v rpicam-vid >/dev/null 2>&1 && ! command -v libcamera-vid >/dev/null 2>&1; then
  echo "Missing dependency: rpicam-vid or libcamera-vid (rpicam-apps/libcamera)"
  missing=1
  missing_names+=("camera")
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "Missing dependency: systemctl (systemd)"
  missing=1
  missing_names+=("systemd")
fi

if ! command -v hostnamectl >/dev/null 2>&1; then
  echo "Missing dependency: hostnamectl (systemd)"
  missing=1
  missing_names+=("hostnamectl")
fi

if [[ "${missing}" -ne 0 ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing missing dependencies..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
      gstreamer1.0-tools \
      gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-ugly \
      gstreamer1.0-libav \
      rpicam-apps \
      libcamera-apps \
      systemd
  else
    echo "apt-get not found; install dependencies manually and re-run."
    exit 1
  fi
fi

if ! id -u "${INSTALL_USER}" >/dev/null 2>&1; then
  echo "User not found: ${INSTALL_USER}"
  exit 1
fi

HOME_DIR="$(getent passwd "${INSTALL_USER}" | cut -d: -f6)"
if [[ -z "${HOME_DIR}" ]]; then
  HOME_DIR="/home/${INSTALL_USER}"
fi

NODE_DIR="${HOME_DIR}/pi-node"

hostnamectl set-hostname "${HOSTNAME}"

mkdir -p "${NODE_DIR}"
cp -r "${SCRIPT_DIR}/"* "${NODE_DIR}/"

sed -i "s/^CAM_ID=.*/CAM_ID=\"${CAM_ID}\"/" "${NODE_DIR}/stream.sh"
sed -i "s/^DEST_IP=.*/DEST_IP=\"${DEST_IP}\"/" "${NODE_DIR}/stream.sh"
sed -i "s/^DEST_PORT=.*/DEST_PORT=\"${DEST_PORT}\"/" "${NODE_DIR}/stream.sh"

sed -i "s/^Environment=CAM_ID=.*/Environment=CAM_ID=${CAM_ID}/" "${NODE_DIR}/stream.service"
sed -i "s/^Environment=DEST_IP=.*/Environment=DEST_IP=${DEST_IP}/" "${NODE_DIR}/stream.service"
sed -i "s/^Environment=DEST_PORT=.*/Environment=DEST_PORT=${DEST_PORT}/" "${NODE_DIR}/stream.service"
sed -i "s|^User=.*|User=${INSTALL_USER}|" "${NODE_DIR}/stream.service"
sed -i "s|^Group=.*|Group=${INSTALL_USER}|" "${NODE_DIR}/stream.service"
sed -i "s|^WorkingDirectory=.*|WorkingDirectory=${NODE_DIR}|" "${NODE_DIR}/stream.service"
sed -i "s|^ExecStart=.*|ExecStart=${NODE_DIR}/stream.sh|" "${NODE_DIR}/stream.service"

cat > "${NODE_DIR}/healthcheck.env" <<EOF
STREAM_SERVICE=stream.service
EOF

sed -i "s|^EnvironmentFile=.*|EnvironmentFile=${NODE_DIR}/healthcheck.env|" "${NODE_DIR}/stream-healthcheck.service"
sed -i "s|^ExecStart=.*|ExecStart=${NODE_DIR}/stream-healthcheck.sh "'\${STREAM_SERVICE}'"|" "${NODE_DIR}/stream-healthcheck.service"

cp "${NODE_DIR}/stream.service" /etc/systemd/system/stream.service
cp "${NODE_DIR}/stream-healthcheck.service" /etc/systemd/system/stream-healthcheck.service
cp "${NODE_DIR}/stream-healthcheck.timer" /etc/systemd/system/stream-healthcheck.timer
systemctl daemon-reload
systemctl enable --now stream.service
systemctl enable --now stream-healthcheck.timer

echo "Installed. Stream URL: udp://${DEST_IP}:${DEST_PORT} (${CAM_ID})"
