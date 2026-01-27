# Pi Node Streaming

## Requirements
- Raspberry Pi Zero 2 W + CSI camera
- Raspberry Pi OS Lite
- `libcamera` + `gstreamer1.0`

Note: Do not use `perl` for any scripts in this project. Use `sed` or other POSIX tools instead.

## Stream command (libcamera-vid → GStreamer → UDP)
The stream is produced by `libcamera-vid` and sent as raw H.264 over UDP via `gst-launch-1.0`.

```bash
libcamera-vid -t 0 --width 1280 --height 720 --framerate 15 \
  --codec h264 --bitrate 2000000 --inline --keyframe 30 --flush -o - | \
gst-launch-1.0 -v fdsrc ! h264parse config-interval=1 ! \
  udpsink host=mac.local port=5001
```

## Hostname + Stream ID
Each node must have a unique hostname and UDP port:

```bash
sudo hostnamectl set-hostname cam-01
```

Stream ID is derived from `CAM_ID` and mapped to a UDP port, e.g.:
- `CAM_ID=cam01` → port `5001`
- `CAM_ID=cam02` → port `5002`

Update `pi-node/stream.sh` and `pi-node/stream.service` to match:
- `CAM_ID`
- `DEST_IP`
- `DEST_PORT` (UDP port)

## Install systemd service

```bash
sudo mkdir -p /home/pi/pi-node
sudo cp -r /path/to/vision-drone/pi-node/* /home/pi/pi-node/

sudo cp /home/pi/pi-node/stream.service /etc/systemd/system/stream.service
sudo systemctl daemon-reload
sudo systemctl enable --now stream.service
```

Check status:

```bash
sudo systemctl status stream.service
```

## Optional helpers

### Automated install
```bash
chmod +x /home/pi/pi-node/install.sh
sudo /home/pi/pi-node/install.sh --cam-id cam01 --hostname cam-01 --dest-ip ambient-host
```

### Generate per-camera configs
```bash
chmod +x /home/pi/pi-node/generate-cam-configs.sh
/home/pi/pi-node/generate-cam-configs.sh --count 4 --dest-ip ambient-host
```

### Stream health check
```bash
chmod +x /home/pi/pi-node/stream-healthcheck.sh
/home/pi/pi-node/stream-healthcheck.sh stream.service
```

### Health check timer (systemd)
The install script enables a systemd timer that runs the health check every 30 seconds.
If the check fails, the stream service is restarted automatically.
Restarts are rate-limited to once per 60 seconds to avoid swamping the Pi.

```bash
sudo systemctl status stream-healthcheck.timer
sudo systemctl list-timers --all | grep stream-healthcheck
```

```bash
sudo systemctl status stream-healthcheck.timer
sudo systemctl list-timers --all | grep stream-healthcheck
```
