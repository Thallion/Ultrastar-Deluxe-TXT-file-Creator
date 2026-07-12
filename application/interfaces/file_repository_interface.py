# application/interfaces/file_repository_interface.py
"""
Interface: File Repository
Definiert die Schnittstelle für Datei-Persistierung
"""
from abc import ABC, abstractmethod

from domain.entities.song import Song


class FileRepositoryInterface(ABC):
    """Interface für Datei-Operationen"""

    @abstractmethod
    def save_song(self, song: Song, file_path: str) -> None:
        """
        Speichert einen Song in eine Datei

        Args:
            song: Song-Objekt
            file_path: Ziel-Dateipfad
        """
        pass

    @abstractmethod
    def load_song(self, file_path: str) -> Song:
        """
        Lädt einen Song aus einer Datei

        Args:
            file_path: Quell-Dateipfad

        Returns:
            Song-Objekt
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Prüft ob eine Datei existiert"""
        pass
