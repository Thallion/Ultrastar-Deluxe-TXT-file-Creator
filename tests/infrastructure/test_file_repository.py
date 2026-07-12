# tests/infrastructure/test_file_repository.py
"""
Unit Tests für File Repository
"""
import pytest
from infrastructure.persistence.ultrastar_file_repository import UltraStarFileRepository
from domain.entities.song import Song, SongMetadata
from domain.entities.note import Note, NoteType


class TestUltraStarFileRepository:
    """Tests für UltraStar File Repository"""

    @pytest.fixture
    def repository(self):
        """Fixture: Repository Instanz"""
        return UltraStarFileRepository()

    @pytest.fixture
    def sample_song(self):
        """Fixture: Sample Song"""
        metadata = SongMetadata(
            title="Test Song",
            artist="Test Artist",
            bpm=240.0,
            gap=1000.0,
            audio_file="test.mp3",
            year=2024
        )

        song = Song(metadata)
        song.notes = [
            Note(NoteType.NORMAL, 0, 4, 5, "First "),
            Note(NoteType.GOLDEN, 8, 8, 10, "Gol"),
            Note(NoteType.NORMAL, 16, 2, 10, "den "),
            Note(NoteType.PAUSE, 20, 0, 0),
            Note(NoteType.NORMAL, 24, 4, 7, "Last ")
        ]

        return song

    def test_save_and_load_song(self, repository, sample_song, tmp_path):
        """Test: Song speichern und laden (Roundtrip)"""
        # Speichern
        file_path = tmp_path / "test_song.txt"
        repository.save_song(sample_song, str(file_path))

        assert file_path.exists()

        # Laden
        loaded_song = repository.load_song(str(file_path))

        # Vergleiche Metadata
        assert loaded_song.metadata.title == sample_song.metadata.title
        assert loaded_song.metadata.artist == sample_song.metadata.artist
        assert loaded_song.metadata.bpm == sample_song.metadata.bpm
        assert loaded_song.metadata.gap == sample_song.metadata.gap

        # Vergleiche Noten
        assert len(loaded_song.notes) == len(sample_song.notes)

        for original, loaded in zip(sample_song.notes, loaded_song.notes):
            assert original.type == loaded.type
            assert original.beat == loaded.beat
            assert original.duration == loaded.duration
            assert original.pitch == loaded.pitch
            assert original.text == loaded.text

    def test_file_format(self, repository, sample_song, tmp_path):
        """Test: Dateiformat entspricht offiziellen Konventionen"""
        file_path = tmp_path / "test_format.txt"
        repository.save_song(sample_song, str(file_path))

        # Rohbytes lesen, sonst übersetzt Python CRLF zu LF
        content = file_path.read_bytes().decode('utf-8')
        lines = content.splitlines()

        # Header prüfen: offizielle Reihenfolge, keine Leerzeile vor den Noten
        assert lines[0] == "#ARTIST:Test Artist"
        assert lines[1] == "#TITLE:Test Song"
        assert lines[2] == "#MP3:test.mp3"
        assert "#BPM:240" in lines      # nicht 240.00
        assert "#GAP:1000" in lines
        assert "" not in lines[:lines.index("E")]

        # CRLF wie offizielle Dateien
        assert "\r\n" in content

        # Noten prüfen (inkl. erhaltener Leerzeichen am Silbenende)
        assert ": 0 4 5 First " in content
        assert "* 8 8 10 Gol\r\n" in content
        assert "- 20\r\n" in content

        # Ende prüfen
        assert lines[-1] == "E"

    def test_bpm_with_decimals_preserved(self, repository, tmp_path):
        """Test: BPM mit Nachkommastellen bleibt erhalten (z.B. 238.88)"""
        metadata = SongMetadata(
            title="T", artist="A", bpm=238.88, gap=0.0, audio_file="a.mp3"
        )
        song = Song(metadata, [Note(NoteType.NORMAL, 0, 1, 0, "x")])

        file_path = tmp_path / "bpm.txt"
        repository.save_song(song, str(file_path))

        content = file_path.read_text(encoding='utf-8')
        assert "#BPM:238.88" in content

    def test_load_comma_decimal_and_linebreak_variants(self, repository, tmp_path):
        """Test: Komma-Dezimalwerte und '- a b' Zeilenumbrüche werden geparst"""
        file_path = tmp_path / "official_style.txt"
        file_path.write_bytes(
            b"#ARTIST:A\r\n#TITLE:T\r\n#MP3:a.mp3\r\n"
            b"#BPM:227,88\r\n#GAP:9247,00\r\n"
            b": 0 2 9 Well \r\n- 5 7\r\n: 8 2 -5 low\r\nE\r\n"
        )

        song = repository.load_song(str(file_path))

        assert song.metadata.bpm == 227.88
        assert song.metadata.gap == 9247.0
        assert len(song.notes) == 3
        assert song.notes[0].text == "Well "   # Leerzeichen erhalten
        assert song.notes[1].type == NoteType.PAUSE
        assert song.notes[1].beat == 5
        assert song.notes[2].pitch == -5
