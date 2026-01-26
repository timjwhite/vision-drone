import argparse
import random
import time
from dataclasses import dataclass
from typing import List

import cv2

from ingest import CameraManager
from fusion import FeatureFusion
from music import MusicEngine
from music.events import MidiEvent
from midi.output import MidiOutput
from vision import VisionEngine


@dataclass
class IngestConfig:
    cameras: List[dict]
    tick_interval: float = 0.1
    music: dict = None
    midi: dict = None
    vision: dict = None
    fusion: dict = None


def load_config(path: str) -> IngestConfig:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for config loading. Install with: pip install pyyaml") from exc

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    return IngestConfig(
        cameras=raw.get("cameras", []),
        tick_interval=float(raw.get("tick_interval", 0.1)),
        music=raw.get("music", {}),
        midi=raw.get("midi", {}),
        vision=raw.get("vision", {}),
        fusion=raw.get("fusion", {}),
    )


def run_ingest_only(config: IngestConfig) -> None:
    camera_manager = CameraManager(config.cameras)
    camera_manager.start()

    last_print = 0.0
    try:
        while True:
            frames = camera_manager.get_latest_frames()
            now = time.time()
            if now - last_print >= 1.0:
                connected = sum(1 for f in frames.values() if f["connected"])
                total = len(frames)
                print(f"ingest: {connected}/{total} connected")
                last_print = now
            time.sleep(config.tick_interval)
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()


def run_pipeline(config: IngestConfig) -> None:
    camera_manager = CameraManager(config.cameras)
    vision_engine = VisionEngine(config.vision or {})
    fusion_engine = FeatureFusion(config.fusion or {})
    music_engine = MusicEngine(config.music or {})
    midi_out = MidiOutput(config.midi or {})

    camera_manager.start()
    midi_out.open()
    try:
        while True:
            frames = camera_manager.get_latest_frames()
            vision_results = vision_engine.process(frames)
            features = fusion_engine.update(vision_results)
            events = music_engine.generate(features)
            midi_out.send(events)
            time.sleep(config.tick_interval)
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()
        midi_out.close()


def run_midi_test(config: IngestConfig) -> None:
    music_engine = MusicEngine(config.music or {})
    midi_out = MidiOutput(config.midi or {})
    midi_out.open()

    scale_notes = music_engine.scale_notes
    last_note_time = 0.0
    last_note = None
    try:
        while True:
            now = time.time()
            if (now - last_note_time) >= 1.0:
                if last_note is not None:
                    midi_out.send([MidiEvent(type="note_off", note=last_note, velocity=0)])
                note = random.choice(scale_notes)
                velocity = random.randint(30, 100)
                print(f"midi-test: note_on {note} vel={velocity}")
                midi_out.send([MidiEvent(type="note_on", note=note, velocity=velocity)])
                last_note = note
                last_note_time = now
            time.sleep(config.tick_interval)
    except KeyboardInterrupt:
        pass
    finally:
        midi_out.close()


def run_vision_test(config: IngestConfig) -> None:
    camera_manager = CameraManager(config.cameras)
    vision_engine = VisionEngine(config.vision or {})
    camera_manager.start()

    last_print = 0.0
    try:
        while True:
            frames = camera_manager.get_latest_frames()
            results = vision_engine.process(frames)
            now = time.time()
            if now - last_print >= 1.0:
                counts = {sid: len(people) for sid, people in results.items()}
                print(f"vision: {counts}")
                last_print = now
            time.sleep(config.tick_interval)
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()


def run_vision_file_test(config: IngestConfig, path: str) -> None:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video file: {path}")

    vision_engine = VisionEngine(config.vision or {})
    last_print = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            payload = {"frame": frame, "timestamp": time.time(), "connected": True}
            results = vision_engine.process({"file": payload})
            now = time.time()
            if now - last_print >= 1.0:
                count = len(results.get("file", []))
                print(f"vision-file: {count}")
                last_print = now
            time.sleep(config.tick_interval)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/ingest.yaml", help="Path to ingest config")
    parser.add_argument("--ingest-only", action="store_true", help="Run ingest loop only")
    parser.add_argument("--midi-test", action="store_true", help="Run synthetic MIDI test only")
    parser.add_argument("--vision-test", action="store_true", help="Run vision motion test only")
    parser.add_argument("--vision-file", default="", help="Run vision test on a local video file")
    parser.add_argument("--vision-test-file", action="store_true", help="Run vision test on mac/test.mp4")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.ingest_only:
        run_ingest_only(config)
        return
    if args.midi_test:
        run_midi_test(config)
        return
    if args.vision_test:
        run_vision_test(config)
        return
    if args.vision_file:
        run_vision_file_test(config, args.vision_file)
        return
    if args.vision_test_file:
        run_vision_file_test(config, "mac/test.mp4")
        return

    run_pipeline(config)


if __name__ == "__main__":
    main()
