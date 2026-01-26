import argparse
import time
from dataclasses import dataclass
from typing import List

from ingest import CameraManager


@dataclass
class IngestConfig:
    cameras: List[dict]
    tick_interval: float = 0.1


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/ingest.yaml", help="Path to ingest config")
    parser.add_argument("--ingest-only", action="store_true", help="Run ingest loop only")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.ingest_only:
        run_ingest_only(config)
        return

    raise RuntimeError("Full pipeline not wired yet. Use --ingest-only for now.")


if __name__ == "__main__":
    main()
