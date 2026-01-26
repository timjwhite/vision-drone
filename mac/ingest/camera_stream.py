import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2


def build_gstreamer_pipeline(rtsp_url: str, latency_ms: int = 200, protocol: str = "tcp") -> str:
    protocols = "tcp" if protocol.lower() == "tcp" else "udp"
    return (
        f"rtspsrc location={rtsp_url} protocols={protocols} latency={latency_ms} ! "
        "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


@dataclass
class CameraStream:
    stream_id: str
    rtsp_url: str
    latency_ms: int = 200
    protocol: str = "tcp"
    reconnect_interval_s: float = 2.0

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
        pipeline = build_gstreamer_pipeline(self.rtsp_url, self.latency_ms, self.protocol)
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap is None or not cap.isOpened():
            return None
        return cap

    def _run(self) -> None:
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

    def _set_connected(self, is_connected: bool) -> None:
        with self._lock:
            self.connected = is_connected
