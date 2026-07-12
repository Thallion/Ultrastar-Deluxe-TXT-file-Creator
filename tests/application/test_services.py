# tests/application/test_services.py
"""
Unit Tests für Application Services
"""
import pytest
from application.services.song_processor_service import SongProcessorService
from domain.entities.song import Song, SongMetadata
from domain.entities.note import Note, NoteType


class TestSongProcessorService:
    """Tests für Song Processor Service"""

    @pytest.fixture
    def sample_song(self):
        """Fixture: Sample Song"""
        metadata = SongMetadata(
            title="Test",
            artist="Test",
            bpm=240.0,
            gap=0.0,
            audio_file="test.mp3"
        )
        song = Song(metadata)

        # Füge Test-Noten hinzu
        song.notes = [
            Note(NoteType.NORMAL, 0, 1, 5, "Too"),    # Zu kurz
            Note(NoteType.NORMAL, 4, 4, 5, "Short"),
            Note(NoteType.NORMAL, 8, 4, 6, "Note"),   # Benachbart, ähnlicher Pitch
            Note(NoteType.PAUSE, 12, 0, 0),
            Note(NoteType.NORMAL, 16, 8, 10, "Long")
        ]

        return song

    def test_remove_short_notes(self, sample_song):
        """Test: Entferne kurze Noten"""
        service = SongProcessorService()

        removed = service.remove_short_notes(sample_song, min_duration=2)

        assert removed == 1  # Eine Note entfernt
        assert len(sample_song.notes) == 4
        assert all(n.duration >= 2 or n.type == NoteType.PAUSE
                   for n in sample_song.notes)

    def test_merge_adjacent_notes(self, sample_song):
        """Test: Verschmelze benachbarte Noten"""
        service = SongProcessorService()

        # Entferne erst die zu kurze Note
        service.remove_short_notes(sample_song, min_duration=2)

        merged = service.merge_adjacent_notes(sample_song, max_pitch_diff=1)

        assert merged == 1  # Ein Paar verschmolzen
        assert len(sample_song.notes) == 3  # 4 - 1 verschmolzen

        # Prüfe verschmolzene Note
        merged_note = sample_song.notes[0]
        assert merged_note.duration == 8  # 4 + 4
        assert merged_note.text == "ShortNote"

    def test_optimize_timing(self, sample_song):
        """Test: Timing-Optimierung"""
        service = SongProcessorService()

        # Setze ungerade Beat-Werte
        sample_song.notes[1].beat = 5  # Wird zu 4
        sample_song.notes[2].beat = 9  # Wird zu 8

        service.optimize_note_timing(sample_song, snap_to_grid=4)

        assert sample_song.notes[1].beat == 4
        assert sample_song.notes[2].beat == 8
