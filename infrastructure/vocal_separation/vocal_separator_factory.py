# infrastructure/vocal_separation/vocal_separator_factory.py
"""
Factory für Vocal Separators
"""
from typing import Optional
import logging

from application.interfaces.vocal_separator_interface import VocalSeparatorInterface
from infrastructure.vocal_separation.demucs_separator import DemucsSeparator
from infrastructure.vocal_separation.spleeter_separator import SpleeterSeparator
from infrastructure.vocal_separation.basic_separator import BasicHarmonicSeparator


logger = logging.getLogger(__name__)


class VocalSeparatorFactory:
    """
    Factory zum Erstellen des besten verfügbaren Vocal Separators
    """

    @staticmethod
    def create(preferred: Optional[str] = None) -> VocalSeparatorInterface:
        """
        Erstellt den besten verfügbaren Separator

        Args:
            preferred: Bevorzugter Separator Name (optional)

        Returns:
            VocalSeparatorInterface Implementierung
        """
        # Versuche bevorzugten Separator
        if preferred:
            separator = VocalSeparatorFactory._create_by_name(preferred)
            if separator and separator.is_available():
                logger.info(f"Verwende bevorzugten Separator: {separator.get_name()}")
                return separator

        # Versuche Demucs (beste Qualität)
        demucs = DemucsSeparator()
        if demucs.is_available():
            logger.info(f"Verwende {demucs.get_name()}")
            return demucs

        # Versuche Spleeter
        spleeter = SpleeterSeparator()
        if spleeter.is_available():
            logger.info(f"Verwende {spleeter.get_name()}")
            return spleeter

        # Fallback: Basic Harmonic Separator
        logger.warning("Keine erweiterte Vocal-Separation verfügbar, verwende Basic-Methode")
        return BasicHarmonicSeparator()

    @staticmethod
    def _create_by_name(name: str) -> Optional[VocalSeparatorInterface]:
        """Erstellt Separator nach Name"""
        name_lower = name.lower()

        if "demucs" in name_lower:
            return DemucsSeparator()
        elif "spleeter" in name_lower:
            return SpleeterSeparator()
        elif "basic" in name_lower or "harmonic" in name_lower:
            return BasicHarmonicSeparator()

        return None
