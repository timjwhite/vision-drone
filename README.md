# vision-drone
Art project to capture moving images and output MIDI signal for performance installations.

## macOS install + run (ingest)
This section is kept up to date as modules are added.

### System requirements
- macOS 12+ (recommended)
- Python 3.12
- GStreamer 1.0
- OpenCV built with GStreamer backend

### Install (suggested)
```bash
# Python deps
./scripts/setup-venv.sh --python python3.12

# GStreamer + OpenCV (brew example)
brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly opencv
```

### Run ingest
```bash
./scripts/run-mac.sh
```

### MIDI test (no vision required)
Enable the macOS IAC Driver and create a bus named `IAC Driver Bus 1`, then run:

```bash
python3 mac/main.py --midi-test --config mac/config/ingest.yaml
```

### Vision test (motion-only)
Requires ingest + GStreamer. It prints a per-stream count of motion tracks:

```bash
python3 mac/main.py --vision-test --config mac/config/ingest.yaml
```

### YOLO person detection (recommended)
The vision module supports YOLO for person detection. The first run will download the model file if needed.
Set `vision.detector: yolo` and `vision.model: yolov8n.pt` in `mac/config/ingest.yaml`.

### Vision test on local file
If you have `mac/test.mp4`, run:

```bash
python3 mac/main.py --vision-test-file --config mac/config/ingest.yaml
```

### Vision test on local file + MIDI
If you want MIDI output driven by the file:

```bash
python3 mac/main.py --vision-test-file-midi --config mac/config/ingest.yaml
```

### UDP test harness (send a movie from any machine)
From any machine with `ffmpeg`, publish a file:

```bash
./scripts/publish-test-mp4.sh /path/to/test.mp4 ambient-host 5001
```

Then run ingest (on the Mac):

```bash
./scripts/run-mac.sh
```

### Notes
- `opencv-python` is installed via pip to provide `cv2`.
- For UDP ingest, OpenCV must be built with GStreamer enabled (brew OpenCV is recommended on macOS).
- Update `mac/config/ingest.yaml` with your camera UDP ports.

Check whether your OpenCV has GStreamer:
```bash
./scripts/check-opencv-gstreamer.sh
```
