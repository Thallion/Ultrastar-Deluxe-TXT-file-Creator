# domain/value_objects/pitch.py
"""
Value Object: Pitch
Repräsentiert eine Tonhöhe mit Konvertierungsmethoden
"""
from dataclasses import dataclass
import numpy as np

# Grenzen für UltraStar-Pitch-Werte (relativ zu C4).
# In offiziellen Songs kommen Werte von ca. -10 bis 72 vor,
# daher großzügige Grenzen statt der engen -20..50.
ULTRASTAR_PITCH_MIN = -60
ULTRASTAR_PITCH_MAX = 84


@dataclass(frozen=True)
class Pitch:
    """
    Immutable Value Object für Tonhöhe

    Attributes:
        frequency: Frequenz in Hz
        midi_note: MIDI Note Nummer
        ultrastar_pitch: UltraStar Pitch Wert (relativ zu C4)
    """
    frequency: float
    midi_note: int
    ultrastar_pitch: int

    @classmethod
    def from_frequency(cls, frequency: float) -> 'Pitch':
        """Erstellt Pitch aus Frequenz"""
        if frequency <= 0:
            return cls(0, 0, 0)

        # MIDI-Note berechnen (A4 = 440Hz = MIDI 69)
        midi_note = 69 + 12 * np.log2(frequency / 440.0)
        midi_note_rounded = int(round(midi_note))

        # UltraStar Pitch (relativ zu C4 = MIDI 60)
        ultrastar_pitch = midi_note_rounded - 60
        ultrastar_pitch = max(ULTRASTAR_PITCH_MIN, min(ULTRASTAR_PITCH_MAX, ultrastar_pitch))

        return cls(frequency, midi_note_rounded, ultrastar_pitch)

    @classmethod
    def from_midi_note(cls, midi_note: int) -> 'Pitch':
        """Erstellt Pitch aus MIDI Note"""
        frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
        ultrastar_pitch = midi_note - 60
        ultrastar_pitch = max(ULTRASTAR_PITCH_MIN, min(ULTRASTAR_PITCH_MAX, ultrastar_pitch))

        return cls(frequency, midi_note, ultrastar_pitch)

    def get_note_name(self) -> str:
        """Gibt den Notennamen zurück (z.B. 'C4', 'A#3')"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (self.midi_note // 12) - 1
        note_index = self.midi_note % 12
        return f"{note_names[note_index]}{octave}"
