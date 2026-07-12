# infrastructure/vocal_separation/demucs_separator.py
"""
Konkrete Implementierung: Demucs Vocal Separator
"""
import subprocess
import sys
import tempfile
import logging
from pathlib import Path
from typing import Optional

from application.interfaces.vocal_separator_interface import VocalSeparatorInterface


logger = logging.getLogger(__name__)


class DemucsSeparator(VocalSeparatorInterface):
    """
    Implementiert VocalSeparatorInterface mit Demucs
    """

    def __init__(self, model: str = "htdemucs", output_dir: Optional[str] = None):
        self.model = model
        self.output_dir = output_dir or tempfile.gettempdir()
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Prüft ob Demucs verfügbar ist"""
        try:
            import demucs  # noqa: F401
            return True
        except ImportError:
            return False

    def separate(self, audio_path: str) -> str:
        """Separiert Vocals mit Demucs"""
        if not self._available:
            logger.warning("Demucs nicht verfügbar, gebe Original zurück")
            return audio_path

        try:
            output_path = Path(self.output_dir)
            output_path.mkdir(exist_ok=True)

            logger.info(f"Starte Demucs Separation für {audio_path}")

            # Führe Demucs über Kommandozeile aus (stabiler)
            cmd = [
                sys.executable, "-m", "demucs.separate",
                "-n", self.model,
                "-o", str(output_path),
                "--two-stems", "vocals",
                str(audio_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Demucs Fehler: {result.stderr}")
                return audio_path

            # Finde Output-Datei
            audio_name = Path(audio_path).stem
            vocal_path = output_path / self.model / audio_name / "vocals.wav"

            if vocal_path.exists():
                logger.info(f"Vocals erfolgreich separiert: {vocal_path}")
                return str(vocal_path)
            else:
                logger.error("Vocal-Datei nicht gefunden")
                return audio_path

        except Exception as e:
            logger.error(f"Demucs Fehler: {e}")
            return audio_path

    def is_available(self) -> bool:
        """Prüft Verfügbarkeit"""
        return self._available

    def get_name(self) -> str:
        """Gibt Namen zurück"""
        return f"Demucs ({self.model})"
