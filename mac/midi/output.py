from __future__ import annotations

from typing import Iterable, Optional

import mido

from music.events import MidiEvent


class MidiOutput:
    def __init__(self, config: dict):
        self.port_name = config.get("port_name", "IAC Driver Bus 1")
        self._port: Optional[mido.ports.BaseOutput] = None

    def open(self) -> None:
        if self._port is None:
            self._port = mido.open_output(self.port_name)

    def close(self) -> None:
        if self._port is not None:
            try:
                self.all_notes_off()
            finally:
                self._port.close()
                self._port = None

    def send(self, events: Iterable[MidiEvent]) -> None:
        if self._port is None:
            self.open()
        assert self._port is not None
        for ev in events:
            if ev.type == "note_on" and ev.note is not None:
                self._port.send(mido.Message("note_on", note=ev.note, velocity=int(ev.velocity or 0)))
            elif ev.type == "note_off" and ev.note is not None:
                self._port.send(mido.Message("note_off", note=ev.note, velocity=int(ev.velocity or 0)))
            elif ev.type == "cc" and ev.cc is not None:
                self._port.send(mido.Message("control_change", control=int(ev.cc), value=int(ev.value or 0)))

    def all_notes_off(self) -> None:
        if self._port is None:
            return
        for note in range(0, 128):
            self._port.send(mido.Message("note_off", note=note, velocity=0))
