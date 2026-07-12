# infrastructure/vocal_separation/spleeter_separator.py
"""
Konkrete Implementierung: Spleeter Vocal Separator
"""
import tempfile
import logging
from pathlib import Path
from typing import Optional

from application.interfaces.vocal_separator_interface import VocalSeparatorInterface


logger = logging.getLogger(__name__)


class SpleeterSeparator(VocalSeparatorInterface):
    """
    Implementiert VocalSeparatorInterface mit Spleeter
    """

    def __init__(self, stems: int = 2, output_dir: Optional[str] = None):
        self.stems = stems
        self.output_dir = output_dir or tempfile.gettempdir()
        self._available = self._check_availability()
        self._separator = None

    def _check_availability(self) -> bool:
        """Prüft ob Spleeter verfügbar ist"""
        try:
            from spleeter.separator import Separator  # noqa: F401
            return True
        except ImportError:
            return False

    def separate(self, audio_path: str) -> str:
        """Separiert Vocals mit Spleeter"""
        if not self._available:
            logger.warning("Spleeter nicht verfügbar, gebe Original zurück")
            return audio_path

        try:
            from spleeter.separator import Separator

            # Lazy Loading des Separators
            if self._separator is None:
                self._separator = Separator(f'spleeter:{self.stems}stems')

            output_path = Path(self.output_dir)
            output_path.mkdir(exist_ok=True)

            logger.info(f"Starte Spleeter Separation für {audio_path}")

            # Separiere Audio
            self._separator.separate_to_file(str(audio_path), str(output_path))

            # Finde Vocal-Datei
            audio_name = Path(audio_path).stem
            vocal_path = output_path / audio_name / "vocals.wav"

            if vocal_path.exists():
                logger.info(f"Vocals erfolgreich separiert: {vocal_path}")
                return str(vocal_path)
            else:
                logger.error("Vocal-Datei nicht gefunden")
                return audio_path

        except Exception as e:
            logger.error(f"Spleeter Fehler: {e}")
            return audio_path

    def is_available(self) -> bool:
        """Prüft Verfügbarkeit"""
        return self._available

    def get_name(self) -> str:
        """Gibt Namen zurück"""
        return f"Spleeter ({self.stems}stems)"
