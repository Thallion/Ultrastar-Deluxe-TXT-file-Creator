# application/services/ultrastar_generator_service.py
"""
Application Service: UltraStar Generator
Koordiniert den Generierungsprozess
"""
from typing import Optional, List
import logging
from pathlib import Path

from domain.entities.song import Song, SongMetadata
from domain.entities.note import Note, NoteType
from domain.entities.lyrics import Lyrics
from domain.services.pitch_detection_service import PitchDetectionService
from domain.services.beat_detection_service import BeatDetectionService, TempoEstimate

from application.interfaces.audio_processor_interface import AudioProcessorInterface
from application.interfaces.vocal_separator_interface import VocalSeparatorInterface
from application.interfaces.file_repository_interface import FileRepositoryInterface


logger = logging.getLogger(__name__)


class GenerationResult:
    """Ergebnis der Song-Generierung"""
    def __init__(self, success: bool, song: Optional[Song] = None,
                 output_path: Optional[str] = None, errors: Optional[List[str]] = None):
        self.success = success
        self.song = song
        self.output_path = output_path
        self.errors = errors or []


class UltraStarGeneratorService:
    """
    Application Service für UltraStar Generierung
    Koordiniert die verschiedenen Domain Services und Infrastructure Services
    """

    def __init__(self,
                 audio_processor: AudioProcessorInterface,
                 vocal_separator: Optional[VocalSeparatorInterface],
                 file_repository: FileRepositoryInterface,
                 pitch_detection_service: PitchDetectionService,
                 beat_detection_service: BeatDetectionService):
        self.audio_processor = audio_processor
        self.vocal_separator = vocal_separator
        self.file_repository = file_repository
        self.pitch_detection_service = pitch_detection_service
        self.beat_detection_service = beat_detection_service

    def generate_from_audio(self,
                            audio_path: str,
                            title: Optional[str] = None,
                            artist: Optional[str] = None,
                            lyrics: Optional[Lyrics] = None,
                            output_path: Optional[str] = None) -> GenerationResult:
        """
        Hauptmethode: Generiert einen UltraStar Song aus Audio

        Args:
            audio_path: Pfad zur Audio-Datei
            title: Song-Titel (optional)
            artist: Künstler (optional)
            lyrics: Lyrics-Objekt (optional)
            output_path: Output-Pfad (optional)

        Returns:
            GenerationResult mit Erfolg/Fehler-Informationen
        """
        try:
            # 1. Metadaten vorbereiten
            audio_file = Path(audio_path)
            if not title:
                title = self._extract_title_from_filename(audio_file.name)
            if not artist:
                artist = self._extract_artist_from_filename(audio_file.name)

            logger.info(f"Generiere UltraStar für: {artist} - {title}")

            # 2. Vocals separieren (wenn Separator verfügbar)
            processed_audio_path = audio_path
            if self.vocal_separator and self.vocal_separator.is_available():
                logger.info(f"Separiere Vocals mit {self.vocal_separator.get_name()}")
                processed_audio_path = self.vocal_separator.separate(audio_path)

            # 3. Audio laden und analysieren
            logger.info("Lade und analysiere Audio...")
            audio_data, sample_rate = self.audio_processor.load_audio(processed_audio_path)

            # 4. Tempo und Onsets erkennen
            logger.info("Erkenne Tempo und Rhythmus...")
            onset_times = self.audio_processor.detect_onsets(audio_data, sample_rate)
            tempo_estimate = self._estimate_tempo(audio_data, sample_rate, onset_times)

            # 5. GAP berechnen
            gap_ms = self.beat_detection_service.calculate_gap(
                onset_times[0] if onset_times.size > 0 else 0
            )

            # 6. Pitch erkennen
            logger.info("Erkenne Tonhöhen...")
            frequencies, confidences, times = self.audio_processor.extract_pitch(audio_data, sample_rate)
            pitch_segments = self.pitch_detection_service.process_pitch_data(frequencies, confidences, times)

            if not pitch_segments:
                return GenerationResult(False, errors=["Keine Tonhöhen erkannt"])

            # 7. Pitch-Segmente verschmelzen
            pitch_segments = self.pitch_detection_service.merge_similar_segments(pitch_segments)

            # 8. Song-Objekt erstellen
            metadata = SongMetadata(
                title=title,
                artist=artist,
                bpm=tempo_estimate.ultrastar_bpm,
                gap=gap_ms,
                audio_file=audio_file.name
            )
            song = Song(metadata)

            # 9. Noten aus Pitch-Segmenten erstellen
            self._create_notes_from_pitch_segments(song, pitch_segments, lyrics)

            # 10. Song validieren
            validation_errors = song.validate()
            if validation_errors:
                logger.warning(f"Validierungswarnungen: {validation_errors}")

            # 11. Song speichern
            if not output_path:
                output_path = f"output/{artist} - {title}.txt"

            self.file_repository.save_song(song, output_path)
            logger.info(f"Song gespeichert: {output_path}")

            return GenerationResult(True, song, output_path)

        except Exception as e:
            logger.error(f"Fehler bei der Generierung: {e}")
            return GenerationResult(False, errors=[str(e)])

    def _estimate_tempo(self, audio_data, sample_rate, onset_times) -> TempoEstimate:
        """
        Schätzt das Tempo. Primär über den Beat-Tracker des Audio-Processors
        (robust), das Onset-Histogramm dient nur als Fallback.
        """
        try:
            bpm = self.audio_processor.estimate_tempo(audio_data, sample_rate)
            if bpm and bpm > 0:
                return TempoEstimate(bpm, 1.0)
        except Exception as e:
            logger.warning(f"Beat-Tracking fehlgeschlagen, verwende Onset-Histogramm: {e}")

        return self.beat_detection_service.estimate_tempo(onset_times)

    def _create_notes_from_pitch_segments(self, song: Song, pitch_segments, lyrics: Optional[Lyrics]):
        """Erstellt Noten aus Pitch-Segmenten und fügt sie zum Song hinzu"""
        syllables = lyrics.get_all_syllables() if lyrics else []
        syllable_index = 0
        last_end_beat = 0

        for i, segment in enumerate(pitch_segments):
            # Konvertiere Zeit zu Beat
            start_beat = self.beat_detection_service.quantize_to_beat_grid(
                segment.start_time * 1000,
                song.metadata.bpm,
                song.metadata.gap
            )

            duration_beats = self.beat_detection_service.calculate_note_duration_beats(
                segment.duration * 1000,
                song.metadata.bpm
            )

            # Quantisierung kann Überlappungen erzeugen: Startbeat hinter
            # das Ende der vorherigen Note schieben statt abzubrechen
            beat_number = max(start_beat.beat_number, last_end_beat)

            # Füge Zeilenumbruch ein wenn nötig
            if beat_number - last_end_beat > 8 and last_end_beat > 0:
                song.add_note(Note(NoteType.PAUSE, last_end_beat + 2, 0, 0))

            # Bestimme Note-Typ
            note_type = NoteType.NORMAL
            if segment.confidence > 0.8 and duration_beats > 6:
                note_type = NoteType.GOLDEN

            # Erstelle Note
            text = ""
            if syllable_index < len(syllables):
                text = str(syllables[syllable_index])
                syllable_index += 1
            elif i > 0:  # Verwende ~ für gehaltene Töne
                text = "~"

            note = Note(
                type=note_type,
                beat=beat_number,
                duration=duration_beats,
                pitch=segment.pitch.ultrastar_pitch,
                text=text
            )

            song.add_note(note)
            last_end_beat = note.end_beat

    def _extract_title_from_filename(self, filename: str) -> str:
        """Extrahiert Titel aus Dateiname"""
        name = Path(filename).stem
        if ' - ' in name:
            return name.split(' - ', 1)[1]
        return name

    def _extract_artist_from_filename(self, filename: str) -> str:
        """Extrahiert Artist aus Dateiname"""
        name = Path(filename).stem
        if ' - ' in name:
            return name.split(' - ', 1)[0]
        return "Unknown Artist"
