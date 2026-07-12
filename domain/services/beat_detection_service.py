# domain/services/beat_detection_service.py
"""
Domain Service: Beat Detection
Geschäftslogik für Beat- und Tempo-Erkennung
"""
import numpy as np

from domain.value_objects.beat import Beat


class TempoEstimate:
    """Repräsentiert eine Tempo-Schätzung"""
    def __init__(self, bpm: float, confidence: float):
        self.bpm = bpm
        self.confidence = confidence

        # UltraStar typische BPM-Bereiche
        self.ultrastar_bpm = self._adjust_for_ultrastar(bpm)

    def _adjust_for_ultrastar(self, bpm: float) -> float:
        """
        Passt BPM an UltraStar-Konventionen an.

        UltraStar-Dateien verwenden ein Vielfaches des realen Tempos,
        damit Silben fein genug quantisiert werden können. Offizielle
        Dateien liegen typischerweise zwischen 200 und 430 BPM.
        """
        candidates = []
        for multiplier in [1, 2, 4, 8]:
            candidate = bpm * multiplier
            if 100 <= candidate <= 500:
                candidates.append(candidate)

        # Wähle BPM im bevorzugten Bereich
        for candidate in candidates:
            if 200 <= candidate <= 400:
                return candidate

        # Fallback: nächster gültiger Wert
        return candidates[0] if candidates else bpm


class BeatDetectionService:
    """
    Domain Service für Beat-Detection
    Enthält die Geschäftslogik für Tempo- und Beat-Erkennung
    """

    # Konstanten
    MIN_BPM = 50
    MAX_BPM = 600
    PREFERRED_BPM_MIN = 200
    PREFERRED_BPM_MAX = 400

    def estimate_tempo(self, onset_times: np.ndarray) -> TempoEstimate:
        """
        Schätzt das Tempo basierend auf Onset-Zeiten

        Args:
            onset_times: Array von Onset-Zeitpunkten in Sekunden

        Returns:
            TempoEstimate Objekt
        """
        if len(onset_times) < 2:
            return TempoEstimate(120.0, 0.0)  # Standard-Tempo

        # Berechne Inter-Onset-Intervalle
        intervals = np.diff(onset_times)

        # Filtere unrealistische Intervalle
        valid_intervals = intervals[(intervals > 0.1) & (intervals < 2.0)]

        if len(valid_intervals) == 0:
            return TempoEstimate(120.0, 0.0)

        # Histogramm-basierte Tempo-Schätzung
        tempo_candidates = 60.0 / valid_intervals  # BPM aus Intervallen

        # Erstelle Histogramm
        hist, bins = np.histogram(tempo_candidates, bins=50, range=(self.MIN_BPM, self.MAX_BPM))

        # Finde Peak
        peak_idx = np.argmax(hist)
        estimated_bpm = (bins[peak_idx] + bins[peak_idx + 1]) / 2

        # Confidence basierend auf Peak-Stärke
        confidence = hist[peak_idx] / len(tempo_candidates)

        return TempoEstimate(estimated_bpm, confidence)

    def calculate_gap(self, first_onset_time: float) -> float:
        """
        Berechnet den GAP (Offset bis zur ersten Note)

        Args:
            first_onset_time: Zeit der ersten Note in Sekunden

        Returns:
            GAP in Millisekunden
        """
        gap_ms = first_onset_time * 1000

        # Runde auf nächste 100ms für saubere Werte
        gap_ms = round(gap_ms / 100) * 100

        return max(0, gap_ms)

    def quantize_to_beat_grid(self,
                              time_ms: float,
                              bpm: float,
                              gap_ms: float,
                              grid_resolution: int = 1) -> Beat:
        """
        Quantisiert eine Zeit zum Beat-Grid

        Args:
            time_ms: Zeit in Millisekunden
            bpm: Beats per Minute
            gap_ms: GAP in Millisekunden
            grid_resolution: Grid-Weite in Beats (1 = jeder Beat,
                             4 = snap auf jeden 4. Beat)

        Returns:
            Beat Objekt (quantisiert)
        """
        if grid_resolution > 1:
            ms_per_beat = 60000.0 / bpm
            fractional_beats = max(0.0, (time_ms - gap_ms) / ms_per_beat)
            snapped = int(round(fractional_beats / grid_resolution)) * grid_resolution
            return Beat.from_beat_number(snapped, bpm, gap_ms)

        return Beat.from_time(time_ms, bpm, gap_ms)

    def calculate_note_duration_beats(self,
                                      duration_ms: float,
                                      bpm: float,
                                      min_duration_beats: int = 1) -> int:
        """
        Berechnet die Dauer einer Note in Beats

        Args:
            duration_ms: Dauer in Millisekunden
            bpm: Beats per Minute
            min_duration_beats: Minimale Dauer in Beats

        Returns:
            Dauer in Beats (gerundet)
        """
        ms_per_beat = 60000.0 / bpm
        beats = duration_ms / ms_per_beat

        # Runde und stelle Mindestdauer sicher
        return max(min_duration_beats, int(round(beats)))
