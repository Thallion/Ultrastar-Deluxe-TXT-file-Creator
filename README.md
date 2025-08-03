# UltraStar Deluxe Karaoke Generator 🎤

Ein fortschrittliches Tool zur automatischen Generierung von UltraStar Deluxe Karaoke-Dateien aus Audio und Lyrics.

## 🌟 Features

- **Automatische Vocal-Separation**: Trennt Gesang von Instrumenten
- **Fortschrittliche Pitch-Detection**: Verwendet pYIN-Algorithmus für präzise Tonhöhenerkennung
- **Intelligente Beat-Synchronisation**: Automatische BPM-Erkennung und Beat-Mapping
- **Lyrics-Synchronisation**: Automatische Zuordnung von Text zu Noten
- **GUI und CLI**: Benutzerfreundliche grafische Oberfläche oder Kommandozeile
- **Referenz-Analyse**: Lernt von existierenden UltraStar-Dateien

## 📋 Systemanforderungen

- Python 3.8+
- FFmpeg (für Audio-Verarbeitung)
- Mindestens 4GB RAM
- Windows, macOS oder Linux

## 🚀 Installation

### 1. Repository klonen
```bash
git clone https://github.com/yourusername/ultrastar-generator.git
cd ultrastar-generator
```

### 2. Virtual Environment erstellen (empfohlen)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder
venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. FFmpeg installieren

**Windows:**
- Download von https://ffmpeg.org/download.html
- Zur PATH Variable hinzufügen

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🎮 Verwendung

### GUI-Modus (empfohlen)

```bash
python start.py
# Wähle Option 1 für GUI
```

### CLI-Modus

```bash
python ultrastar_generator.py audio.mp3 --lyrics lyrics.txt --title "Song Title" --artist "Artist Name"
```

### Optionen

- `audio`: Audio-Datei (MP3, WAV, FLAC, etc.)
- `--lyrics, -l`: Lyrics-Datei (optional)
- `--title, -t`: Song-Titel (Standard: aus Dateiname)
- `--artist, -a`: Künstler (Standard: aus Dateiname)
- `--output, -o`: Output-Verzeichnis (Standard: ./output)

## 📝 Unterstützte Formate

### Audio
- MP3, WAV, FLAC, M4A, OGG
- Empfohlen: 320kbps MP3 oder verlustfrei

### Lyrics
- Plain Text (.txt)
- LRC Format (.lrc)
- Eine Zeile pro Vers

## 🎯 Tipps für beste Ergebnisse

1. **Audio-Qualität**: Verwende hochwertige Audio-Dateien (min. 256kbps)
2. **Klarer Gesang**: Songs mit deutlichem Gesang funktionieren am besten
3. **Lyrics vorbereiten**: 
   - Eine Zeile pro Vers
   - Keine Timestamps bei .txt Dateien
   - Korrekte Silbentrennung hilft
4. **Nachbearbeitung**: Verwende UltraStar Creator für Feinabstimmung

## 🔧 Erweiterte Features

### Vocal Separation mit Spleeter (optional)
```bash
pip install spleeter
# Wird automatisch verwendet wenn installiert
```

### Debug-Tool
```bash
python debug_tool.py file1.txt file2.txt --compare --visualize
```

## 📊 Technische Details

### UltraStar Format
- **BPM**: Beats per Minute (typisch 100-500)
- **GAP**: Offset in Millisekunden bis zur ersten Note
- **Pitch**: Relative Tonhöhe (typisch -10 bis +40)
- **Beats**: Zeiteinheit relativ zum GAP

### Algorithmen
- **Vocal Separation**: Harmonic-Percussive Source Separation (HPSS)
- **Pitch Detection**: pYIN (probabilistic YIN)
- **Beat Tracking**: Dynamic Programming Beat Tracker
- **Onset Detection**: Spectral Flux mit Backtracking

## 🐛 Fehlerbehebung

### Import-Fehler
```bash
pip install --upgrade librosa numpy scipy
```

### Audio-Ladefehler
```bash
pip install --upgrade soundfile
```

### GUI startet nicht
```bash
pip install --upgrade kivymd kivy
```

## 🤝 Beitragen

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## 📄 Lizenz

MIT License - siehe LICENSE Datei

## 🙏 Credits

- Librosa Team für Audio-Verarbeitung
- KivyMD Team für die GUI-Bibliothek
- UltraStar Deluxe Community

## 📞 Support

Bei Fragen oder Problemen:
- Öffne ein Issue auf GitHub
- Kontaktiere uns per E-Mail
- Besuche das UltraStar Forum

---

**Viel Spaß beim Karaoke singen! 🎤✨**