# domain/value_objects/beat.py
"""
Value Object: Beat
Repräsentiert Beat/Timing Informationen
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Beat:
    """
    Immutable Value Object für Beat-Informationen

    Attributes:
        beat_number: Beat-Nummer (UltraStar Beat)
        time_ms: Zeit in Millisekunden
        bpm: Beats per Minute
        gap_ms: Gap in Millisekunden
    """
    beat_number: int
    time_ms: float
    bpm: float
    gap_ms: float

    @classmethod
    def from_time(cls, time_ms: float, bpm: float, gap_ms: float) -> 'Beat':
        """Erstellt Beat aus Zeit"""
        ms_per_beat = 60000.0 / bpm
        relative_time_ms = time_ms - gap_ms

        if relative_time_ms < 0:
            beat_number = 0
        else:
            beat_number = int(round(relative_time_ms / ms_per_beat))

        return cls(beat_number, time_ms, bpm, gap_ms)

    @classmethod
    def from_beat_number(cls, beat_number: int, bpm: float, gap_ms: float) -> 'Beat':
        """Erstellt Beat aus Beat-Nummer"""
        ms_per_beat = 60000.0 / bpm
        time_ms = gap_ms + (beat_number * ms_per_beat)

        return cls(beat_number, time_ms, bpm, gap_ms)

    def to_next_beat(self) -> 'Beat':
        """Gibt den nächsten Beat zurück"""
        return Beat.from_beat_number(self.beat_number + 1, self.bpm, self.gap_ms)
