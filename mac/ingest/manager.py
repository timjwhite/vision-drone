from typing import Dict, Iterable, List, Optional

from .camera_stream import CameraStream


class CameraManager:
    def __init__(self, camera_configs: Iterable[dict]):
        self._streams: Dict[str, CameraStream] = {}
        for cfg in camera_configs:
            stream = CameraStream(
                stream_id=cfg["id"],
                rtsp_url=cfg["rtsp_url"],
                latency_ms=cfg.get("latency_ms", 200),
                protocol=cfg.get("protocol", "tcp"),
                reconnect_interval_s=cfg.get("reconnect_interval_s", 2.0),
            )
            self._streams[stream.stream_id] = stream

    def start(self) -> None:
        for stream in self._streams.values():
            stream.start()

    def stop(self) -> None:
        for stream in self._streams.values():
            stream.stop()

    def get_latest_frames(self) -> Dict[str, dict]:
        frames: Dict[str, dict] = {}
        for stream_id, stream in self._streams.items():
            frame, ts, connected = stream.get_latest()
            frames[stream_id] = {
                "frame": frame,
                "timestamp": ts,
                "connected": connected,
            }
        return frames

    def get_stream(self, stream_id: str) -> Optional[CameraStream]:
        return self._streams.get(stream_id)

    def list_stream_ids(self) -> List[str]:
        return list(self._streams.keys())
