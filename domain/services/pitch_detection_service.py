# domain/services/pitch_detection_service.py
"""
Domain Service: Pitch Detection
Geschäftslogik für Tonhöhenerkennung
"""
from typing import List, Optional
import numpy as np

from domain.value_objects.pitch import Pitch


class PitchSegment:
    """Repräsentiert ein Segment mit erkannter Tonhöhe"""
    def __init__(self, start_time: float, duration: float, pitch: Pitch, confidence: float):
        self.start_time = start_time
        self.duration = duration
        self.pitch = pitch
        self.confidence = confidence

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration


class PitchDetectionService:
    """
    Domain Service für Pitch-Detection
    Enthält die Geschäftslogik für Tonhöhenerkennung
    """

    # Konstanten für menschliche Stimme
    HUMAN_VOICE_MIN_FREQ = 80.0   # ~E2
    HUMAN_VOICE_MAX_FREQ = 800.0  # ~G5
    MIN_SEGMENT_DURATION = 0.1    # Minimale Segmentdauer in Sekunden
    MIN_CONFIDENCE = 0.3          # Minimale Confidence für gültige Segmente

    def process_pitch_data(self,
                           frequencies: np.ndarray,
                           confidences: np.ndarray,
                           times: np.ndarray) -> List[PitchSegment]:
        """
        Verarbeitet rohe Pitch-Daten zu Pitch-Segmenten

        Args:
            frequencies: Array von Frequenzen
            confidences: Array von Confidence-Werten
            times: Array von Zeitstempeln

        Returns:
            Liste von PitchSegment Objekten
        """
        segments = []
        current_segment_start = None
        current_frequencies = []
        current_confidences = []

        for i in range(len(frequencies)):
            freq = frequencies[i]
            conf = confidences[i]
            time = times[i]

            # Prüfe ob gültiger Pitch
            is_valid = (freq > 0 and
                        self.HUMAN_VOICE_MIN_FREQ <= freq <= self.HUMAN_VOICE_MAX_FREQ and
                        conf >= self.MIN_CONFIDENCE)

            if is_valid:
                if current_segment_start is None:
                    current_segment_start = time
                current_frequencies.append(freq)
                current_confidences.append(conf)
            else:
                # Segment beenden wenn vorhanden
                if current_segment_start is not None:
                    segment = self._create_segment(
                        current_segment_start,
                        time - current_segment_start,
                        current_frequencies,
                        current_confidences
                    )
                    if segment:
                        segments.append(segment)

                    # Reset
                    current_segment_start = None
                    current_frequencies = []
                    current_confidences = []

        # Letztes Segment verarbeiten
        if current_segment_start is not None and current_frequencies:
            segment = self._create_segment(
                current_segment_start,
                times[-1] - current_segment_start,
                current_frequencies,
                current_confidences
            )
            if segment:
                segments.append(segment)

        return segments

    def _create_segment(self,
                        start_time: float,
                        duration: float,
                        frequencies: List[float],
                        confidences: List[float]) -> Optional[PitchSegment]:
        """Erstellt ein PitchSegment aus Rohdaten"""
        if duration < self.MIN_SEGMENT_DURATION or not frequencies:
            return None

        # Gewichteter Durchschnitt der Frequenzen
        avg_frequency = np.average(frequencies, weights=confidences)
        avg_confidence = np.mean(confidences)

        pitch = Pitch.from_frequency(avg_frequency)

        return PitchSegment(start_time, duration, pitch, avg_confidence)

    def merge_similar_segments(self,
                               segments: List[PitchSegment],
                               max_pitch_diff: int = 2,
                               max_gap: float = 0.1) -> List[PitchSegment]:
        """
        Verschmilzt ähnliche aufeinanderfolgende Segmente

        Args:
            segments: Liste von PitchSegmenten
            max_pitch_diff: Maximale Pitch-Differenz für Verschmelzung
            max_gap: Maximale Zeitlücke für Verschmelzung

        Returns:
            Verschmolzene Segmente
        """
        if not segments:
            return []

        merged = []
        current = segments[0]

        for next_segment in segments[1:]:
            # Prüfe ob Segmente verschmolzen werden können
            pitch_diff = abs(current.pitch.ultrastar_pitch - next_segment.pitch.ultrastar_pitch)
            time_gap = next_segment.start_time - current.end_time

            if pitch_diff <= max_pitch_diff and time_gap <= max_gap:
                # Verschmelze Segmente
                total_duration = next_segment.end_time - current.start_time
                avg_confidence = (current.confidence + next_segment.confidence) / 2

                # Verwende den Pitch des längeren Segments
                if next_segment.duration > current.duration:
                    pitch = next_segment.pitch
                else:
                    pitch = current.pitch

                current = PitchSegment(current.start_time, total_duration, pitch, avg_confidence)
            else:
                # Speichere aktuelles Segment und starte neues
                merged.append(current)
                current = next_segment

        # Letztes Segment hinzufügen
        merged.append(current)

        return merged
