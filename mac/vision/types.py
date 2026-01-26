from dataclasses import dataclass
from typing import Tuple


@dataclass
class PersonState:
    track_id: int
    position: Tuple[float, float]
    velocity: float
    stationary: bool
    has_phone: bool
    last_seen: float
