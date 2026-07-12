# domain/entities/song.py
"""
Domain Entity: Song
Repräsentiert einen kompletten Song mit Metadaten und Noten
"""
import bisect
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from domain.entities.note import Note, NoteType


@dataclass
class SongMetadata:
    """Metadaten eines Songs"""
    title: str
    artist: str
    bpm: float
    gap: float  # Gap in Millisekunden
    audio_file: str
    creator: str = "UltraStar Generator"
    language: str = "Unknown"
    year: Optional[int] = None
    genre: Optional[str] = None
    edition: Optional[str] = None
    cover: Optional[str] = None
    background: Optional[str] = None
    video: Optional[str] = None
    video_gap: Optional[float] = None
    start: Optional[float] = None
    end: Optional[float] = None
    preview_start: Optional[float] = None

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not self.title or not self.artist:
            raise ValueError("Title and artist are required")

        # UltraStar-BPM ist ein Quantisierungs-Vielfaches des realen Tempos;
        # offizielle Dateien enthalten Werte bis über 900
        if not (10 <= self.bpm <= 1200):
            raise ValueError("BPM must be between 10 and 1200")

        if self.gap < 0:
            raise ValueError("Gap cannot be negative")

        if self.year is None:
            self.year = datetime.now().year


@dataclass
class Song:
    """
    Repräsentiert einen kompletten UltraStar Song

    Attributes:
        metadata: Song-Metadaten
        notes: Liste von Noten (nach Beat sortiert)
    """
    metadata: SongMetadata
    notes: List[Note] = field(default_factory=list)

    def add_note(self, note: Note) -> None:
        """
        Fügt eine Note sortiert ein und prüft Überlappung mit den Nachbarn.

        Die Liste bleibt dadurch immer sortiert; eine vollständige
        Überlappungsprüfung gegen alle Noten übernimmt validate().
        """
        beats = [n.beat for n in self.notes]
        idx = bisect.bisect_right(beats, note.beat)

        if note.type != NoteType.PAUSE:
            for neighbor in self.notes[max(0, idx - 2):idx + 2]:
                if note.overlaps_with(neighbor):
                    raise ValueError(f"Note at beat {note.beat} overlaps with existing note")

        self.notes.insert(idx, note)

    def sort_notes(self) -> None:
        """Sortiert Noten nach Beat"""
        self.notes.sort(key=lambda n: n.beat)

    def get_duration_in_beats(self) -> int:
        """Berechnet die Gesamtdauer des Songs in Beats"""
        if not self.notes:
            return 0

        vocal_notes = [n for n in self.notes if n.type != NoteType.PAUSE]
        if not vocal_notes:
            return 0

        return max(n.end_beat for n in vocal_notes)

    def get_duration_in_ms(self) -> float:
        """Berechnet die Gesamtdauer des Songs in Millisekunden"""
        beats = self.get_duration_in_beats()
        ms_per_beat = 60000.0 / self.metadata.bpm
        return self.metadata.gap + (beats * ms_per_beat)

    def validate(self) -> List[str]:
        """
        Validiert den Song und gibt eine Liste von Problemen zurück

        Returns:
            Liste von Validierungsfehlern (leer wenn alles OK)
        """
        errors = []

        if not self.notes:
            errors.append("Song has no notes")

        # Überlappungsprüfung über sortierte Noten: eine Note überlappt,
        # wenn sie vor dem bisher größten End-Beat beginnt
        vocal_notes = sorted(
            (n for n in self.notes if n.type != NoteType.PAUSE),
            key=lambda n: n.beat
        )
        max_end = None
        for note in vocal_notes:
            if max_end is not None and note.beat < max_end:
                errors.append(f"Notes overlap at beat {note.beat}")
            max_end = note.end_beat if max_end is None else max(max_end, note.end_beat)

        # Prüfe auf zu große Lücken
        for i in range(len(vocal_notes) - 1):
            gap = vocal_notes[i + 1].beat - vocal_notes[i].end_beat
            if gap > 100:  # Mehr als 100 Beats Pause
                errors.append(f"Large gap of {gap} beats after beat {vocal_notes[i].beat}")

        return errors
