# domain/entities/note.py
"""
Domain Entity: Note
Repräsentiert eine einzelne Note im UltraStar Format
"""
from dataclasses import dataclass
from enum import Enum

from domain.value_objects.pitch import ULTRASTAR_PITCH_MIN, ULTRASTAR_PITCH_MAX


class NoteType(Enum):
    """Enum für verschiedene Note-Typen in UltraStar"""
    NORMAL = ':'
    GOLDEN = '*'
    FREESTYLE = 'F'
    RAP = 'R'
    GOLDEN_RAP = 'G'
    PAUSE = '-'


@dataclass
class Note:
    """
    Repräsentiert eine Note im UltraStar Format

    Attributes:
        type: Der Typ der Note (Normal, Golden, etc.)
        beat: Start-Beat der Note
        duration: Dauer in Beats
        pitch: Tonhöhe (relativ zu C4)
        text: Lyrics-Text für diese Note (Leerzeichen sind bedeutungstragend:
              eine Silbe am Wortende trägt ein angehängtes Leerzeichen)
    """
    type: NoteType
    beat: int
    duration: int
    pitch: int
    text: str = ""

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if self.beat < 0:
            raise ValueError("Beat cannot be negative")

        if self.type != NoteType.PAUSE and self.duration < 1:
            raise ValueError("Note duration must be at least 1 beat")

        if self.type != NoteType.PAUSE and not (ULTRASTAR_PITCH_MIN <= self.pitch <= ULTRASTAR_PITCH_MAX):
            raise ValueError(
                f"Pitch must be between {ULTRASTAR_PITCH_MIN} and {ULTRASTAR_PITCH_MAX}"
            )

    def to_ultrastar_format(self) -> str:
        """Konvertiert Note zu UltraStar Format String"""
        if self.type == NoteType.PAUSE:
            return f"- {self.beat}"

        return f"{self.type.value} {self.beat} {self.duration} {self.pitch} {self.text}"

    @property
    def end_beat(self) -> int:
        """Berechnet den End-Beat der Note"""
        return self.beat + self.duration

    def overlaps_with(self, other: 'Note') -> bool:
        """Prüft ob diese Note mit einer anderen überlappt"""
        if self.type == NoteType.PAUSE or other.type == NoteType.PAUSE:
            return False

        return not (self.end_beat <= other.beat or other.end_beat <= self.beat)
