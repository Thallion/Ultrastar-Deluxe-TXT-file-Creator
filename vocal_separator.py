#vocal_separator.py

#!/usr/bin/env python3
"""
Vocal Separator Module für UltraStar Generator
Unterstützt verschiedene Vocal-Separation Methoden
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import numpy as np
import librosa
import warnings
warnings.filterwarnings("ignore")


class VocalSeparator:
    """
    Wrapper für verschiedene Vocal-Separation Methoden
    """
    
    def __init__(self):
        self.demucs_available = self._check_demucs()
        self.spleeter_available = self._check_spleeter()
        
    def _check_demucs(self) -> bool:
        """Prüft ob Demucs installiert ist"""
        try:
            import demucs
            return True
        except ImportError:
            return False
    
    def _check_spleeter(self) -> bool:
        """Prüft ob Spleeter installiert ist"""
        try:
            import spleeter
            return True
        except ImportError:
            return False
    
    def separate_vocals(self, audio_path: str, output_dir: str = None) -> str:
        """
        Separiert Vocals vom Audio mit der besten verfügbaren Methode
        
        Args:
            audio_path: Pfad zur Audio-Datei
            output_dir: Output-Verzeichnis (optional)
            
        Returns:
            Pfad zur Vocal-Datei
        """
        if self.demucs_available:
            print("🎵 Verwende Demucs für Vocal-Separation (beste Qualität)...")
            return self._separate_with_demucs(audio_path, output_dir)
        elif self.spleeter_available:
            print("🎵 Verwende Spleeter für Vocal-Separation...")
            return self._separate_with_spleeter(audio_path, output_dir)
        else:
            print("⚠️  Keine erweiterte Vocal-Separation verfügbar")
            print("💡 Installiere 'demucs' für beste Ergebnisse: pip install demucs")
            return audio_path
    
    def _separate_with_demucs(self, audio_path: str, output_dir: str = None) -> str:
        """
        Verwendet Demucs für Vocal-Separation
        """
        try:
            import demucs.separate
            from demucs.pretrained import get_model
            from demucs.apply import apply_model
            import torch
            
            # Temporäres Verzeichnis wenn nicht angegeben
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Demucs über Kommandozeile (stabiler)
            print("   Starte Demucs (kann beim ersten Mal länger dauern)...")
            
            cmd = [
                "python", "-m", "demucs.separate",
                "-n", "htdemucs",  # Bestes Modell
                "-o", str(output_path),
                "--two-stems", "vocals",  # Nur Vocals extrahieren
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Demucs Fehler: {result.stderr}")
                return audio_path
            
            # Finde die Vocal-Datei
            audio_name = Path(audio_path).stem
            vocal_path = output_path / "htdemucs" / audio_name / "vocals.wav"
            
            if vocal_path.exists():
                print("✅ Vocal-Separation erfolgreich!")
                return str(vocal_path)
            else:
                print("❌ Vocal-Datei nicht gefunden")
                return audio_path
                
        except Exception as e:
            print(f"❌ Demucs Fehler: {e}")
            return audio_path
    
    def _separate_with_spleeter(self, audio_path: str, output_dir: str = None) -> str:
        """
        Verwendet Spleeter für Vocal-Separation
        """
        try:
            from spleeter.separator import Separator
            
            # Temporäres Verzeichnis wenn nicht angegeben
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            # 2stems Model (vocals/accompaniment)
            separator = Separator('spleeter:2stems')
            
            # Separiere Audio
            separator.separate_to_file(audio_path, output_dir)
            
            # Finde die Vocal-Datei
            audio_name = Path(audio_path).stem
            vocal_path = Path(output_dir) / audio_name / "vocals.wav"
            
            if vocal_path.exists():
                print("✅ Vocal-Separation erfolgreich!")
                return str(vocal_path)
            else:
                print("❌ Vocal-Datei nicht gefunden")
                return audio_path
                
        except Exception as e:
            print(f"❌ Spleeter Fehler: {e}")
            return audio_path
    
    def enhance_vocals(self, audio: np.ndarray, sr: float) -> np.ndarray:
        """
        Verbessert die Vocal-Qualität nach der Separation
        """
        try:
            # Noise Gate
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
            threshold = np.percentile(rms, 30)
            mask = rms > threshold
            
            # Erweitere Maske für smoothing
            from scipy.ndimage import binary_dilation
            mask = binary_dilation(mask, iterations=4)
            
            # Wende Maske an
            mask_interp = np.interp(
                np.arange(len(audio)),
                np.linspace(0, len(audio), len(mask)),
                mask.astype(float)
            )
            
            audio_gated = audio * mask_interp
            
            # Leichter Kompressor
            threshold_db = -20
            ratio = 4
            
            # Konvertiere zu dB
            audio_db = librosa.amplitude_to_db(np.abs(audio_gated), ref=np.max)
            
            # Kompression
            mask = audio_db > threshold_db
            audio_db[mask] = threshold_db + (audio_db[mask] - threshold_db) / ratio
            
            # Zurück zu Amplitude
            audio_compressed = librosa.db_to_amplitude(audio_db) * np.sign(audio_gated)
            
            # Normalisierung
            audio_normalized = audio_compressed / (np.max(np.abs(audio_compressed)) + 1e-6) * 0.8
            
            return audio_normalized
            
        except Exception as e:
            print(f"⚠️  Vocal-Enhancement Fehler: {e}")
            return audio


# Integration in den UltraStarGenerator
def integrate_vocal_separator(generator_class):
    """
    Erweitert den UltraStarGenerator um erweiterte Vocal-Separation
    """
    class EnhancedGenerator(generator_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.vocal_separator = VocalSeparator()
        
        def separate_vocals(self, audio_path: str) -> tuple:
            """
            Überschreibt die separate_vocals Methode mit erweiterter Funktionalität
            """
            # Versuche erweiterte Separation
            separated_path = self.vocal_separator.separate_vocals(
                audio_path, 
                str(self.output_dir / "separated")
            )
            
            # Lade das Ergebnis
            if separated_path != audio_path:
                # Vocal-Datei wurde erstellt
                vocals, sr = librosa.load(separated_path, sr=self.SAMPLE_RATE)
                
                # Verbessere Vocal-Qualität
                vocals = self.vocal_separator.enhance_vocals(vocals, sr)
                
                # Lösche temporäre Dateien
                if "separated" in separated_path:
                    try:
                        shutil.rmtree(Path(separated_path).parent.parent)
                    except:
                        pass
                
                return vocals, sr
            else:
                # Fallback auf Original-Methode
                return super().separate_vocals(audio_path)
    
    return EnhancedGenerator


# Standalone Test-Funktion
def test_vocal_separation(audio_path: str):
    """
    Testet die Vocal-Separation
    """
    separator = VocalSeparator()
    
    print(f"🎵 Teste Vocal-Separation für: {audio_path}")
    print(f"   Demucs verfügbar: {separator.demucs_available}")
    print(f"   Spleeter verfügbar: {separator.spleeter_available}")
    
    output_dir = "vocal_test_output"
    result = separator.separate_vocals(audio_path, output_dir)
    
    if result != audio_path:
        print(f"✅ Erfolg! Vocals gespeichert in: {result}")
        
        # Lade und analysiere
        vocals, sr = librosa.load(result, sr=22050)
        duration = len(vocals) / sr
        
        print(f"   Dauer: {duration:.1f} Sekunden")
        print(f"   Sample Rate: {sr} Hz")
        
        # Optional: Speichere enhanced Version
        enhanced = separator.enhance_vocals(vocals, sr)
        
        import soundfile as sf
        enhanced_path = Path(output_dir) / "vocals_enhanced.wav"
        sf.write(enhanced_path, enhanced, sr)
        print(f"   Enhanced Version: {enhanced_path}")
    else:
        print("❌ Vocal-Separation fehlgeschlagen")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_vocal_separation(sys.argv[1])
    else:
        print("Verwendung: python vocal_separator.py <audio_datei>")