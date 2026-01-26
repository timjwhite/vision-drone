from dataclasses import dataclass


@dataclass
class GlobalFeatures:
    total_people: int = 0
    movement_energy: float = 0.0
    stationary_ratio: float = 0.0
    phone_ratio: float = 0.0
    slow_count: int = 0
    medium_count: int = 0
    fast_count: int = 0
