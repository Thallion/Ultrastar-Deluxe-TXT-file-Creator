# application/interfaces/audio_processor_interface.py
"""
Interface: Audio Processor
Definiert die Schnittstelle für Audio-Verarbeitung
"""
from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class AudioProcessorInterface(ABC):
    """Interface für Audio-Verarbeitung"""

    @abstractmethod
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, float]:
        """
        Lädt eine Audio-Datei

        Args:
            file_path: Pfad zur Audio-Datei

        Returns:
            Tuple von (audio_data, sample_rate)
        """
        pass

    @abstractmethod
    def detect_onsets(self, audio: np.ndarray, sr: float) -> np.ndarray:
        """
        Erkennt Onsets (Anfänge von Noten)

        Args:
            audio: Audio-Daten
            sr: Sample Rate

        Returns:
            Array von Onset-Zeiten in Sekunden
        """
        pass

    @abstractmethod
    def extract_pitch(self, audio: np.ndarray, sr: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extrahiert Pitch-Informationen

        Args:
            audio: Audio-Daten
            sr: Sample Rate

        Returns:
            Tuple von (frequencies, confidences, times)
        """
        pass

    @abstractmethod
    def estimate_tempo(self, audio: np.ndarray, sr: float) -> float:
        """
        Schätzt das Tempo

        Args:
            audio: Audio-Daten
            sr: Sample Rate

        Returns:
            Tempo in BPM
        """
        pass
