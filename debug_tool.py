#!/usr/bin/env python3
"""
UltraStar Debug Tool
Vergleicht und analysiert UltraStar .txt Dateien
"""

import re
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import argparse

class UltraStarParser:
    """Parser für UltraStar .txt Dateien"""
    
    def __init__(self):
        self.metadata = {}
        self.notes = []
    
    def parse_file(self, file_path: str) -> Dict:
        """Parst eine UltraStar .txt Datei"""
        self.metadata = {}
        self.notes = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Metadata
                if line.startswith('#'):
                    key, value = line[1:].split(':', 1)
                    self.metadata[key] = value
                
                # Noten
                elif line.startswith((':','*', 'F')):  # Normal, Golden, Freestyle
                    parts = line.split()
                    if len(parts) >= 4:
                        note_type = parts[0][0]
                        beat = int(parts[1])
                        duration = int(parts[2])
                        pitch = int(parts[3])
                        text = ' '.join(parts[4:]) if len(parts) > 4 else ''
                        
                        self.notes.append({
                            'type': note_type,
                            'beat': beat,
                            'duration': duration,
                            'pitch': pitch,
                            'text': text
                        })
                
                # Pausen
                elif line.startswith('-'):
                    beat = int(line.split()[1]) if len(line.split()) > 1 else 0
                    self.notes.append({
                        'type': '-',
                        'beat': beat,
                        'duration': 0,
                        'pitch': 0,
                        'text': ''
                    })
        
        return {
            'metadata': self.metadata,
            'notes': self.notes
        }

class UltraStarAnalyzer:
    """Analysiert und vergleicht UltraStar Dateien"""
    
    def __init__(self):
        self.parser = UltraStarParser()
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analysiert eine einzelne UltraStar Datei"""
        data = self.parser.parse_file(file_path)
        metadata = data['metadata']
        notes = data['notes']
        
        # Nur Gesangsnoten (keine Pausen)
        vocal_notes = [n for n in notes if n['type'] in [':', '*', 'F']]
        
        if not vocal_notes:
            return {'error': 'Keine Gesangsnoten gefunden'}
        
        analysis = {
            'file': Path(file_path).name,
            'metadata': metadata,
            'total_notes': len(vocal_notes),
            'note_types': {},
            'pitch_range': {},
            'duration_stats': {},
            'beat_stats': {},
            'lyrics_analysis': {}
        }
        
        # Note-Typen zählen
        for note_type in [':', '*', 'F']:
            count = len([n for n in vocal_notes if n['type'] == note_type])
            analysis['note_types'][note_type] = count
        
        # Pitch-Analyse
        pitches = [n['pitch'] for n in vocal_notes]
        analysis['pitch_range'] = {
            'min': min(pitches),
            'max': max(pitches),
            'mean': np.mean(pitches),
            'median': np.median(pitches),
            'std': np.std(pitches)
        }
        
        # Duration-Analyse
        durations = [n['duration'] for n in vocal_notes]
        analysis['duration_stats'] = {
            'min': min(durations),
            'max': max(durations),
            'mean': np.mean(durations),
            'median': np.median(durations)
        }
        
        # Beat-Analyse
        beats = [n['beat'] for n in vocal_notes]
        analysis['beat_stats'] = {
            'min': min(beats),
            'max': max(beats),
            'total_range': max(beats) - min(beats)
        }
        
        # Lyrics-Analyse
        texts = [n['text'] for n in vocal_notes if n['text']]
        total_chars = sum(len(text) for text in texts)
        avg_syllable_length = total_chars / len(texts) if texts else 0
        
        analysis['lyrics_analysis'] = {
            'total_syllables': len(texts),
            'avg_syllable_length': avg_syllable_length,
            'empty_notes': len([n for n in vocal_notes if not n['text'] or n['text'] == '~'])
        }
        
        return analysis
    
    def compare_files(self, file1: str, file2: str) -> Dict:
        """Vergleicht zwei UltraStar Dateien"""
        analysis1 = self.analyze_file(file1)
        analysis2 = self.analyze_file(file2)
        
        if 'error' in analysis1 or 'error' in analysis2:
            return {'error': 'Fehler beim Analysieren der Dateien'}
        
        comparison = {
            'file1': analysis1['file'],
            'file2': analysis2['file'],
            'metadata_diff': {},
            'pitch_comparison': {},
            'duration_comparison': {},
            'beat_comparison': {},
            'quality_assessment': {}
        }
        
        # Metadata-Vergleich
        for key in ['BPM', 'GAP']:
            val1 = analysis1['metadata'].get(key, 'N/A')
            val2 = analysis2['metadata'].get(key, 'N/A')
            comparison['metadata_diff'][key] = {
                'file1': val1,
                'file2': val2,
                'match': val1 == val2
            }
        
        # Pitch-Vergleich
        p1 = analysis1['pitch_range']
        p2 = analysis2['pitch_range']
        comparison['pitch_comparison'] = {
            'range_diff': {
                'file1': f"{p1['min']}-{p1['max']}",
                'file2': f"{p2['min']}-{p2['max']}",
                'realistic_range_file1': p1['min'] >= 0 and p1['max'] <= 40,
                'realistic_range_file2': p2['min'] >= 0 and p2['max'] <= 40
            },
            'mean_diff': abs(p1['mean'] - p2['mean'])
        }
        
        # Beat-Vergleich
        b1 = analysis1['beat_stats']
        b2 = analysis2['beat_stats']
        comparison['beat_comparison'] = {
            'range_file1': b1['total_range'],
            'range_file2': b2['total_range'],
            'timing_seems_reasonable': {
                'file1': b1['total_range'] > 100,  # Mindestens 100 Beats für ganzen Song
                'file2': b2['total_range'] > 100
            }
        }
        
        # Qualitätsbewertung
        def assess_quality(analysis):
            score = 0
            issues = []
            
            # Pitch-Bereich prüfen
            if 0 <= analysis['pitch_range']['min'] <= 40 and 0 <= analysis['pitch_range']['max'] <= 40:
                score += 25
            else:
                issues.append("Unrealistischer Pitch-Bereich")
            
            # BPM prüfen
            bpm = analysis['metadata'].get('BPM', '0')
            try:
                bpm_val = float(bpm)
                if 60 <= bpm_val <= 250:
                    score += 25
                else:
                    issues.append(f"Unplausibles BPM: {bpm}")
            except:
                issues.append("Ungültiges BPM")
            
            # Note-Anzahl prüfen
            if analysis['total_notes'] > 50:
                score += 25
            else:
                issues.append("Sehr wenige Noten")
            
            # Lyrics prüfen
            if analysis['lyrics_analysis']['empty_notes'] < analysis['total_notes'] * 0.5:
                score += 25
            else:
                issues.append("Viele leere Lyrics")
            
            return score, issues
        
        score1, issues1 = assess_quality(analysis1)
        score2, issues2 = assess_quality(analysis2)
        
        comparison['quality_assessment'] = {
            'file1_score': score1,
            'file1_issues': issues1,
            'file2_score': score2,
            'file2_issues': issues2,
            'better_file': analysis1['file'] if score1 > score2 else analysis2['file']
        }
        
        return comparison
    
    def visualize_comparison(self, file1: str, file2: str, output_path: str = None):
        """Erstellt Visualisierung des Vergleichs"""
        analysis1 = self.analyze_file(file1)
        analysis2 = self.analyze_file(file2)
        
        if 'error' in analysis1 or 'error' in analysis2:
            print("Fehler beim Laden der Dateien")
            return
        
        # Parse Noten für Visualisierung
        data1 = self.parser.parse_file(file1)
        data2 = self.parser.parse_file(file2)
        
        notes1 = [n for n in data1['notes'] if n['type'] in [':', '*', 'F']]
        notes2 = [n for n in data2['notes'] if n['type'] in [':', '*', 'F']]
        
        # Plotte Vergleich
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('UltraStar Files Comparison', fontsize=16)
        
        # Plot 1: Pitch über Zeit
        if notes1:
            beats1 = [n['beat'] for n in notes1]
            pitches1 = [n['pitch'] for n in notes1]
            ax1.scatter(beats1, pitches1, alpha=0.6, s=20, label=analysis1['file'])
        
        if notes2:
            beats2 = [n['beat'] for n in notes2]
            pitches2 = [n['pitch'] for n in notes2]
            ax1.scatter(beats2, pitches2, alpha=0.6, s=20, label=analysis2['file'])
        
        ax1.set_xlabel('Beat')
        ax1.set_ylabel('Pitch (MIDI)')
        ax1.set_title('Pitch over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Pitch-Verteilung
        if notes1:
            ax2.hist([n['pitch'] for n in notes1], bins=20, alpha=0.5, label=analysis1['file'])
        if notes2:
            ax2.hist([n['pitch'] for n in notes2], bins=20, alpha=0.5, label=analysis2['file'])
        
        ax2.set_xlabel('Pitch (MIDI)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Pitch Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Note-Dauer-Verteilung
        if notes1:
            ax3.hist([n['duration'] for n in notes1], bins=20, alpha=0.5, label=analysis1['file'])
        if notes2:
            ax3.hist([n['duration'] for n in notes2], bins=20, alpha=0.5, label=analysis2['file'])
        
        ax3.set_xlabel('Duration (Beats)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Note Duration Distribution')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Statistiken-Vergleich
        stats_labels = ['Total Notes', 'Pitch Range', 'Avg Duration']
        file1_stats = [
            analysis1['total_notes'],
            analysis1['pitch_range']['max'] - analysis1['pitch_range']['min'],
            analysis1['duration_stats']['mean']
        ]
        file2_stats = [
            analysis2['total_notes'],
            analysis2['pitch_range']['max'] - analysis2['pitch_range']['min'],
            analysis2['duration_stats']['mean']
        ]
        
        x = np.arange(len(stats_labels))
        width = 0.35
        
        ax4.bar(x - width/2, file1_stats, width, label=analysis1['file'])
        ax4.bar(x + width/2, file2_stats, width, label=analysis2['file'])
        
        ax4.set_xlabel('Statistics')
        ax4.set_ylabel('Value')
        ax4.set_title('Statistics Comparison')
        ax4.set_xticks(x)
        ax4.set_xticklabels(stats_labels)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Visualisierung gespeichert: {output_path}")
        else:
            plt.show()

def main():
    parser = argparse.ArgumentParser(description='UltraStar Debug & Comparison Tool')
    parser.add_argument('file1', help='Erste UltraStar .txt Datei')
    parser.add_argument('file2', nargs='?', help='Zweite UltraStar .txt Datei (für Vergleich)')
    parser.add_argument('--analyze', '-a', action='store_true', help='Analysiere einzelne Datei')
    parser.add_argument('--compare', '-c', action='store_true', help='Vergleiche zwei Dateien')
    parser.add_argument('--visualize', '-v', action='store_true', help='Erstelle Visualisierung')
    parser.add_argument('--output', '-o', help='Output-Pfad für Visualisierung')
    
    args = parser.parse_args()
    
    analyzer = UltraStarAnalyzer()
    
    if args.file2 and (args.compare or not args.analyze):
        # Vergleiche zwei Dateien
        print("🔍 Vergleiche UltraStar Dateien...")
        comparison = analyzer.compare_files(args.file1, args.file2)
        
        if 'error' in comparison:
            print(f"❌ Fehler: {comparison['error']}")
            return
        
        print(f"\n📊 Vergleich: {comparison['file1']} vs {comparison['file2']}")
        print("=" * 60)
        
        # Metadata
        print("\n🏷️  Metadata-Vergleich:")
        for key, diff in comparison['metadata_diff'].items():
            match_str = "✅" if diff['match'] else "❌"
            print(f"   {key}: {diff['file1']} vs {diff['file2']} {match_str}")
        
        # Pitch
        print("\n🎵 Pitch-Analyse:")
        pr = comparison['pitch_comparison']['range_diff']
        print(f"   Range: {pr['file1']} vs {pr['file2']}")
        print(f"   Realistic: {pr['realistic_range_file1']} vs {pr['realistic_range_file2']}")
        
        # Qualität
        print("\n⭐ Qualitätsbewertung:")
        qa = comparison['quality_assessment']
        print(f"   {comparison['file1']}: {qa['file1_score']}/100")
        if qa['file1_issues']:
            print(f"     Issues: {', '.join(qa['file1_issues'])}")
        print(f"   {comparison['file2']}: {qa['file2_score']}/100")
        if qa['file2_issues']:
            print(f"     Issues: {', '.join(qa['file2_issues'])}")
        print(f"   🏆 Besser: {qa['better_file']}")
        
        if args.visualize:
            analyzer.visualize_comparison(args.file1, args.file2, args.output)
    
    else:
        # Analysiere einzelne Datei
        print(f"🔍 Analysiere {args.file1}...")
        analysis = analyzer.analyze_file(args.file1)
        
        if 'error' in analysis:
            print(f"❌ Fehler: {analysis['error']}")
            return
        
        print(f"\n📊 Analyse: {analysis['file']}")
        print("=" * 40)
        
        print(f"\n📈 Grunddaten:")
        print(f"   Noten: {analysis['total_notes']}")
        print(f"   Note-Typen: {analysis['note_types']}")
        
        print(f"\n🎵 Pitch-Statistiken:")
        pr = analysis['pitch_range']
        print(f"   Bereich: {pr['min']}-{pr['max']} (Ø{pr['mean']:.1f})")
        print(f"   Realistisch: {0 <= pr['min'] <= 40 and 0 <= pr['max'] <= 40}")
        
        print(f"\n⏱️  Timing:")
        bs = analysis['beat_stats']
        print(f"   Beat-Range: {bs['min']}-{bs['max']} ({bs['total_range']} total)")
        
        print(f"\n📝 Lyrics:")
        la = analysis['lyrics_analysis']
        print(f"   Silben: {la['total_syllables']}")
        print(f"   Leere Noten: {la['empty_notes']}")

if __name__ == "__main__":
    main()