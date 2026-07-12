# tests/domain/test_value_objects.py
"""
Unit Tests für Value Objects
"""
from domain.value_objects.pitch import Pitch, ULTRASTAR_PITCH_MIN, ULTRASTAR_PITCH_MAX
from domain.value_objects.beat import Beat


class TestPitch:
    """Tests für Pitch Value Object"""

    def test_pitch_from_frequency(self):
        """Test: Pitch aus Frequenz erstellen"""
        # A4 = 440Hz = MIDI 69
        pitch = Pitch.from_frequency(440.0)

        assert pitch.frequency == 440.0
        assert pitch.midi_note == 69
        assert pitch.ultrastar_pitch == 9  # 69 - 60

        # C4 = ~261.63Hz = MIDI 60
        pitch_c4 = Pitch.from_frequency(261.63)
        assert pitch_c4.midi_note == 60
        assert pitch_c4.ultrastar_pitch == 0

    def test_pitch_from_midi(self):
        """Test: Pitch aus MIDI-Note erstellen"""
        pitch = Pitch.from_midi_note(60)  # C4

        assert pitch.midi_note == 60
        assert pitch.ultrastar_pitch == 0
        assert 261 < pitch.frequency < 262

    def test_pitch_limits(self):
        """Test: Pitch-Grenzen"""
        # Sehr hohe Frequenz
        high_pitch = Pitch.from_frequency(8000.0)
        assert high_pitch.ultrastar_pitch <= ULTRASTAR_PITCH_MAX

        # Sehr tiefe Frequenz
        low_pitch = Pitch.from_frequency(20.0)
        assert low_pitch.ultrastar_pitch >= ULTRASTAR_PITCH_MIN

    def test_official_pitch_values_not_clamped(self):
        """Test: In offiziellen Songs vorkommende Pitches werden nicht gestaucht"""
        # Pitch 72 = MIDI 132? Nein: MIDI 60 + 72 = 132 unrealistisch,
        # aber Pitch aus hoher Gesangsfrequenz (~C6 = MIDI 84 → Pitch 24)
        pitch = Pitch.from_midi_note(84)
        assert pitch.ultrastar_pitch == 24

        low = Pitch.from_midi_note(50)  # D3 → Pitch -10 (offiziell belegt)
        assert low.ultrastar_pitch == -10

    def test_note_names(self):
        """Test: Notennamen"""
        c4 = Pitch.from_midi_note(60)
        assert c4.get_note_name() == "C4"

        a4 = Pitch.from_midi_note(69)
        assert a4.get_note_name() == "A4"

        fsharp3 = Pitch.from_midi_note(54)
        assert fsharp3.get_note_name() == "F#3"


class TestBeat:
    """Tests für Beat Value Object"""

    def test_beat_from_time(self):
        """Test: Beat aus Zeit erstellen"""
        # BPM = 240, GAP = 1000ms
        # Beat 0 = 1000ms
        # Beat 4 = 2000ms (1000 + 4 * 250)
        beat = Beat.from_time(2000.0, 240.0, 1000.0)

        assert beat.beat_number == 4
        assert beat.time_ms == 2000.0
        assert beat.bpm == 240.0
        assert beat.gap_ms == 1000.0

    def test_beat_from_number(self):
        """Test: Beat aus Beat-Nummer erstellen"""
        beat = Beat.from_beat_number(10, 120.0, 500.0)

        # ms_per_beat = 60000 / 120 = 500
        # time = 500 + 10 * 500 = 5500
        assert beat.time_ms == 5500.0
        assert beat.beat_number == 10

    def test_negative_time_handling(self):
        """Test: Negative Zeit vor GAP"""
        beat = Beat.from_time(500.0, 240.0, 1000.0)
        assert beat.beat_number == 0  # Kann nicht negativ sein

    def test_next_beat(self):
        """Test: Nächster Beat"""
        beat = Beat.from_beat_number(5, 240.0, 1000.0)
        next_beat = beat.to_next_beat()

        assert next_beat.beat_number == 6
        assert next_beat.time_ms == beat.time_ms + (60000.0 / 240.0)
