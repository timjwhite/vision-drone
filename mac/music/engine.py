import math
import time
from dataclasses import dataclass
from typing import List

from fusion.features import GlobalFeatures
from music.events import MidiEvent


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def scale_to_midi(value: float, in_min: float, in_max: float, out_min: int, out_max: int) -> int:
    if in_max <= in_min:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    t = clamp(t, 0.0, 1.0)
    return int(round(out_min + t * (out_max - out_min)))


@dataclass
class Voice:
    voice_id: int
    midi_note: int
    active: bool = False
    last_trigger: float = 0.0


class MusicEngine:
    def __init__(self, config: dict):
        self.scale_notes = config.get("scale_notes", [62, 64, 65, 67, 69, 71, 72, 74])
        self.voice_count = int(config.get("voice_count", 8))
        self.min_interval_s = float(config.get("min_interval_s", 1.5))
        self.velocity_min = int(config.get("velocity_min", 20))
        self.velocity_max = int(config.get("velocity_max", 90))
        self.cc_movement = int(config.get("cc_movement", 1))
        self.cc_density = int(config.get("cc_density", 11))
        self.cc_phone = int(config.get("cc_phone", 74))

        self._voices: List[Voice] = []
        for i in range(self.voice_count):
            note = self.scale_notes[i % len(self.scale_notes)]
            self._voices.append(Voice(voice_id=i, midi_note=note))

    def generate(self, features: GlobalFeatures, now: float | None = None) -> List[MidiEvent]:
        now = now or time.time()
        events: List[MidiEvent] = []

        target_active = clamp(features.total_people, 0, self.voice_count)
        target_active = int(target_active)

        velocity = scale_to_midi(features.movement_energy, 0.0, 10.0, self.velocity_min, self.velocity_max)
        velocity = int(velocity * (1.0 - clamp(features.phone_ratio, 0.0, 1.0)))
        velocity = clamp(velocity, 0, 127)

        for v in self._voices:
            if v.voice_id < target_active:
                if (now - v.last_trigger) >= self.min_interval_s:
                    if not v.active:
                        events.append(MidiEvent(type="note_on", note=v.midi_note, velocity=velocity))
                        v.active = True
                    else:
                        events.append(MidiEvent(type="note_on", note=v.midi_note, velocity=velocity))
                    v.last_trigger = now
            else:
                if v.active:
                    events.append(MidiEvent(type="note_off", note=v.midi_note, velocity=0))
                    v.active = False

        events.append(MidiEvent(type="cc", cc=self.cc_movement, value=scale_to_midi(features.movement_energy, 0, 10, 0, 127)))
        events.append(MidiEvent(type="cc", cc=self.cc_density, value=scale_to_midi(target_active, 0, self.voice_count, 0, 127)))
        events.append(MidiEvent(type="cc", cc=self.cc_phone, value=scale_to_midi(features.phone_ratio, 0, 1, 0, 127)))

        return events
