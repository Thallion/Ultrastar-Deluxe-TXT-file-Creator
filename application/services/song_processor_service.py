# application/services/song_processor_service.py
"""
Application Service: Song Processor
Verarbeitet und optimiert Songs
"""
import logging

from domain.entities.song import Song
from domain.entities.note import Note, NoteType


logger = logging.getLogger(__name__)


class SongProcessorService:
    """
    Service für Song-Nachbearbeitung und Optimierung
    """

    def optimize_note_timing(self, song: Song, snap_to_grid: int = 4) -> None:
        """
        Optimiert Note-Timing durch Grid-Snapping

        Args:
            song: Song-Objekt
            snap_to_grid: Grid-Weite in Beats (4 = snap auf jeden 4. Beat)
        """
        for note in song.notes:
            if note.type == NoteType.PAUSE:
                continue

            # Snap Start-Beat zum Grid
            note.beat = round(note.beat / snap_to_grid) * snap_to_grid

            # Stelle sicher dass Dauer mindestens 1 ist
            if note.duration < 1:
                note.duration = 1

    def remove_short_notes(self, song: Song, min_duration: int = 2) -> int:
        """
        Entfernt zu kurze Noten

        Args:
            song: Song-Objekt
            min_duration: Minimale Dauer in Beats

        Returns:
            Anzahl entfernter Noten
        """
        original_count = len(song.notes)
        song.notes = [n for n in song.notes
                      if n.type == NoteType.PAUSE or n.duration >= min_duration]
        return original_count - len(song.notes)

    def merge_adjacent_notes(self, song: Song, max_pitch_diff: int = 1) -> int:
        """
        Verschmilzt benachbarte Noten mit ähnlicher Tonhöhe

        Args:
            song: Song-Objekt
            max_pitch_diff: Maximale Pitch-Differenz

        Returns:
            Anzahl verschmolzener Noten
        """
        if not song.notes:
            return 0

        merged_count = 0
        new_notes = []
        current = song.notes[0]

        for next_note in song.notes[1:]:
            # Skip Pausen
            if current.type == NoteType.PAUSE or next_note.type == NoteType.PAUSE:
                new_notes.append(current)
                current = next_note
                continue

            # Prüfe ob verschmelzbar
            if (current.end_beat == next_note.beat and
                    abs(current.pitch - next_note.pitch) <= max_pitch_diff):
                # Verschmelze
                current.duration += next_note.duration
                if next_note.text and not current.text.endswith('~'):
                    current.text += next_note.text
                merged_count += 1
            else:
                new_notes.append(current)
                current = next_note

        new_notes.append(current)
        song.notes = new_notes

        return merged_count
