# application/interfaces/vocal_separator_interface.py
"""
Interface: Vocal Separator
Definiert die Schnittstelle für Vocal-Separation
"""
from abc import ABC, abstractmethod


class VocalSeparatorInterface(ABC):
    """Interface für Vocal-Separation"""

    @abstractmethod
    def separate(self, audio_path: str) -> str:
        """
        Separiert Vocals von einer Audio-Datei

        Args:
            audio_path: Pfad zur Audio-Datei

        Returns:
            Pfad zur separierten Vocal-Datei
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Prüft ob der Separator verfügbar ist"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Gibt den Namen des Separators zurück"""
        pass
