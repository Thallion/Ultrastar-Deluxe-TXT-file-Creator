# infrastructure/audio/librosa_audio_processor.py
"""
Konkrete Implementierung: Librosa Audio Processor
"""
from typing import Tuple
import numpy as np
import librosa
import logging

from application.interfaces.audio_processor_interface import AudioProcessorInterface


logger = logging.getLogger(__name__)


class LibrosaAudioProcessor(AudioProcessorInterface):
    """
    Implementiert AudioProcessorInterface mit Librosa
    """

    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length

        # Frequenz-Grenzen für menschliche Stimme
        self.fmin = 80.0   # ~E2
        self.fmax = 800.0  # ~G5

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, float]:
        """Lädt Audio-Datei mit Librosa"""
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            logger.info(f"Audio geladen: {len(audio)/sr:.1f}s @ {sr}Hz")
            return audio, sr
        except Exception as e:
            logger.error(f"Fehler beim Laden von {file_path}: {e}")
            raise

    def detect_onsets(self, audio: np.ndarray, sr: float) -> np.ndarray:
        """Erkennt Onsets mit Librosa"""
        onset_frames = librosa.onset.onset_detect(
            y=audio,
            sr=sr,
            hop_length=self.hop_length,
            backtrack=True,
            pre_max=3,
            post_max=3,
            pre_avg=3,
            post_avg=5,
            delta=0.05
        )

        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
        logger.info(f"Onsets erkannt: {len(onset_times)}")

        return onset_times

    def extract_pitch(self, audio: np.ndarray, sr: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extrahiert Pitch mit pYIN Algorithmus"""
        # pYIN für robuste Pitch-Erkennung
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=self.fmin,
            fmax=self.fmax,
            sr=sr,
            hop_length=self.hop_length,
            fill_na=0.0
        )

        # Zeit-Array
        times = librosa.frames_to_time(
            np.arange(len(f0)),
            sr=sr,
            hop_length=self.hop_length
        )

        # Konvertiere NaN zu 0 für Konsistenz
        f0 = np.nan_to_num(f0, nan=0.0)

        # Verwende voiced_probs als Confidence, falls verfügbar
        if voiced_probs is None:
            # Erstelle Confidence basierend auf voiced_flag
            confidences = np.where(f0 > 0, 0.8, 0.0)
        else:
            confidences = np.nan_to_num(voiced_probs, nan=0.0)

        logger.info(f"Pitch extrahiert: {np.sum(f0 > 0)} voiced frames")

        return f0, confidences, times

    def estimate_tempo(self, audio: np.ndarray, sr: float) -> float:
        """Schätzt Tempo mit Librosa"""
        tempo, beats = librosa.beat.beat_track(
            y=audio,
            sr=sr,
            hop_length=self.hop_length,
            trim=False
        )

        # Neuere librosa-Versionen liefern ein Array zurück
        tempo = float(np.atleast_1d(tempo)[0])

        logger.info(f"Tempo geschätzt: {tempo:.1f} BPM")
        return tempo

    def separate_harmonic_percussive(self, audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Trennt harmonische und perkussive Komponenten
        Nützlich für Vocal-Extraktion
        """
        y_harmonic, y_percussive = librosa.effects.hpss(audio, margin=8.0)
        return y_harmonic, y_percussive
