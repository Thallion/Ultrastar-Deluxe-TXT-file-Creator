# infrastructure/persistence/ultrastar_file_repository.py
"""
Konkrete Implementierung: UltraStar File Repository

Format-Konventionen orientieren sich an offiziellen UltraStar-Dateien:
- Header-Reihenfolge: ARTIST, TITLE, MP3, COVER, BACKGROUND, VIDEO, ...
- BPM/GAP ohne unnötige Nachkommastellen (240 statt 240.00)
- Keine Leerzeile zwischen Header und Noten
- CRLF-Zeilenenden, UTF-8
- Leerzeichen in Silben-Texten bleiben erhalten (Wortgrenzen!)
- Abschluss mit 'E'
"""
import logging
import re
from pathlib import Path
from typing import List, Optional

from application.interfaces.file_repository_interface import FileRepositoryInterface
from domain.entities.song import Song, SongMetadata
from domain.entities.note import Note, NoteType


logger = logging.getLogger(__name__)

# Notenzeile: Typ, Beat, Dauer, Pitch, danach genau ein Trennzeichen —
# der Rest ist Silben-Text inklusive führender/anhängender Leerzeichen
_NOTE_LINE_RE = re.compile(r'^([:*FRG])\s+(-?\d+)\s+(\d+)\s+(-?\d+)(?: (.*))?$')


class UltraStarFileRepository(FileRepositoryInterface):
    """
    Implementiert FileRepositoryInterface für UltraStar .txt Format
    """

    def save_song(self, song: Song, file_path: str) -> None:
        """Speichert Song im UltraStar Format"""
        try:
            # Stelle sicher dass Verzeichnis existiert
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # newline='\r\n': offizielle Dateien verwenden CRLF
            with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
                self._write_header(f, song.metadata)
                self._write_notes(f, song.notes)
                f.write("E\n")

            logger.info(f"Song gespeichert: {output_path}")

        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            raise

    def load_song(self, file_path: str) -> Song:
        """Lädt Song aus UltraStar Format"""
        try:
            notes = []
            metadata_dict = {}

            for raw_line in self._read_lines(file_path):
                line = raw_line.rstrip('\r\n')
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith('#'):
                    # Metadata
                    if ':' in stripped:
                        key, value = stripped[1:].split(':', 1)
                        metadata_dict[key.strip().upper()] = value.strip()

                elif stripped == 'E':
                    break

                elif line[:1] in (':', '*', 'F', 'R', 'G', '-'):
                    # Note: bewusst 'line' statt 'stripped', um
                    # Leerzeichen am Silbenende zu erhalten
                    note = self._parse_note_line(line)
                    if note:
                        notes.append(note)

            metadata = self._build_metadata(metadata_dict)
            song = Song(metadata, notes)

            logger.info(f"Song geladen: {file_path}")
            return song

        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}")
            raise

    def exists(self, file_path: str) -> bool:
        """Prüft ob Datei existiert"""
        return Path(file_path).exists()

    def _read_lines(self, file_path: str) -> List[str]:
        """Liest Datei als UTF-8 (mit BOM-Unterstützung), Fallback CP1252"""
        for encoding in ('utf-8-sig', 'cp1252'):
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    return f.readlines()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Datei-Encoding nicht unterstützt: {file_path}")

    def _build_metadata(self, tags: dict) -> SongMetadata:
        """Erstellt SongMetadata aus geparsten Header-Tags"""
        def parse_float(value: Optional[str]) -> Optional[float]:
            if not value:
                return None
            # Offizielle Dateien verwenden teils Komma als Dezimaltrennzeichen
            return float(value.replace(',', '.'))

        def parse_year(value: Optional[str]) -> Optional[int]:
            try:
                return int(value) if value else None
            except ValueError:
                return None

        return SongMetadata(
            title=tags.get('TITLE', 'Unknown'),
            artist=tags.get('ARTIST', 'Unknown'),
            bpm=parse_float(tags.get('BPM')) or 120.0,
            gap=parse_float(tags.get('GAP')) or 0.0,
            audio_file=tags.get('MP3', tags.get('AUDIO', '')),
            creator=tags.get('CREATOR', 'Unknown'),
            language=tags.get('LANGUAGE', 'Unknown'),
            year=parse_year(tags.get('YEAR')),
            genre=tags.get('GENRE'),
            edition=tags.get('EDITION'),
            cover=tags.get('COVER'),
            background=tags.get('BACKGROUND'),
            video=tags.get('VIDEO'),
            video_gap=parse_float(tags.get('VIDEOGAP')),
            start=parse_float(tags.get('START')),
            end=parse_float(tags.get('END')),
            preview_start=parse_float(tags.get('PREVIEWSTART')),
        )

    @staticmethod
    def _format_number(value: float) -> str:
        """Formatiert Zahlen wie offizielle Dateien: 240 statt 240.00, 238.88 bleibt"""
        rounded = round(float(value), 2)
        if rounded == int(rounded):
            return str(int(rounded))
        return f"{rounded:g}"

    def _write_header(self, f, metadata: SongMetadata):
        """Schreibt UltraStar Header in offizieller Tag-Reihenfolge"""
        f.write(f"#ARTIST:{metadata.artist}\n")
        f.write(f"#TITLE:{metadata.title}\n")
        f.write(f"#MP3:{metadata.audio_file}\n")

        if metadata.cover:
            f.write(f"#COVER:{metadata.cover}\n")
        if metadata.background:
            f.write(f"#BACKGROUND:{metadata.background}\n")
        if metadata.video:
            f.write(f"#VIDEO:{metadata.video}\n")
        if metadata.video_gap is not None:
            f.write(f"#VIDEOGAP:{self._format_number(metadata.video_gap)}\n")

        f.write(f"#CREATOR:{metadata.creator}\n")
        if metadata.edition:
            f.write(f"#EDITION:{metadata.edition}\n")
        if metadata.genre:
            f.write(f"#GENRE:{metadata.genre}\n")
        if metadata.year:
            f.write(f"#YEAR:{metadata.year}\n")
        f.write(f"#LANGUAGE:{metadata.language}\n")

        f.write(f"#BPM:{self._format_number(metadata.bpm)}\n")
        f.write(f"#GAP:{self._format_number(metadata.gap)}\n")

        if metadata.start is not None:
            f.write(f"#START:{self._format_number(metadata.start)}\n")
        if metadata.end is not None:
            f.write(f"#END:{self._format_number(metadata.end)}\n")
        if metadata.preview_start is not None:
            f.write(f"#PREVIEWSTART:{self._format_number(metadata.preview_start)}\n")

    def _write_notes(self, f, notes: List[Note]):
        """Schreibt Noten im UltraStar Format"""
        for note in notes:
            f.write(note.to_ultrastar_format() + "\n")

    def _parse_note_line(self, line: str) -> Optional[Note]:
        """Parst eine Note-Zeile, Silben-Leerzeichen bleiben erhalten"""
        try:
            if line.startswith('-'):
                # Zeilenumbruch: '- <beat>' oder '- <beat> <beat>' (relative Dateien)
                parts = line.split()
                beat = int(parts[1]) if len(parts) > 1 else 0
                return Note(NoteType.PAUSE, beat, 0, 0)

            match = _NOTE_LINE_RE.match(line)
            if not match:
                logger.warning(f"Unbekanntes Zeilenformat: {line!r}")
                return None

            note_type_map = {
                ':': NoteType.NORMAL,
                '*': NoteType.GOLDEN,
                'F': NoteType.FREESTYLE,
                'R': NoteType.RAP,
                'G': NoteType.GOLDEN_RAP,
            }

            return Note(
                type=note_type_map[match.group(1)],
                beat=int(match.group(2)),
                duration=int(match.group(3)),
                pitch=int(match.group(4)),
                text=match.group(5) or '',
            )

        except Exception as e:
            logger.warning(f"Fehler beim Parsen der Note-Zeile: {line!r} - {e}")
            return None
