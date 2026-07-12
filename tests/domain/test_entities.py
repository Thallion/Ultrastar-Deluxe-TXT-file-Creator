# tests/domain/test_entities.py
"""
Unit Tests für Domain Entities
"""
import pytest
from domain.entities.note import Note, NoteType
from domain.entities.song import Song, SongMetadata


class TestNote:
    """Tests für Note Entity"""

    def test_create_valid_note(self):
        """Test: Erstelle gültige Note"""
        note = Note(
            type=NoteType.NORMAL,
            beat=10,
            duration=4,
            pitch=5,
            text="Test"
        )

        assert note.type == NoteType.NORMAL
        assert note.beat == 10
        assert note.duration == 4
        assert note.pitch == 5
        assert note.text == "Test"

    def test_official_pitch_range_accepted(self):
        """Test: Pitch-Werte aus offiziellen Songs (-10 bis 72) sind gültig"""
        Note(NoteType.NORMAL, 0, 4, -10)
        Note(NoteType.NORMAL, 0, 4, 72)

    def test_duration_one_is_valid(self):
        """Test: Noten mit Dauer 1 sind gültig (häufig in offiziellen Songs)"""
        note = Note(NoteType.NORMAL, 0, 1, 5, "kurz")
        assert note.duration == 1

    def test_negative_beat_raises_error(self):
        """Test: Negativer Beat wirft Fehler"""
        with pytest.raises(ValueError, match="Beat cannot be negative"):
            Note(NoteType.NORMAL, -1, 4, 5)

    def test_invalid_pitch_range(self):
        """Test: Ungültiger Pitch-Bereich"""
        with pytest.raises(ValueError, match="Pitch must be between"):
            Note(NoteType.NORMAL, 0, 4, 100)

    def test_note_to_ultrastar_format(self):
        """Test: Konvertierung zu UltraStar Format"""
        note = Note(NoteType.NORMAL, 10, 4, 5, "Test")
        assert note.to_ultrastar_format() == ": 10 4 5 Test"

        golden = Note(NoteType.GOLDEN, 20, 8, 10, "Golden")
        assert golden.to_ultrastar_format() == "* 20 8 10 Golden"

        pause = Note(NoteType.PAUSE, 30, 0, 0)
        assert pause.to_ultrastar_format() == "- 30"

    def test_note_format_preserves_trailing_space(self):
        """Test: Leerzeichen am Silbenende bleibt erhalten (Wortgrenze)"""
        note = Note(NoteType.NORMAL, 0, 2, 9, "Well ")
        assert note.to_ultrastar_format() == ": 0 2 9 Well "

    def test_note_overlap_detection(self):
        """Test: Überlappungserkennung"""
        note1 = Note(NoteType.NORMAL, 10, 4, 5)
        note2 = Note(NoteType.NORMAL, 12, 4, 5)  # Überlappt
        note3 = Note(NoteType.NORMAL, 14, 4, 5)  # Überlappt nicht

        assert note1.overlaps_with(note2) == True
        assert note1.overlaps_with(note3) == False


class TestSong:
    """Tests für Song Entity"""

    @pytest.fixture
    def sample_metadata(self):
        """Fixture: Sample Metadata"""
        return SongMetadata(
            title="Test Song",
            artist="Test Artist",
            bpm=240.0,
            gap=1000.0,
            audio_file="test.mp3"
        )

    def test_create_song(self, sample_metadata):
        """Test: Song erstellen"""
        song = Song(sample_metadata)

        assert song.metadata.title == "Test Song"
        assert song.metadata.artist == "Test Artist"
        assert len(song.notes) == 0

    def test_add_notes_to_song(self, sample_metadata):
        """Test: Noten zu Song hinzufügen"""
        song = Song(sample_metadata)

        note1 = Note(NoteType.NORMAL, 0, 4, 5, "First")
        note2 = Note(NoteType.NORMAL, 8, 4, 7, "Second")

        song.add_note(note1)
        song.add_note(note2)

        assert len(song.notes) == 2
        assert song.notes[0].text == "First"
        assert song.notes[1].text == "Second"

    def test_add_note_keeps_notes_sorted(self, sample_metadata):
        """Test: Noten bleiben nach Beat sortiert, auch bei ungeordnetem Einfügen"""
        song = Song(sample_metadata)

        song.add_note(Note(NoteType.NORMAL, 20, 4, 5))
        song.add_note(Note(NoteType.NORMAL, 0, 4, 5))
        song.add_note(Note(NoteType.NORMAL, 10, 4, 5))

        assert [n.beat for n in song.notes] == [0, 10, 20]

    def test_overlapping_notes_rejected(self, sample_metadata):
        """Test: Überlappende Noten werden abgelehnt"""
        song = Song(sample_metadata)

        note1 = Note(NoteType.NORMAL, 0, 4, 5)
        note2 = Note(NoteType.NORMAL, 2, 4, 5)  # Überlappt mit note1

        song.add_note(note1)

        with pytest.raises(ValueError, match="overlaps with existing note"):
            song.add_note(note2)

    def test_validate_detects_overlaps(self, sample_metadata):
        """Test: validate() findet Überlappungen in unsortierten Noten"""
        song = Song(sample_metadata)
        song.notes = [
            Note(NoteType.NORMAL, 0, 10, 5),
            Note(NoteType.NORMAL, 4, 2, 5),  # liegt innerhalb der ersten Note
        ]

        errors = song.validate()
        assert any("overlap" in e for e in errors)

    def test_song_duration_calculation(self, sample_metadata):
        """Test: Song-Dauer Berechnung"""
        song = Song(sample_metadata)

        song.add_note(Note(NoteType.NORMAL, 0, 4, 5))
        song.add_note(Note(NoteType.NORMAL, 10, 8, 5))
        song.add_note(Note(NoteType.PAUSE, 20, 0, 0))

        assert song.get_duration_in_beats() == 18  # 10 + 8

        # ms = gap + (beats * ms_per_beat)
        # ms_per_beat = 60000 / 240 = 250
        expected_ms = 1000 + (18 * 250)
        assert song.get_duration_in_ms() == expected_ms
