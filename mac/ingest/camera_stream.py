import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import io
import numpy as np

try:
    import av
except Exception:  # pragma: no cover - optional dependency
    av = None


def build_gstreamer_pipeline(
    rtsp_url: Optional[str],
    latency_ms: int = 200,
    protocol: str = "udp",
    udp_port: Optional[int] = None,
) -> str:
    protocol = protocol.lower()
    if protocol == "udp":
        if udp_port is None:
            raise ValueError("udp_port is required when protocol=udp")
        return (
            "udpsrc port={port} caps=\"application/x-rtp, media=video, "
            "encoding-name=H264, payload=96, clock-rate=90000\" ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "appsink drop=true max-buffers=1 sync=false"
        ).format(port=udp_port)

    protocols = "tcp" if protocol == "tcp" else "udp"
    if not rtsp_url:
        raise ValueError("rtsp_url is required when protocol=rtsp")
    return (
        f"rtspsrc location={rtsp_url} protocols={protocols} latency={latency_ms} ! "
        "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


@dataclass
class CameraStream:
    stream_id: str
    rtsp_url: Optional[str] = None
    latency_ms: int = 200
    protocol: str = "udp"
    udp_port: Optional[int] = None
    reconnect_interval_s: float = 2.0
    use_pyav: bool = True

    last_frame: Optional[object] = None
    last_timestamp: float = 0.0
    connected: bool = False

    _thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name=f"CameraStream-{self.stream_id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_latest(self):
        with self._lock:
            return self.last_frame, self.last_timestamp, self.connected

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        pipeline = build_gstreamer_pipeline(
            self.rtsp_url,
            self.latency_ms,
            self.protocol,
            self.udp_port,
        )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap is None or not cap.isOpened():
            return None
        return cap

    def _run(self) -> None:
        if self.protocol == "udp" and self.use_pyav:
            self._run_pyav()
            return

        cap: Optional[cv2.VideoCapture] = None
        while not self._stop_event.is_set():
            if cap is None:
                cap = self._open_capture()
                if cap is None:
                    self._set_connected(False)
                    time.sleep(self.reconnect_interval_s)
                    continue
                self._set_connected(True)

            ok, frame = cap.read()
            if not ok or frame is None:
                self._set_connected(False)
                cap.release()
                cap = None
                time.sleep(self.reconnect_interval_s)
                continue

            ts = time.time()
            with self._lock:
                self.last_frame = frame
                self.last_timestamp = ts
                self.connected = True

        if cap is not None:
            cap.release()

    def _run_pyav(self) -> None:
        if av is None:
            raise RuntimeError("PyAV is not installed. Install with: pip install av")
        if self.udp_port is None:
            raise ValueError("udp_port is required for PyAV UDP ingest")

        while not self._stop_event.is_set():
            try:
                container = self._open_pyav()
            except Exception:
                self._set_connected(False)
                time.sleep(self.reconnect_interval_s)
                continue

            self._set_connected(True)
            try:
                for frame in container.decode(video=0):
                    if self._stop_event.is_set():
                        break
                    img = frame.to_ndarray(format="bgr24")
                    ts = time.time()
                    with self._lock:
                        self.last_frame = img
                        self.last_timestamp = ts
                        self.connected = True
            except Exception:
                self._set_connected(False)
            finally:
                try:
                    container.close()
                except Exception:
                    pass
            time.sleep(self.reconnect_interval_s)

    def _set_connected(self, is_connected: bool) -> None:
        with self._lock:
            self.connected = is_connected

    def _open_pyav(self):
        url = f"udp://0.0.0.0:{self.udp_port}"
        options = {
            "fflags": "nobuffer",
            "flags": "low_delay",
            "probesize": "32",
            "analyzeduration": "0",
        }
        return av.open(url, format="h264", options=options)
