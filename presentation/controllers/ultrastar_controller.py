# presentation/controllers/ultrastar_controller.py
"""
MVC Controller: UltraStar Controller
Vermittelt zwischen Model und View
"""
import threading
import logging
from typing import Optional
from pathlib import Path

from presentation.models.ultrastar_model import UltraStarModel, ProcessingStatus
from application.services.ultrastar_generator_service import UltraStarGeneratorService
from domain.entities.lyrics import Lyrics, LyricLine, Syllable


logger = logging.getLogger(__name__)


class UltraStarController:
    """
    Controller für die UltraStar Anwendung
    Koordiniert Model-Updates basierend auf User-Input
    """

    def __init__(self, model: UltraStarModel, generator_service: UltraStarGeneratorService):
        self.model = model
        self.generator_service = generator_service
        self._processing_thread: Optional[threading.Thread] = None

    def set_audio_file(self, file_path: str) -> bool:
        """
        Setzt die Audio-Datei

        Returns:
            True wenn erfolgreich
        """
        if not Path(file_path).exists():
            self.model.add_log_message(f"❌ Audio-Datei nicht gefunden: {file_path}")
            return False

        self.model.set_audio_path(file_path)
        self.model.add_log_message(f"✅ Audio-Datei geladen: {Path(file_path).name}")
        return True

    def set_lyrics_file(self, file_path: str) -> bool:
        """
        Setzt die Lyrics-Datei

        Returns:
            True wenn erfolgreich
        """
        if not Path(file_path).exists():
            self.model.add_log_message(f"❌ Lyrics-Datei nicht gefunden: {file_path}")
            return False

        try:
            # Lade und parse Lyrics
            lyrics = self._load_lyrics(file_path)
            self.model.lyrics = lyrics
            self.model.set_lyrics_path(file_path)
            self.model.add_log_message(f"✅ Lyrics geladen: {lyrics.get_total_syllable_count()} Silben")
            return True
        except Exception as e:
            self.model.add_log_message(f"❌ Fehler beim Laden der Lyrics: {e}")
            return False

    def start_generation(self, title: Optional[str] = None, artist: Optional[str] = None):
        """Startet die Song-Generierung in einem separaten Thread"""
        if self._processing_thread and self._processing_thread.is_alive():
            self.model.add_log_message("⚠️ Verarbeitung läuft bereits")
            return

        if not self.model.audio_path:
            self.model.add_log_message("❌ Keine Audio-Datei ausgewählt")
            return

        # Starte in separatem Thread
        self._processing_thread = threading.Thread(
            target=self._generate_song,
            args=(title, artist)
        )
        self._processing_thread.daemon = True
        self._processing_thread.start()

    def _generate_song(self, title: Optional[str], artist: Optional[str]):
        """Generiert den Song (läuft in separatem Thread)"""
        try:
            # Update Progress Callbacks
            def update_progress(status: ProcessingStatus, progress: float, message: str):
                self.model.update_progress(status, progress, message)

            # Start
            update_progress(ProcessingStatus.LOADING, 0.1, "Lade Audio...")

            # Führe Generierung aus
            result = self.generator_service.generate_from_audio(
                audio_path=self.model.audio_path,
                title=title,
                artist=artist,
                lyrics=self.model.lyrics,
                output_path=None
            )

            if result.success:
                # Erfolg
                self.model.set_current_song(result.song)
                self.model.add_recent_file(result.output_path)
                update_progress(ProcessingStatus.COMPLETED, 1.0, "Erfolgreich abgeschlossen!")
                self.model.add_log_message(f"✅ Song generiert: {result.output_path}")
            else:
                # Fehler
                update_progress(ProcessingStatus.ERROR, 0.0, "Fehler bei der Generierung")
                for error in result.errors:
                    self.model.add_log_message(f"❌ {error}")

        except Exception as e:
            logger.error(f"Fehler bei der Generierung: {e}")
            self.model.update_progress(ProcessingStatus.ERROR, 0.0, f"Fehler: {str(e)}")
            self.model.add_log_message(f"❌ Unerwarteter Fehler: {e}")

    def cancel_generation(self):
        """Bricht die laufende Generierung ab"""
        # TODO: Implementiere Abbruch-Mechanismus
        pass

    def reset(self):
        """Setzt alles zurück"""
        self.model.reset()

    def _load_lyrics(self, file_path: str) -> Lyrics:
        """Lädt Lyrics aus Datei"""
        lines = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple Zeilen-basierte Verarbeitung
        for line in content.strip().split('\n'):
            if not line.strip():
                continue

            # Einfache Silben-Trennung (kann verbessert werden)
            words = line.split()
            syllables = []

            for word in words:
                # UltraStar-Konvention: Silbe am Wortende trägt ein
                # Leerzeichen, sonst kleben Wörter in der Anzeige zusammen
                syllables.append(Syllable(word + ' '))

            lines.append(LyricLine(syllables))

        return Lyrics(lines)
