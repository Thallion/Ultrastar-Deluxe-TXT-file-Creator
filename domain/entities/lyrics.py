# domain/entities/lyrics.py
"""
Domain Entity: Lyrics
Repräsentiert Lyrics mit Silben und Timing-Informationen
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Syllable:
    """Repräsentiert eine Silbe mit optionalem Timing"""
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def __str__(self) -> str:
        return self.text

    @property
    def duration(self) -> Optional[float]:
        """Berechnet die Dauer der Silbe"""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None


@dataclass
class LyricLine:
    """Repräsentiert eine Zeile von Lyrics"""
    syllables: List[Syllable]
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def get_text(self) -> str:
        """Gibt den kompletten Text der Zeile zurück"""
        return ' '.join(syl.text for syl in self.syllables)

    def get_syllable_count(self) -> int:
        """Gibt die Anzahl der Silben zurück"""
        return len(self.syllables)


@dataclass
class Lyrics:
    """
    Repräsentiert die kompletten Lyrics eines Songs

    Attributes:
        lines: Liste von Lyric-Zeilen
        language: Sprache der Lyrics
    """
    lines: List[LyricLine]
    language: str = "Unknown"

    def get_all_syllables(self) -> List[Syllable]:
        """Gibt alle Silben als flache Liste zurück"""
        syllables = []
        for line in self.lines:
            syllables.extend(line.syllables)
        return syllables

    def get_total_syllable_count(self) -> int:
        """Gibt die Gesamtanzahl der Silben zurück"""
        return sum(line.get_syllable_count() for line in self.lines)

    def get_full_text(self) -> str:
        """Gibt den kompletten Text zurück"""
        return '\n'.join(line.get_text() for line in self.lines)
