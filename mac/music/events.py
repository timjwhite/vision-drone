from dataclasses import dataclass
from typing import Optional


@dataclass
class MidiEvent:
    type: str  # "note_on", "note_off", "cc"
    note: Optional[int] = None
    velocity: Optional[int] = None
    cc: Optional[int] = None
    value: Optional[int] = None
