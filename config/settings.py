# config/settings.py
"""
Zentrale Konfigurationsdatei
Alle Konstanten und Einstellungen an einem Ort
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AudioSettings:
    """Audio-Verarbeitungs Einstellungen"""
    sample_rate: int = 22050
    hop_length: int = 512
    n_fft: int = 2048

    # Frequenz-Grenzen für menschliche Stimme
    voice_freq_min: float = 80.0   # ~E2
    voice_freq_max: float = 800.0  # ~G5

    # Onset Detection
    onset_delta: float = 0.05
    onset_pre_max: int = 3
    onset_post_max: int = 3


@dataclass
class UltraStarSettings:
    """UltraStar Format Einstellungen"""
    # Beat/Timing (UltraStar-BPM ist ein Vielfaches des realen Tempos,
    # offizielle Dateien enthalten Werte bis über 900)
    min_bpm: float = 10.0
    max_bpm: float = 1200.0
    preferred_bpm_min: float = 200.0
    preferred_bpm_max: float = 400.0

    # Noten (offizielle Songs enthalten viele Noten mit Dauer 1)
    min_note_duration_ms: float = 100.0
    min_note_duration_beats: int = 1

    # Pitch (offizielle Songs nutzen Werte von ca. -10 bis 72)
    min_pitch: int = -60
    max_pitch: int = 84

    # Pausen
    min_pause_beats: int = 8

    # Grid-Snapping
    default_grid_resolution: int = 4  # Viertel-Beats


@dataclass
class VocalSeparationSettings:
    """Vocal-Separation Einstellungen"""
    preferred_model: str = "htdemucs"
    use_gpu: bool = True
    chunk_size: int = 10  # Sekunden
    overlap: float = 0.25  # 25% Überlappung


@dataclass
class ApplicationSettings:
    """Allgemeine Anwendungs-Einstellungen"""
    output_directory: Path = Path("output")
    temp_directory: Path = Path("temp")
    log_directory: Path = Path("logs")

    # UI
    theme_style: str = "Light"
    primary_palette: str = "Blue"

    # Verarbeitung
    max_threads: int = 4
    enable_gpu: bool = True

    # Dateien
    max_recent_files: int = 10
    auto_save: bool = True

    def __post_init__(self):
        """Erstelle Verzeichnisse wenn nicht vorhanden"""
        self.output_directory.mkdir(exist_ok=True)
        self.temp_directory.mkdir(exist_ok=True)
        self.log_directory.mkdir(exist_ok=True)


@dataclass
class Config:
    """Haupt-Konfigurations-Klasse"""
    # default_factory statt Instanz-Defaults: veränderliche Defaults
    # sind ab Python 3.11 in dataclasses ein Fehler
    audio: AudioSettings = field(default_factory=AudioSettings)
    ultrastar: UltraStarSettings = field(default_factory=UltraStarSettings)
    vocal_separation: VocalSeparationSettings = field(default_factory=VocalSeparationSettings)
    app: ApplicationSettings = field(default_factory=ApplicationSettings)

    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Config':
        """Lädt Konfiguration aus Datei (z.B. JSON/YAML)"""
        # TODO: Implementiere Config-Laden
        return cls()

    def save_to_file(self, config_path: Path):
        """Speichert Konfiguration in Datei"""
        # TODO: Implementiere Config-Speichern
        pass


# Globale Config-Instanz
config = Config()
