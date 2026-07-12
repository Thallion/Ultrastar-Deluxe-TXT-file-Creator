# presentation/models/ultrastar_model.py
"""
MVC Model: UltraStar Model
Hält den Zustand der Anwendung
"""
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from domain.entities.song import Song
from domain.entities.lyrics import Lyrics


class ProcessingStatus(Enum):
    """Status der Verarbeitung"""
    IDLE = "idle"
    LOADING = "loading"
    SEPARATING_VOCALS = "separating_vocals"
    DETECTING_PITCH = "detecting_pitch"
    DETECTING_BEATS = "detecting_beats"
    GENERATING_NOTES = "generating_notes"
    SAVING = "saving"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessingProgress:
    """Fortschritt der Verarbeitung"""
    status: ProcessingStatus
    progress: float  # 0.0 - 1.0
    message: str
    details: Optional[str] = None


class UltraStarModel:
    """
    Model für die UltraStar Anwendung
    Verwaltet den Zustand und benachrichtigt Observer
    """

    def __init__(self):
        # Aktueller Zustand
        self.current_song: Optional[Song] = None
        self.audio_path: Optional[str] = None
        self.lyrics_path: Optional[str] = None
        self.lyrics: Optional[Lyrics] = None
        self.processing_progress = ProcessingProgress(ProcessingStatus.IDLE, 0.0, "Bereit")

        # Observer Pattern
        self._observers = []

        # Einstellungen
        self.settings = {
            'use_vocal_separation': True,
            'preferred_separator': None,
            'output_directory': 'output',
            'auto_save': True
        }

        # Historie
        self.recent_files: List[str] = []
        self.log_messages: List[str] = []

    def add_observer(self, observer):
        """Fügt einen Observer hinzu"""
        self._observers.append(observer)

    def remove_observer(self, observer):
        """Entfernt einen Observer"""
        self._observers.remove(observer)

    def notify_observers(self, event: str, data=None):
        """Benachrichtigt alle Observer"""
        for observer in self._observers:
            observer.update(event, data)

    def set_audio_path(self, path: str):
        """Setzt den Audio-Pfad"""
        self.audio_path = path
        self.notify_observers('audio_changed', path)

    def set_lyrics_path(self, path: str):
        """Setzt den Lyrics-Pfad"""
        self.lyrics_path = path
        self.notify_observers('lyrics_changed', path)

    def update_progress(self, status: ProcessingStatus, progress: float, message: str, details: str = None):
        """Aktualisiert den Verarbeitungsfortschritt"""
        self.processing_progress = ProcessingProgress(status, progress, message, details)
        self.notify_observers('progress_updated', self.processing_progress)

    def set_current_song(self, song: Song):
        """Setzt den aktuellen Song"""
        self.current_song = song
        self.notify_observers('song_generated', song)

    def add_log_message(self, message: str):
        """Fügt eine Log-Nachricht hinzu"""
        self.log_messages.append(message)
        self.notify_observers('log_added', message)

    def add_recent_file(self, file_path: str):
        """Fügt eine Datei zur Historie hinzu"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        # Behalte nur die letzten 10
        self.recent_files = self.recent_files[:10]
        self.notify_observers('recent_files_updated', self.recent_files)

    def update_setting(self, key: str, value):
        """Aktualisiert eine Einstellung"""
        if key in self.settings:
            self.settings[key] = value
            self.notify_observers('setting_changed', {key: value})

    def reset(self):
        """Setzt das Model zurück"""
        self.current_song = None
        self.audio_path = None
        self.lyrics_path = None
        self.lyrics = None
        self.processing_progress = ProcessingProgress(ProcessingStatus.IDLE, 0.0, "Bereit")
        self.log_messages.clear()
        self.notify_observers('model_reset', None)
