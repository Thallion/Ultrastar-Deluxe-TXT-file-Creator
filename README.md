# UltraStar Deluxe Karaoke Generator 🎤
## Clean Architecture Edition (v2.0)

Ein fortschrittliches Tool zur automatischen Generierung von UltraStar Deluxe Karaoke-Dateien, jetzt mit sauberer DDD/MVC Architektur.

## 🏗️ Architektur-Übersicht

Dieses Projekt folgt den Prinzipien von **Domain-Driven Design (DDD)** und **Clean Architecture**:

```
ultrastar-generator/
│
├── domain/                 # 🎯 Geschäftslogik (unabhängig von Frameworks)
│   ├── entities/          # Kerngeschäftsobjekte
│   ├── value_objects/     # Unveränderliche Wertobjekte  
│   └── services/          # Domain Services
│
├── application/           # 📋 Anwendungslogik
│   ├── services/         # Use Cases / Orchestrierung
│   └── interfaces/       # Ports (Interfaces)
│
├── infrastructure/        # 🔧 Technische Implementierungen
│   ├── audio/           # Audio-Verarbeitung (Librosa)
│   ├── vocal_separation/# Vocal-Trennung (Demucs/Spleeter)
│   └── persistence/     # Datei I/O
│
├── presentation/         # 🖥️ UI Layer (MVC)
│   ├── models/         # MVC Models (Zustand)
│   ├── views/          # MVC Views (UI)
│   └── controllers/    # MVC Controllers (Logik)
│
└── config/              # ⚙️ Konfiguration
```

### Warum Clean Architecture?

1. **Testbarkeit**: Jede Schicht kann isoliert getestet werden
2. **Flexibilität**: Einfacher Austausch von Implementierungen
3. **Wartbarkeit**: Klare Trennung der Verantwortlichkeiten
4. **Erweiterbarkeit**: Neue Features ohne Breaking Changes

## 🚀 Schnellstart

### Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/ultrastar-generator.git
cd ultrastar-generator

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Optional: Vocal Separation
pip install demucs  # Beste Qualität
# oder
pip install spleeter  # Schneller
```

### Verwendung

#### GUI-Modus
```bash
python main.py
# oder
python start.py
```

#### CLI-Modus
```bash
python main.py song.mp3 --lyrics lyrics.txt --title "Song Title" --artist "Artist"
```

### Docker
```bash
# Mit Docker Compose
docker-compose up

# Oder einzelner Container
docker build -t ultrastar-generator .
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output ultrastar-generator
```

## 📁 Projekt-Struktur im Detail

### Domain Layer (Geschäftslogik)

**Entities** - Die Kerngeschäftsobjekte:
- `Note`: Repräsentiert eine einzelne Note
- `Song`: Kompletter Song mit Metadaten
- `Lyrics`: Liedtext mit Silben

**Value Objects** - Unveränderliche Werte:
- `Pitch`: Tonhöhe mit Konvertierungen
- `Beat`: Timing-Informationen

**Domain Services** - Geschäftslogik:
- `PitchDetectionService`: Tonhöhenerkennung
- `BeatDetectionService`: Rhythmuserkennung

### Application Layer (Use Cases)

**Services** - Orchestrierung:
- `UltraStarGeneratorService`: Hauptprozess
- `SongProcessorService`: Nachbearbeitung

**Interfaces** - Ports für externe Systeme:
- `AudioProcessorInterface`
- `VocalSeparatorInterface`
- `FileRepositoryInterface`

### Infrastructure Layer (Implementierungen)

**Audio Processing**:
- `LibrosaAudioProcessor`: Konkrete Audio-Verarbeitung

**Vocal Separation**:
- `DemucsSeparator`: Hochqualitative Trennung
- `SpleeterSeparator`: Schnelle Alternative
- `BasicSeparator`: Fallback-Lösung

**Persistence**:
- `UltraStarFileRepository`: Datei I/O

### Presentation Layer (UI)

**MVC Pattern**:
- **Model**: `UltraStarModel` - Anwendungszustand
- **View**: `UltraStarView` - UI-Komponenten
- **Controller**: `UltraStarController` - Koordination

## 🧪 Testing

```bash
# Alle Tests ausführen
pytest

# Mit Coverage
pytest --cov=domain --cov=application --cov=infrastructure

# Spezifische Test-Kategorie
pytest tests/domain/
pytest tests/application/
pytest tests/infrastructure/
```

### Test-Struktur
```
tests/
├── domain/         # Unit Tests für Geschäftslogik
├── application/    # Service Tests
├── infrastructure/ # Integrationstests
└── e2e/           # End-to-End Tests
```

## 🔧 Konfiguration

Die Konfiguration erfolgt über `config/settings.py`:

```python
from config.settings import config

# Audio-Einstellungen
config.audio.sample_rate = 22050
config.audio.hop_length = 512

# UltraStar-Einstellungen
config.ultrastar.preferred_bpm_min = 200
config.ultrastar.preferred_bpm_max = 400

# Vocal Separation
config.vocal_separation.preferred_model = "htdemucs"
```

## 🎯 Dependency Injection

Das Projekt nutzt Dependency Injection für lose Kopplung:

```python
# Beispiel: Service-Erstellung
audio_processor = LibrosaAudioProcessor()
vocal_separator = VocalSeparatorFactory.create()
file_repository = UltraStarFileRepository()

generator_service = UltraStarGeneratorService(
    audio_processor=audio_processor,
    vocal_separator=vocal_separator,
    file_repository=file_repository,
    pitch_detection_service=PitchDetectionService(),
    beat_detection_service=BeatDetectionService()
)
```

## 📚 API-Dokumentation

### Domain Services

```python
# Pitch Detection
pitch_service = PitchDetectionService()
segments = pitch_service.process_pitch_data(frequencies, confidences, times)
merged = pitch_service.merge_similar_segments(segments)

# Beat Detection
beat_service = BeatDetectionService()
tempo = beat_service.estimate_tempo(onset_times)
gap = beat_service.calculate_gap(first_onset_time)
```

### Application Services

```python
# Song Generation
result = generator_service.generate_from_audio(
    audio_path="song.mp3",
    title="My Song",
    artist="Artist",
    lyrics=lyrics_object
)

if result.success:
    print(f"Created: {result.output_path}")
```

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

### Code-Standards

- **Black** für Code-Formatierung
- **Type Hints** für alle öffentlichen APIs
- **Docstrings** für alle Klassen und Methoden
- **Unit Tests** für neue Features

```bash
# Code formatieren
black .

# Type Checking
mypy .

# Linting
flake8
```

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

## 🙏 Credits

- **Librosa Team** - Audio-Verarbeitung
- **Demucs/Spleeter Teams** - Vocal Separation
- **KivyMD Team** - GUI Framework
- **UltraStar Community** - Format-Spezifikation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ultrastar-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ultrastar-generator/discussions)
- **Wiki**: [Projekt Wiki](https://github.com/yourusername/ultrastar-generator/wiki)

---

**Happy Karaoke! 🎤✨**

*Entwickelt mit ❤️ und Clean Code Prinzipien*