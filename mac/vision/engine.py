import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2

from .types import PersonState


@dataclass
class TrackData:
    state: PersonState
    last_position: Tuple[float, float]
    last_time: float
    velocity_ema: float


class VisionEngine:
    def __init__(self, config: dict):
        self.detection_interval_s = float(config.get("detection_interval_s", 0.2))
        self.min_area = int(config.get("min_area", 800))
        self.distance_threshold = float(config.get("distance_threshold", 60.0))
        self.max_lost_s = float(config.get("max_lost_s", 1.5))
        self.ema_alpha = float(config.get("ema_alpha", 0.4))
        self.stationary_threshold = float(config.get("stationary_threshold", 5.0))

        self._next_track_id = 1
        self._last_detection_time: Dict[str, float] = {}
        self._trackers: Dict[str, Dict[int, TrackData]] = {}
        self._bg_subs: Dict[str, cv2.BackgroundSubtractor] = {}

    def process(self, frames: Dict[str, dict]) -> Dict[str, List[PersonState]]:
        results: Dict[str, List[PersonState]] = {}
        for stream_id, payload in frames.items():
            frame = payload.get("frame")
            ts = payload.get("timestamp") or time.time()
            if frame is None:
                results[stream_id] = []
                continue

            tracks = self._trackers.setdefault(stream_id, {})
            bg = self._bg_subs.setdefault(stream_id, cv2.createBackgroundSubtractorMOG2(history=200, detectShadows=False))
            last_det = self._last_detection_time.get(stream_id, 0.0)

            detections: List[Tuple[float, float]] = []
            if (ts - last_det) >= self.detection_interval_s:
                detections = self._detect_motion(frame, bg)
                self._last_detection_time[stream_id] = ts

            self._update_tracks(tracks, detections, ts)
            results[stream_id] = [t.state for t in tracks.values()]

        return results

    def _detect_motion(self, frame, bg) -> List[Tuple[float, float]]:
        fg = bg.apply(frame)
        fg = cv2.medianBlur(fg, 5)
        _, th = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        th = cv2.dilate(th, None, iterations=2)
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        points: List[Tuple[float, float]] = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.min_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w / 2.0
            cy = y + h / 2.0
            points.append((cx, cy))
        return points

    def _update_tracks(self, tracks: Dict[int, TrackData], detections: List[Tuple[float, float]], ts: float) -> None:
        unmatched = set(tracks.keys())
        assigned: Dict[int, Tuple[float, float]] = {}

        for det in detections:
            best_id = None
            best_dist = self.distance_threshold
            for track_id, track in tracks.items():
                dx = det[0] - track.last_position[0]
                dy = det[1] - track.last_position[1]
                dist = math.hypot(dx, dy)
                if dist < best_dist:
                    best_dist = dist
                    best_id = track_id
            if best_id is not None:
                assigned[best_id] = det
                if best_id in unmatched:
                    unmatched.remove(best_id)

        for track_id, pos in assigned.items():
            track = tracks[track_id]
            dt = max(1e-3, ts - track.last_time)
            dist = math.hypot(pos[0] - track.last_position[0], pos[1] - track.last_position[1])
            velocity = dist / dt
            velocity_ema = (self.ema_alpha * velocity) + ((1.0 - self.ema_alpha) * track.velocity_ema)
            stationary = velocity_ema < self.stationary_threshold
            track.state.position = pos
            track.state.velocity = velocity_ema
            track.state.stationary = stationary
            track.state.last_seen = ts
            track.last_position = pos
            track.last_time = ts
            track.velocity_ema = velocity_ema

        for track_id in list(unmatched):
            track = tracks[track_id]
            if (ts - track.state.last_seen) > self.max_lost_s:
                tracks.pop(track_id, None)

        for det in detections:
            if det in assigned.values():
                continue
            track_id = self._next_track_id
            self._next_track_id += 1
            state = PersonState(
                track_id=track_id,
                position=det,
                velocity=0.0,
                stationary=True,
                has_phone=False,
                last_seen=ts,
            )
            tracks[track_id] = TrackData(
                state=state,
                last_position=det,
                last_time=ts,
                velocity_ema=0.0,
            )
