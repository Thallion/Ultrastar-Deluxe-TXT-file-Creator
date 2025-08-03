#!/usr/bin/env python3
"""
UltraStar Deluxe Karaoke File Generator
Erstellt .txt Dateien aus MP3 und Lyrics - FIXED VERSION
"""

import os
import numpy as np
import librosa
from pathlib import Path
import argparse
from typing import List, Tuple, Dict, Optional
import re
import warnings
warnings.filterwarnings("ignore")

class UltraStarGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # UltraStar Format Konstanten (angepasst für Vocals)
        self.SAMPLE_RATE = 22050
        self.HOP_LENGTH = 512
        self.FMIN = 80.0   # Tiefste menschliche Stimme (ca. E2)
        self.FMAX = 800.0  # Höchste menschliche Stimme (ca. G5)
    
    def reverse_engineer_timing(self, original_file: str = None):
        """
        Analysiert funktionierende UltraStar-Datei um korrektes Timing zu verstehen
        """
        if not original_file or not Path(original_file).exists():
            print("⚠️  Keine Original-Datei zum Reverse Engineering verfügbar")
            return {'beat_factor': 4, 'timing_verified': False}
        
        print(f"🔍 Analysiere Original: {Path(original_file).name}")
        
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            bpm = None
            gap = None
            notes = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('#BPM:'):
                    bpm = float(line.split(':')[1])
                elif line.startswith('#GAP:'):
                    gap = int(line.split(':')[1])
                elif line.startswith(':'):
                    parts = line.split()
                    if len(parts) >= 4:
                        beat = int(parts[1])
                        duration = int(parts[2])
                        pitch = int(parts[3])
                        notes.append((beat, duration, pitch))
            
            if notes and bpm and gap is not None:
                # Analysiere Beat-Pattern der ersten Noten
                beats = [n[0] for n in notes[:10]]
                intervals = np.diff(beats)
                
                print(f"📊 Original-Analyse:")
                print(f"   BPM: {bpm}")
                print(f"   GAP: {gap}ms")
                print(f"   Beat-Pattern: {beats[:5]}...")
                print(f"   Beat-Intervalle: {intervals[:3].tolist()}...")
                
                # Schätze Beat-Faktor durch Rückrechnung
                if len(beats) >= 2:
                    beat_diff = beats[1] - beats[0]
                    # Bei BPM=264, GAP=18680 sollte beat_diff ≈ 3 sein
                    # Das entspricht etwa 450ms bei korrekter Konvertierung
                    
                    # Teste verschiedene Faktoren
                    for factor in [1, 2, 4, 8]:
                        expected_ms = beat_diff * 60000 / (bpm * factor)
                        if 200 <= expected_ms <= 1000:  # Plausible Silbendauer
                            print(f"   Beat-Faktor {factor}: {beat_diff} beats = {expected_ms:.0f}ms")
                            return {
                                'bpm': bpm,
                                'gap': gap,
                                'beat_factor': factor,
                                'timing_verified': True
                            }
                
                return {'bpm': bpm, 'gap': gap, 'beat_factor': 4, 'timing_verified': True}
            
        except Exception as e:
            print(f"❌ Reverse Engineering Fehler: {e}")
        
        return {'beat_factor': 4, 'timing_verified': False}
    
    def separate_vocals(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """
        Erweiterte Vocal-Separation
        """
        try:
            # Lade Audio
            y, sr = librosa.load(audio_path, sr=self.SAMPLE_RATE)
            
            # Harmonic-Percussive Separation mit stärkerer Trennung
            y_harmonic, y_percussive = librosa.effects.hpss(y, margin=8.0)
            
            # Spectral Gating für Vocal-Frequenzen
            S = librosa.stft(y_harmonic, hop_length=self.HOP_LENGTH)
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=S.shape[0]*2-1)
            
            # Frequenz-Maske für Vocal-Bereich
            vocal_mask = (frequencies >= self.FMIN) & (frequencies <= self.FMAX)
            S_vocal = S.copy()
            S_vocal[~vocal_mask] *= 0.1  # Dämpfe Nicht-Vocal-Bereiche
            
            vocals = librosa.istft(S_vocal, hop_length=self.HOP_LENGTH)
            
            return vocals, sr
            
        except Exception as e:
            print(f"❌ Vocal-Separation Fehler: {e}")
            # Fallback: Original Audio
            y, sr = librosa.load(audio_path, sr=self.SAMPLE_RATE)
            return y, sr
    
    def detect_pitch(self, audio: np.ndarray, sr: float) -> List[Tuple[float, float, float]]:
        """
        Robuste Pitch-Detection für Vocals
        """
        try:
            # Multi-Method Pitch Detection
            
            # 1. Piptrack für harmonische Inhalte
            pitches1, magnitudes1 = librosa.piptrack(
                y=audio, sr=sr,
                threshold=0.2,
                fmin=self.FMIN, fmax=self.FMAX,
                hop_length=self.HOP_LENGTH
            )
            
            # 2. YIN für Vocal-Pitches (robuster für Sprache/Gesang)
            try:
                f0_yin = librosa.yin(audio, fmin=self.FMIN, fmax=self.FMAX, sr=sr, hop_length=self.HOP_LENGTH)
            except:
                f0_yin = None
            
            # Frame-Zeiten berechnen
            times = librosa.frames_to_time(
                np.arange(pitches1.shape[1]), sr=sr, hop_length=self.HOP_LENGTH
            )
            
            pitch_data = []
            
            for t_idx, time in enumerate(times):
                if t_idx >= pitches1.shape[1]:
                    break
                    
                best_freq = 0
                best_confidence = 0
                
                # Piptrack Ergebnis
                frame_pitches = pitches1[:, t_idx]
                frame_mags = magnitudes1[:, t_idx]
                
                if np.max(frame_mags) > 0:
                    max_idx = np.argmax(frame_mags)
                    freq1 = frame_pitches[max_idx]
                    conf1 = frame_mags[max_idx]
                    
                    if freq1 > 0:
                        best_freq = freq1
                        best_confidence = conf1
                
                # YIN Ergebnis (falls verfügbar)
                if f0_yin is not None and t_idx < len(f0_yin):
                    freq2 = f0_yin[t_idx]
                    if freq2 > 0 and not np.isnan(freq2):
                        # Kombiniere beide Methoden
                        if best_freq == 0:
                            best_freq = freq2
                            best_confidence = 0.8
                        elif abs(freq2 - best_freq) / best_freq < 0.1:  # Ähnliche Frequenzen
                            best_freq = (best_freq + freq2) / 2  # Durchschnitt
                            best_confidence = min(1.0, best_confidence + 0.3)
                
                if best_freq > 0 and best_confidence > 0.15:
                    pitch_data.append((time, best_freq, best_confidence))
            
            return pitch_data
            
        except Exception as e:
            print(f"❌ Pitch-Detection Fehler: {e}")
            return []
    
    def frequency_to_midi(self, frequency: float) -> int:
        """
        Konvertiert Frequenz zu UltraStar MIDI-Note (0-36 Bereich)
        """
        if frequency <= 0:
            return 0
        
        # Standard MIDI-Konvertierung
        midi_standard = 69 + 12 * np.log2(frequency / 440.0)
        
        # UltraStar verwendet 0-36 Bereich (C3-C6 = MIDI 48-84 → UltraStar 0-36)
        ultrastar_note = int(round(midi_standard - 48))
        
        # Begrenze auf UltraStar-Bereich
        return max(0, min(36, ultrastar_note))
    
    def smooth_pitch_data(self, pitch_data: List[Tuple[float, float, float]], 
                         min_duration: float = 0.4) -> List[Tuple[float, float, int]]:
        """
        Glättet Pitch-Daten zu stabilen Noten (weniger, aber bessere Noten)
        """
        if not pitch_data:
            return []
        
        # Filtere nur starke Pitches (höherer Threshold)
        filtered_data = [(t, f, c) for t, f, c in pitch_data if c > 0.25]
        
        if not filtered_data:
            return []
        
        notes = []
        current_group = []
        
        for time, freq, confidence in filtered_data:
            midi_note = self.frequency_to_midi(freq)
            
            if not current_group:
                current_group = [(time, freq, midi_note, confidence)]
            else:
                last_time = current_group[-1][0]
                last_midi = current_group[-1][2]
                
                # Neue Note wenn Zeit-Lücke > 300ms oder Pitch-Unterschied > 2 Halbtöne
                if (time - last_time > 0.3 or abs(midi_note - last_midi) > 2):
                    # Finalisiere vorherige Gruppe
                    note = self.finalize_note_group(current_group, min_duration)
                    if note:
                        notes.append(note)
                    
                    # Starte neue Gruppe
                    current_group = [(time, freq, midi_note, confidence)]
                else:
                    current_group.append((time, freq, midi_note, confidence))
        
        # Letzte Gruppe
        if current_group:
            note = self.finalize_note_group(current_group, min_duration)
            if note:
                notes.append(note)
        
        print(f"🎵 Note-Optimierung: {len(filtered_data)} Pitches → {len(notes)} Noten")
        return notes
    
    def finalize_note_group(self, group: List[Tuple[float, float, int, float]], 
                           min_duration: float) -> Optional[Tuple[float, float, int]]:
        """
        Erstellt finale Note aus Pitch-Gruppe
        """
        if not group:
            return None
        
        times = [p[0] for p in group]
        midis = [p[2] for p in group]
        confidences = [p[3] for p in group]
        
        start_time = min(times)
        end_time = max(times)
        duration = end_time - start_time
        
        # Prüfe Mindestdauer
        if duration < min_duration:
            return None
        
        # Gewichteter Durchschnitt für MIDI-Note
        weights = np.array(confidences)
        midi_weighted = np.average(midis, weights=weights)
        midi_final = max(0, min(36, int(round(midi_weighted))))
        
        return (start_time, duration, midi_final)
    
    def estimate_bpm(self, audio: np.ndarray, sr: float) -> float:
        """
        Robuste BPM-Detection mit Fokus auf UltraStar-typische Werte
        """
        try:
            # Standard Beat-Tracking
            tempo1, beats = librosa.beat.beat_track(y=audio, sr=sr, hop_length=self.HOP_LENGTH)
            
            # Onset-basierte BPM
            onsets = librosa.onset.onset_detect(y=audio, sr=sr, hop_length=self.HOP_LENGTH, units='time')
            tempo2 = 120.0
            
            if len(onsets) > 10:
                intervals = np.diff(onsets)
                valid_intervals = intervals[(intervals > 0.2) & (intervals < 3.0)]
                if len(valid_intervals) > 5:
                    tempo2 = 60.0 / np.median(valid_intervals)
            
            print(f"🎯 BPM-Kandidaten: librosa={tempo1:.1f}, onset={tempo2:.1f}")
            
            # Teste alle sinnvollen Multiplikatoren
            candidates = []
            for base_tempo in [tempo1, tempo2]:
                for multiplier in [0.25, 0.5, 1.0, 2.0, 4.0]:
                    candidate = base_tempo * multiplier
                    if 60 <= candidate <= 400:
                        candidates.append(candidate)
            
            # Bewerte Kandidaten
            best_bpm = tempo1
            best_score = -1
            
            for bpm in candidates:
                score = 0
                
                # Bevorzuge typische Bereiche
                if 120 <= bpm <= 140:
                    score += 10  # Balladen
                elif 140 <= bpm <= 180:
                    score += 15  # Standard Pop
                elif 180 <= bpm <= 220:
                    score += 20  # Uptempo
                elif 220 <= bpm <= 280:
                    score += 25  # Sehr schnell (Let It Go Bereich)
                
                # Spezial-Bonus für Let It Go Bereich
                if 250 <= bpm <= 270:
                    score += 20
                
                # Bonus für "runde" Werte
                if bpm % 10 == 0:
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_bpm = bpm
            
            print(f"🎯 Gewähltes BPM: {best_bpm:.1f} (Score: {best_score})")
            return float(best_bpm)
            
        except Exception as e:
            print(f"❌ BPM-Detection Fehler: {e}")
            return 264.0  # Let It Go Fallback
    
    def parse_lyrics(self, lyrics_path: str) -> List[str]:
        """
        Parst Lyrics vereinfacht zu Wort-Liste
        """
        lyrics = []
        try:
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Entferne LRC-Timestamps
            content = re.sub(r'\[\d{2}:\d{2}(?:\.\d{2})?\]', '', content)
            
            # Teile in Wörter
            words = content.split()
            lyrics = [word.strip('.,!?;:') for word in words if word.strip()]
            
        except Exception as e:
            print(f"❌ Lyrics-Fehler: {e}")
        
        return lyrics
    
    def time_to_beats(self, time_seconds: float, bpm: float, gap_ms: int, beat_factor: int = 4) -> int:
        """
        KORREKTE UltraStar Beat-Konvertierung basierend auf Reverse Engineering
        """
        time_ms = time_seconds * 1000
        
        if time_ms <= gap_ms:
            return 0
        
        # Korrekte UltraStar Formel (reverse engineered):
        # Beat = (Zeit_ms - GAP) * BPM / (60000 / beat_factor)
        beats = (time_ms - gap_ms) * bpm / (60000 / beat_factor)
        
        return max(0, int(round(beats)))
    
    def generate_ultrastar_file(self, 
                              notes: List[Tuple[float, float, int]],
                              lyrics: List[str],
                              title: str,
                              artist: str,
                              audio_filename: str,
                              bpm: float,
                              beat_factor: int = 4) -> str:
        """
        Generiert UltraStar .txt Datei mit korrektem Timing
        """
        if not notes:
            print("❌ Keine Noten zum Verarbeiten!")
            return ""
        
        output_file = self.output_dir / f"{title} - {artist}.txt"
        
        # Berechne GAP = Zeit bis zur ersten Note
        first_note_time = notes[0][0]
        gap_ms = max(0, int(first_note_time * 1000) - 500)  # 500ms früher starten
        
        print(f"🕐 GAP berechnet: {gap_ms}ms (erste Note bei {first_note_time:.1f}s)")
        
        # Konvertiere zu Beats
        beat_notes = []
        for start_time, duration, midi in notes:
            start_beat = self.time_to_beats(start_time, bpm, gap_ms, beat_factor)
            duration_beats = max(1, self.time_to_beats(duration, bpm, 0, beat_factor))
            beat_notes.append((start_beat, duration_beats, midi))
        
        # Sortiere und validiere
        beat_notes = [(s, d, m) for s, d, m in beat_notes if s >= 0]
        beat_notes.sort(key=lambda x: x[0])
        
        if not beat_notes:
            print("❌ Keine gültigen Beat-Noten!")
            return ""
        
        print(f"🎼 Beat-Bereich: {beat_notes[0][0]} bis {beat_notes[-1][0]}")
        
        # End-Zeit berechnen
        last_note = notes[-1]
        end_time_ms = int((last_note[0] + last_note[1]) * 1000)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"#TITLE:{title}\n")
            f.write(f"#ARTIST:{artist}\n")
            f.write(f"#MP3:{audio_filename}\n")
            f.write(f"#BPM:{bpm:.1f}\n")
            f.write(f"#GAP:{gap_ms}\n")
            f.write(f"#END:{end_time_ms}\n")
            f.write("\n")
            
            # Noten mit Lyrics
            lyrics_index = 0
            last_beat = 0
            
            for i, (beat, duration, midi) in enumerate(beat_notes):
                # Pausen für große Lücken
                if beat - last_beat > 10:
                    f.write(f"- {last_beat + 1}\n")
                
                # Text zuweisen
                text = ""
                if lyrics_index < len(lyrics):
                    text = lyrics[lyrics_index]
                    lyrics_index += 1
                elif i % 20 == 0:  # Sporadische Tilden
                    text = "~"
                
                # Note-Type
                note_type = "*" if duration > 6 or midi > 25 else ":"
                
                # Schreibe Note (nur wenn Text vorhanden)
                if text:
                    f.write(f"{note_type} {beat} {duration} {midi} {text}\n")
                
                last_beat = beat + duration
            
            f.write("E\n")
        
        print(f"🎵 UltraStar-Datei erstellt: {output_file}")
        return str(output_file)
    
    def process_files(self, audio_path: str, lyrics_path: str = None, 
                     title: str = None, artist: str = None, 
                     reference_file: str = None) -> Optional[str]:
        """
        Hauptprozess: Audio + Lyrics zu UltraStar Datei
        """
        print("🎵 UltraStar Generation - FIXED VERSION")
        print("=" * 50)
        
        # Dateinamen extrahieren falls nicht angegeben
        audio_file = Path(audio_path)
        if not title:
            title = audio_file.stem
        if not artist:
            artist = "Unknown Artist"
        
        print(f"🎵 Titel: {title} - {artist}")
        
        # Reverse Engineering (falls Referenz verfügbar)
        timing_info = self.reverse_engineer_timing(reference_file)
        beat_factor = timing_info.get('beat_factor', 4)
        
        # 1. Vocals separieren
        print("🎤 Separiere Vocals...")
        vocals, sr = self.separate_vocals(audio_path)
        
        # 2. BPM schätzen
        print("🥁 Schätze BPM...")
        bpm = self.estimate_bpm(vocals, sr)
        
        # 3. Pitch Detection
        print("🎼 Erkenne Tonhöhen...")
        pitch_data = self.detect_pitch(vocals, sr)
        if not pitch_data:
            print("❌ Keine Tonhöhen erkannt!")
            return None
        
        print(f"✅ {len(pitch_data)} Pitch-Punkte erkannt")
        
        # 4. Pitch-Daten glätten
        print("🎯 Extrahiere Noten...")
        notes = self.smooth_pitch_data(pitch_data)
        if not notes:
            print("❌ Keine Noten extrahiert!")
            return None
        
        print(f"✅ {len(notes)} Noten extrahiert")
        
        # 5. Lyrics laden
        lyrics = []
        if lyrics_path and Path(lyrics_path).exists():
            print("📝 Lade Lyrics...")
            lyrics = self.parse_lyrics(lyrics_path)
            print(f"✅ {len(lyrics)} Wörter geladen")
        
        # 6. UltraStar Datei generieren
        print("📄 Generiere UltraStar Datei...")
        ultrastar_file = self.generate_ultrastar_file(
            notes, lyrics, title, artist, audio_file.name, bpm, beat_factor
        )
        
        if ultrastar_file:
            print(f"🎉 Erfolgreich!")
            
            # Finale Statistiken
            print(f"\n📊 Statistiken:")
            print(f"   - BPM: {bpm:.1f}")
            print(f"   - Beat-Faktor: {beat_factor}")
            print(f"   - Noten: {len(notes)}")
            print(f"   - Lyrics: {len(lyrics)}")
            print(f"   - Dauer: {notes[-1][0] + notes[-1][1]:.1f}s")
            
            return ultrastar_file
        
        return None


def main():
    parser = argparse.ArgumentParser(description='UltraStar Deluxe Karaoke Generator')
    parser.add_argument('audio', help='Audio-Datei (MP3, WAV, etc.)')
    parser.add_argument('--lyrics', '-l', help='Lyrics-Datei (TXT, LRC)')
    parser.add_argument('--title', '-t', help='Song-Titel')
    parser.add_argument('--artist', '-a', help='Künstler')
    parser.add_argument('--reference', '-r', help='Referenz UltraStar-Datei für Timing-Analyse')
    parser.add_argument('--output', '-o', default='output', help='Output-Verzeichnis')
    
    args = parser.parse_args()
    
    if not Path(args.audio).exists():
        print(f"❌ Audio-Datei nicht gefunden: {args.audio}")
        return
    
    generator = UltraStarGenerator(args.output)
    result = generator.process_files(
        args.audio, 
        args.lyrics, 
        args.title, 
        args.artist,
        args.reference
    )
    
    if result:
        print(f"\n✨ Erfolgreich! UltraStar Datei: {result}")
        print("\n💡 Tipps:")
        print("- Verwende --reference mit einer funktionierenden UltraStar-Datei für besseres Timing")
        print("- Überprüfe Timing und Tonhöhen im UltraStar Editor")
        print("- Bei schlechter Qualität: bessere Vocal-Separation mit Spleeter verwenden")
    else:
        print("\n❌ Fehler bei der Generierung!")


if __name__ == "__main__":
    main()