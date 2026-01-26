from dataclasses import dataclass
from typing import Dict, List

from .features import GlobalFeatures
from vision.types import PersonState


@dataclass
class FusionConfig:
    velocity_slow: float = 10.0
    velocity_medium: float = 30.0
    velocity_fast: float = 60.0
    max_energy: float = 10.0
    ema_alpha: float = 0.3


class FeatureFusion:
    def __init__(self, config: dict):
        self.cfg = FusionConfig(
            velocity_slow=float(config.get("velocity_slow", 10.0)),
            velocity_medium=float(config.get("velocity_medium", 30.0)),
            velocity_fast=float(config.get("velocity_fast", 60.0)),
            max_energy=float(config.get("max_energy", 10.0)),
            ema_alpha=float(config.get("ema_alpha", 0.3)),
        )
        self._last = GlobalFeatures()

    def update(self, vision_results: Dict[str, List[PersonState]]) -> GlobalFeatures:
        people: List[PersonState] = []
        for states in vision_results.values():
            people.extend(states)

        total = len(people)
        if total == 0:
            return self._smooth(GlobalFeatures())

        movement_energy = sum(p.velocity for p in people)
        stationary_count = sum(1 for p in people if p.stationary)
        phone_count = sum(1 for p in people if p.has_phone)

        slow = sum(1 for p in people if (p.velocity >= self.cfg.velocity_slow and p.velocity < self.cfg.velocity_medium))
        medium = sum(1 for p in people if (p.velocity >= self.cfg.velocity_medium and p.velocity < self.cfg.velocity_fast))
        fast = sum(1 for p in people if p.velocity >= self.cfg.velocity_fast)

        features = GlobalFeatures(
            total_people=total,
            movement_energy=min(movement_energy, self.cfg.max_energy),
            stationary_ratio=stationary_count / total,
            phone_ratio=phone_count / total,
            slow_count=slow,
            medium_count=medium,
            fast_count=fast,
        )
        return self._smooth(features)

    def _smooth(self, current: GlobalFeatures) -> GlobalFeatures:
        a = self.cfg.ema_alpha
        last = self._last

        smoothed = GlobalFeatures(
            total_people=current.total_people,
            movement_energy=(a * current.movement_energy) + ((1 - a) * last.movement_energy),
            stationary_ratio=(a * current.stationary_ratio) + ((1 - a) * last.stationary_ratio),
            phone_ratio=(a * current.phone_ratio) + ((1 - a) * last.phone_ratio),
            slow_count=current.slow_count,
            medium_count=current.medium_count,
            fast_count=current.fast_count,
        )
        self._last = smoothed
        return smoothed
