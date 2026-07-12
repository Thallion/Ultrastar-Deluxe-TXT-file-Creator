# infrastructure/vocal_separation/basic_separator.py
"""
Konkrete Implementierung: Basic Harmonic Separator
Fallback wenn keine erweiterten Methoden verfügbar sind
"""
import numpy as np
import librosa
import logging
from pathlib import Path
import soundfile as sf

from application.interfaces.vocal_separator_interface import VocalSeparatorInterface


logger = logging.getLogger(__name__)


class BasicHarmonicSeparator(VocalSeparatorInterface):
    """
    Basis-Implementierung mit Harmonic-Percussive Source Separation
    """

    def __init__(self):
        self._temp_dir = Path("temp")
        self._temp_dir.mkdir(exist_ok=True)

    def separate(self, audio_path: str) -> str:
        """
        Separiert Vocals mit HPSS und Frequenz-Filterung
        """
        try:
            logger.info("Verwende Basic Harmonic Separation")

            # Lade Audio
            y, sr = librosa.load(audio_path, sr=22050)

            # Harmonic-Percussive Separation
            y_harmonic, y_percussive = librosa.effects.hpss(y, margin=8.0)

            # Spektral-Analyse
            S = librosa.stft(y_harmonic)
            S_power = np.abs(S) ** 2

            # Frequenz-Maske für Vocals (80-800 Hz)
            frequencies = librosa.fft_frequencies(sr=sr)
            vocal_mask = (frequencies >= 80) & (frequencies <= 800)

            # Wende Maske an
            S_vocal = S.copy()
            S_vocal[~vocal_mask] *= 0.1  # Dämpfe andere Frequenzen

            # Spektrale Energie für Vocal-Detection
            spectral_centroid = librosa.feature.spectral_centroid(S=S_power, sr=sr)

            # Erstelle zeitvariable Maske basierend auf spektralen Features
            time_frames = S.shape[1]
            time_mask = np.ones(time_frames)

            # Dämpfe Frames mit sehr hohem/niedrigem Spectral Centroid
            for i in range(time_frames):
                if spectral_centroid[0, i] < 200 or spectral_centroid[0, i] > 2000:
                    time_mask[i] = 0.3

            # Wende Zeit-Maske an
            S_vocal *= time_mask

            # Rücktransformation
            vocals = librosa.istft(S_vocal)

            # Normalisiere
            vocals = vocals / (np.max(np.abs(vocals)) + 1e-6) * 0.8

            # Speichere als temporäre Datei
            output_path = self._temp_dir / f"vocals_{Path(audio_path).stem}.wav"
            sf.write(output_path, vocals, sr)

            logger.info(f"Basic Separation abgeschlossen: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Basic Separation Fehler: {e}")
            return audio_path

    def is_available(self) -> bool:
        """Basic Separator ist immer verfügbar"""
        return True

    def get_name(self) -> str:
        """Gibt Namen zurück"""
        return "Basic Harmonic Separator"
