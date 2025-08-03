#ultrastar_generator.py

#!/usr/bin/env python3
"""
UltraStar Deluxe Karaoke File Generator - Überarbeitete Version
Basierend auf Analyse von funktionierenden UltraStar-Dateien
"""

import os
import numpy as np
from numpy import ndarray
import librosa
from pathlib import Path
import argparse
from typing import List, Tuple, Dict, Optional
import re
import warnings
warnings.filterwarnings("ignore")

# Versuche erweiterte Vocal-Separation zu laden
try:
    from vocal_separator import integrate_vocal_separator, VocalSeparator
    ADVANCED_VOCAL_SEPARATION = True
except ImportError:
    ADVANCED_VOCAL_SEPARATION = False
    print("ℹ️  Erweiterte Vocal-Separation nicht verfügbar")
    print("   Für bessere Ergebnisse: pip install demucs")

class UltraStarGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # UltraStar Format Konstanten (angepasst basierend auf Beispieldateien)
        self.SAMPLE_RATE = 22050
        self.HOP_LENGTH = 512
        self.FMIN = 80.0   # Tiefste menschliche Stimme (ca. E2)
        self.FMAX = 800.0  # Höchste menschliche Stimme (ca. G5)
        
        # UltraStar spezifische Konstanten
        self.BEATS_PER_SECOND = 4  # Standard für UltraStar
        self.MIN_NOTE_DURATION_MS = 100  # Minimale Notendauer in ms
        self.MIN_NOTE_DURATION_BEATS = 2  # Minimale Notendauer in Beats
    
    def analyze_reference_files(self, reference_dir: str = ".") -> Dict:
        """
        Analysiert UltraStar-Referenzdateien um typische Werte zu lernen
        """
        reference_data = {
            'bpm_range': [],
            'gap_range': [],
            'pitch_range': [],
            'beat_patterns': []
        }
        
        ref_path = Path(reference_dir)
        for txt_file in ref_path.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('#BPM:'):
                        bpm = float(line.split(':')[1].replace(',', '.'))
                        reference_data['bpm_range'].append(bpm)
                    elif line.startswith('#GAP:'):
                        gap = float(line.split(':')[1].replace(',', '.'))
                        reference_data['gap_range'].append(gap)
                    elif line.startswith((':', '*', 'F', 'R', 'G')):
                        parts = line.split()
                        if len(parts) >= 4:
                            pitch = int(parts[3])
                            reference_data['pitch_range'].append(pitch)
            except:
                continue
        
        # Statistiken berechnen
        if reference_data['bpm_range']:
            print(f"📊 Referenz-Analyse:")
            print(f"   BPM-Bereich: {min(reference_data['bpm_range']):.1f} - {max(reference_data['bpm_range']):.1f}")
            print(f"   GAP-Bereich: {min(reference_data['gap_range']):.0f} - {max(reference_data['gap_range']):.0f} ms")
            if reference_data['pitch_range']:
                print(f"   Pitch-Bereich: {min(reference_data['pitch_range'])} - {max(reference_data['pitch_range'])}")
        
        return reference_data
    
    def separate_vocals(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """
        Verbesserte Vocal-Separation mit Fokus auf Gesangsfrequenzen
        """
        try:
            # Lade Audio
            y, sr = librosa.load(audio_path, sr=self.SAMPLE_RATE)
            
            # Harmonic-Percussive Separation
            y_harmonic, y_percussive = librosa.effects.hpss(y, margin=8.0)
            
            # Spektrale Eigenschaften berechnen
            S = librosa.stft(y_harmonic, hop_length=self.HOP_LENGTH)
            S_power = np.abs(S) ** 2
            
            # Mel-Spektrogramm für bessere Vocal-Erkennung
            mel_spec = librosa.feature.melspectrogram(
                S=S_power, sr=sr, n_mels=128, fmin=self.FMIN, fmax=self.FMAX
            )
            
            # Vocal-Aktivitätserkennung
            spectral_rolloff = librosa.feature.spectral_rolloff(S=S_power, sr=sr, roll_percent=0.85)
            spectral_centroid = librosa.feature.spectral_centroid(S=S_power, sr=sr)
            
            # Frequenz-Maske für Vocals
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=S.shape[0]*2-1)
            vocal_mask = (frequencies >= self.FMIN) & (frequencies <= self.FMAX)
            
            # Spektrale Energie in Vocal-Bereich
            S_vocal = S.copy()
            S_vocal[~vocal_mask] *= 0.1
            
            # Rücktransformation
            vocals = librosa.istft(S_vocal, hop_length=self.HOP_LENGTH)
            
            return vocals, sr
            
        except Exception as e:
            print(f"❌ Vocal-Separation Fehler: {e}")
            y, sr = librosa.load(audio_path, sr=self.SAMPLE_RATE)
            return y, sr
    
    def detect_onsets_and_tempo(self, audio: np.ndarray, sr: float) -> Tuple[np.ndarray, float]:
        """
        Verbesserte Onset-Detection und Tempo-Schätzung
        """
        # Onset Detection mit verschiedenen Methoden
        onset_frames = librosa.onset.onset_detect(
            y=audio, sr=sr, hop_length=self.HOP_LENGTH,
            backtrack=True, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.05
        )
        
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.HOP_LENGTH)
        
        # Tempo-Schätzung mit dynamischer Programmierung
        tempo, beats = librosa.beat.beat_track(
            y=audio, sr=sr, hop_length=self.HOP_LENGTH, trim=False
        )
        
        # UltraStar verwendet oft höhere BPM-Werte
        # Analysiere verschiedene Tempo-Multiplikatoren
        tempo_candidates = []
        for multiplier in [1, 2, 4, 8]:
            candidate_bpm = tempo * multiplier
            if 100 <= candidate_bpm <= 500:  # Typischer UltraStar-Bereich
                tempo_candidates.append(candidate_bpm)
        
        # Wähle BPM im typischen UltraStar-Bereich (200-400)
        best_bpm = tempo
        for bpm in tempo_candidates:
            if 200 <= bpm <= 400:
                best_bpm = bpm
                break
        
        print(f"🎵 Tempo erkannt: {tempo:.1f} BPM → UltraStar BPM: {best_bpm:.1f}")
        
        return onset_times, best_bpm
    
    def detect_pitch_advanced(self, audio: np.ndarray, sr: float, onset_times: np.ndarray) -> List[Dict]:
        """
        Fortgeschrittene Pitch-Detection mit Onset-Synchronisation
        """
        pitch_data = []
        
        # Verwende pYIN für robuste Pitch-Detection
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, fmin=self.FMIN, fmax=self.FMAX, sr=sr,
            hop_length=self.HOP_LENGTH, fill_na=0.0
        )
        
        times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=self.HOP_LENGTH)
        
        # Segmentiere basierend auf Onsets
        segments = []
        for i in range(len(onset_times) - 1):
            start_time = onset_times[i]
            end_time = onset_times[i + 1]
            
            # Finde Frames im Segment
            mask = (times >= start_time) & (times < end_time)
            segment_f0 = f0[mask]
            segment_probs = voiced_probs[mask] if voiced_probs is not None else np.ones_like(segment_f0)
            
            if len(segment_f0) > 0 and np.any(segment_f0 > 0):
                # Berechne durchschnittliche Frequenz (gewichtet nach Wahrscheinlichkeit)
                valid_f0 = segment_f0[segment_f0 > 0]
                valid_probs = segment_probs[segment_f0 > 0]
                
                if len(valid_f0) > 0:
                    avg_freq = np.average(valid_f0, weights=valid_probs)
                    confidence = np.mean(valid_probs)
                    
                    pitch_data.append({
                        'start_time': start_time,
                        'duration': end_time - start_time,
                        'frequency': avg_freq,
                        'confidence': confidence
                    })
        
        return pitch_data
    
    def frequency_to_ultrastar_pitch(self, frequency: float) -> int:
        """
        Konvertiert Frequenz zu UltraStar Pitch (typisch -10 bis +40)
        Basierend auf Analyse der Beispieldateien
        """
        if frequency <= 0:
            return 0
        
        # MIDI-Note berechnen (A4 = 440Hz = MIDI 69)
        midi_note = 69 + 12 * np.log2(frequency / 440.0)
        
        # UltraStar verwendet relative Tonhöhen um C4 (MIDI 60)
        # Bereich typisch -10 bis +40
        ultrastar_pitch = int(round(midi_note - 60))
        
        # Begrenze auf typischen UltraStar-Bereich
        return max(-10, min(40, ultrastar_pitch))
    
    def ms_to_beats(self, time_ms: float, bpm: float, gap_ms: float = 0) -> int:
        """
        Konvertiert Zeit in Millisekunden zu UltraStar Beats
        """
        # UltraStar Beat-Formel
        beats_per_minute = bpm
        ms_per_beat = 60000.0 / beats_per_minute
        
        # Zeit relativ zum GAP
        relative_time_ms = time_ms - gap_ms
        
        if relative_time_ms < 0:
            return 0
        
        beats = relative_time_ms / ms_per_beat
        return max(0, int(round(beats)))
    
    def duration_to_beats(self, duration_ms: float, bpm: float) -> int:
        """
        Konvertiert Dauer in Millisekunden zu Beats
        """
        ms_per_beat = 60000.0 / bpm
        beats = duration_ms / ms_per_beat
        return max(self.MIN_NOTE_DURATION_BEATS, int(round(beats)))
    
    def parse_lyrics(self, lyrics_path: str) -> List[str]:
        """
        Verbesserte Lyrics-Verarbeitung
        """
        syllables = []
        
        try:
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Entferne LRC-Timestamps falls vorhanden
            content = re.sub(r'\[\d{2}:\d{2}(?:\.\d{2})?\]', '', content)
            
            # Verarbeite Zeile für Zeile
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Teile in Wörter
                words = line.split()
                
                for word in words:
                    # Entferne Satzzeichen am Ende
                    word_clean = word.rstrip('.,!?;:')
                    
                    # Erkenne Silben (vereinfacht)
                    # TODO: Bessere Silbentrennung implementieren
                    if len(word_clean) <= 3:
                        syllables.append(word_clean)
                    elif len(word_clean) <= 6:
                        # Teile in 2 Silben
                        mid = len(word_clean) // 2
                        syllables.append(word_clean[:mid])
                        syllables.append(word_clean[mid:])
                    else:
                        # Teile in 3 Silben
                        third = len(word_clean) // 3
                        syllables.append(word_clean[:third])
                        syllables.append(word_clean[third:third*2])
                        syllables.append(word_clean[third*2:])
            
        except Exception as e:
            print(f"❌ Lyrics-Parsing Fehler: {e}")
        
        return syllables
    
    def create_notes_from_pitch_data(self, pitch_data: List[Dict], bpm: float, gap_ms: float) -> List[Dict]:
        """
        Erstellt UltraStar-Noten aus Pitch-Daten
        """
        notes = []
        
        for pitch_info in pitch_data:
            start_time_ms = pitch_info['start_time'] * 1000
            duration_ms = pitch_info['duration'] * 1000
            
            # Filtere zu kurze Noten
            if duration_ms < self.MIN_NOTE_DURATION_MS:
                continue
            
            # Konvertiere zu Beats
            start_beat = self.ms_to_beats(start_time_ms, bpm, gap_ms)
            duration_beats = self.duration_to_beats(duration_ms, bpm)
            
            # Konvertiere Pitch
            pitch = self.frequency_to_ultrastar_pitch(pitch_info['frequency'])
            
            # Bestimme Note-Typ basierend auf Confidence
            note_type = ':' # Normal
            if pitch_info['confidence'] > 0.8 and duration_beats > 6:
                note_type = '*'  # Golden note für lange, stabile Töne
            
            notes.append({
                'type': note_type,
                'beat': start_beat,
                'duration': duration_beats,
                'pitch': pitch,
                'confidence': pitch_info['confidence']
            })
        
        # Sortiere nach Beat
        notes.sort(key=lambda x: x['beat'])
        
        # Füge Pausen ein
        notes_with_pauses = []
        last_end_beat = 0
        
        for note in notes:
            # Füge Pause ein wenn Lücke > 8 Beats
            if note['beat'] - last_end_beat > 8:
                notes_with_pauses.append({
                    'type': '-',
                    'beat': last_end_beat + 2
                })
            
            notes_with_pauses.append(note)
            last_end_beat = note['beat'] + note['duration']
        
        return notes_with_pauses
    
    def assign_lyrics_to_notes(self, notes: List[Dict], lyrics: List[str]) -> List[Dict]:
        """
        Intelligente Zuordnung von Lyrics zu Noten
        """
        vocal_notes = [n for n in notes if n['type'] != '-']
        lyrics_index = 0
        
        for note in notes:
            if note['type'] == '-':
                continue
            
            if lyrics_index < len(lyrics):
                note['text'] = lyrics[lyrics_index]
                lyrics_index += 1
            else:
                # Verwende Tilde für gehaltene Töne
                note['text'] = '~'
        
        return notes
    
    def generate_ultrastar_file(self, 
                              notes: List[Dict],
                              title: str,
                              artist: str,
                              audio_filename: str,
                              bpm: float,
                              gap_ms: float,
                              end_ms: Optional[float] = None) -> str:
        """
        Generiert UltraStar .txt Datei
        """
        if not notes:
            print("❌ Keine Noten zum Verarbeiten!")
            return ""
        
        output_file = self.output_dir / f"{artist} - {title}.txt"
        
        # Berechne End-Zeit wenn nicht angegeben
        if end_ms is None:
            last_vocal_note = max([n for n in notes if n['type'] != '-'], 
                                 key=lambda x: x['beat'] + x.get('duration', 0))
            end_beat = last_vocal_note['beat'] + last_vocal_note.get('duration', 0)
            ms_per_beat = 60000.0 / bpm
            end_ms = gap_ms + (end_beat * ms_per_beat) + 2000  # +2 Sekunden Buffer
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"#ARTIST:{artist}\n")
            f.write(f"#TITLE:{title}\n")
            f.write(f"#MP3:{audio_filename}\n")
            f.write(f"#BPM:{bpm:.2f}\n")
            f.write(f"#GAP:{int(gap_ms)}\n")
            f.write(f"#VIDEO:{Path(audio_filename).stem}.mp4\n")
            f.write(f"#CREATOR:UltraStar Generator\n")
            f.write(f"#LANGUAGE:Unknown\n")
            f.write(f"#YEAR:2024\n")
            f.write(f"#END:{int(end_ms)}\n")
            f.write("\n")
            
            # Noten
            for note in notes:
                if note['type'] == '-':
                    f.write(f"- {note['beat']}\n")
                else:
                    text = note.get('text', '~')
                    f.write(f"{note['type']} {note['beat']} {note['duration']} {note['pitch']} {text}\n")
            
            # Ende
            f.write("E\n")
        
        print(f"✅ UltraStar-Datei erstellt: {output_file}")
        return str(output_file)
    
    def process_files(self, audio_path: str, lyrics_path: str = None, 
                     title: str = None, artist: str = None, 
                     reference_file: str = None) -> Optional[str]:
        """
        Hauptprozess: Audio + Lyrics zu UltraStar Datei
        """
        print("🎵 UltraStar Generation - Überarbeitete Version")
        print("=" * 50)
        
        # Dateinamen extrahieren falls nicht angegeben
        audio_file = Path(audio_path)
        if not title:
            title = audio_file.stem.split(' - ')[-1] if ' - ' in audio_file.stem else audio_file.stem
        if not artist:
            artist = audio_file.stem.split(' - ')[0] if ' - ' in audio_file.stem else "Unknown Artist"
        
        print(f"🎵 Titel: {title}")
        print(f"🎤 Artist: {artist}")
        
        # Analysiere Referenzdateien
        self.analyze_reference_files(audio_file.parent)
        
        # 1. Vocals separieren
        print("\n🎤 Separiere Vocals...")
        vocals, sr = self.separate_vocals(audio_path)
        
        # 2. Onset Detection und Tempo
        print("🥁 Erkenne Tempo und Rhythmus...")
        onset_times, bpm = self.detect_onsets_and_tempo(vocals, sr)
        print(f"   → {len(onset_times)} Onsets erkannt")
        
        # 3. Pitch Detection
        print("🎼 Erkenne Tonhöhen...")
        pitch_data = self.detect_pitch_advanced(vocals, sr, onset_times)
        print(f"   → {len(pitch_data)} Pitch-Segmente erkannt")
        
        if not pitch_data:
            print("❌ Keine Tonhöhen erkannt!")
            return None
        
        # 4. GAP berechnen (Zeit bis zur ersten Note)
        first_note_ms = pitch_data[0]['start_time'] * 1000
        gap_ms = max(0, first_note_ms - 500)  # 500ms Vorlauf
        
        print(f"\n📊 Timing-Parameter:")
        print(f"   BPM: {bpm:.2f}")
        print(f"   GAP: {gap_ms:.0f} ms")
        
        # 5. Erstelle Noten
        print("\n🎯 Erstelle Noten...")
        notes = self.create_notes_from_pitch_data(pitch_data, bpm, gap_ms)
        print(f"   → {len([n for n in notes if n['type'] != '-'])} Noten erstellt")
        
        # 6. Lyrics laden und zuordnen
        if lyrics_path and Path(lyrics_path).exists():
            print("\n📝 Lade und verarbeite Lyrics...")
            lyrics = self.parse_lyrics(lyrics_path)
            print(f"   → {len(lyrics)} Silben extrahiert")
            notes = self.assign_lyrics_to_notes(notes, lyrics)
        
        # 7. UltraStar Datei generieren
        print("\n📄 Generiere UltraStar Datei...")
        
        # Audio-Dauer für END-Tag
        audio_duration_s = librosa.get_duration(y=vocals, sr=sr)
        end_ms = audio_duration_s * 1000
        
        ultrastar_file = self.generate_ultrastar_file(
            notes, title, artist, audio_file.name, bpm, gap_ms, end_ms
        )
        
        if ultrastar_file:
            print("\n🎉 Erfolgreich abgeschlossen!")
            print(f"\n💡 Nächste Schritte:")
            print(f"1. Kopiere die .txt und .mp3 Datei in deinen UltraStar Songs-Ordner")
            print(f"2. Öffne die Datei im UltraStar Creator für Feinabstimmung")
            print(f"3. Füge ggf. Video, Cover und Background hinzu")
            
            return ultrastar_file
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description='UltraStar Deluxe Karaoke Generator - Überarbeitete Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python ultrastar_generator.py song.mp3
  python ultrastar_generator.py song.mp3 --lyrics lyrics.txt
  python ultrastar_generator.py "Artist - Title.mp3" --lyrics lyrics.txt
  python ultrastar_generator.py song.mp3 --title "My Song" --artist "Artist Name"
        """
    )
    
    parser.add_argument('audio', help='Audio-Datei (MP3, WAV, etc.)')
    parser.add_argument('--lyrics', '-l', help='Lyrics-Datei (TXT, LRC)')
    parser.add_argument('--title', '-t', help='Song-Titel (Standard: aus Dateiname)')
    parser.add_argument('--artist', '-a', help='Künstler (Standard: aus Dateiname)')
    parser.add_argument('--output', '-o', default='output', help='Output-Verzeichnis')
    
    args = parser.parse_args()
    
    if not Path(args.audio).exists():
        print(f"❌ Audio-Datei nicht gefunden: {args.audio}")
        return
    
    # Verwende erweiterte Vocal-Separation wenn verfügbar
    if ADVANCED_VOCAL_SEPARATION:
        GeneratorClass = integrate_vocal_separator(UltraStarGenerator)
        print("✨ Verwende erweiterte Vocal-Separation")
    else:
        GeneratorClass = UltraStarGenerator
    
    generator = GeneratorClass(args.output)
    result = generator.process_files(
        args.audio, 
        args.lyrics, 
        args.title, 
        args.artist
    )
    
    if result:
        print(f"\n✨ UltraStar Datei erstellt: {result}")
    else:
        print("\n❌ Fehler bei der Generierung!")
        print("\n💡 Tipps für bessere Ergebnisse:")
        print("- Verwende hochwertige Audio-Dateien (MP3 320kbps oder WAV)")
        print("- Stelle sicher, dass Gesang deutlich hörbar ist")
        print("- Verwende Songs mit klarer Melodie")
        print("- Füge eine Lyrics-Datei hinzu für bessere Text-Synchronisation")
        if not ADVANCED_VOCAL_SEPARATION:
            print("- Installiere 'demucs' für bessere Vocal-Separation: pip install demucs")


if __name__ == "__main__":
    main()