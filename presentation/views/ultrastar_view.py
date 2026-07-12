# presentation/views/ultrastar_view.py
"""
MVC View: UltraStar View
Hauptansicht der Anwendung
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.scrollview import MDScrollView

from presentation.views.widgets.file_card import FileCard
from presentation.views.widgets.log_card import LogCard
from presentation.models.ultrastar_model import ProcessingStatus


class UltraStarView(MDScreen):
    """
    View für die UltraStar Anwendung
    Zeigt UI-Komponenten und reagiert auf Model-Änderungen
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.controller = None  # Wird von außen gesetzt
        self.file_manager = None
        self._current_file_callback = None

        self._setup_ui()

    def _setup_ui(self):
        """Erstellt die komplette UI"""
        # Main Layout
        main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16)
        )

        # Title
        title = MDLabel(
            text="UltraStar Deluxe Karaoke Generator",
            theme_text_color="Primary",
            font_style="H4",
            halign="center",
            size_hint_y=None,
            height=dp(64)
        )
        main_layout.add_widget(title)

        # Scroll Container
        scroll = MDScrollView()
        content_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None
        )
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # File Cards
        self.audio_card = FileCard(
            title="Audio-Datei (MP3, WAV, etc.)",
            file_types=[".mp3", ".wav", ".flac", ".m4a", ".ogg"]
        )
        content_layout.add_widget(self.audio_card)

        self.lyrics_card = FileCard(
            title="Lyrics-Datei (optional)",
            file_types=[".txt", ".lrc"]
        )
        content_layout.add_widget(self.lyrics_card)

        # Metadata Inputs
        metadata_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(160)
        )

        self.title_field = MDTextField(
            hint_text="Song-Titel (optional)",
            helper_text="Wird aus Dateiname extrahiert falls leer",
            helper_text_mode="on_focus"
        )
        metadata_layout.add_widget(self.title_field)

        self.artist_field = MDTextField(
            hint_text="Künstler (optional)",
            helper_text="Standard: 'Unknown Artist'",
            helper_text_mode="on_focus"
        )
        metadata_layout.add_widget(self.artist_field)

        content_layout.add_widget(metadata_layout)

        # Progress
        self.progress_bar = MDProgressBar(
            value=0,
            size_hint_y=None,
            height=dp(8)
        )
        content_layout.add_widget(self.progress_bar)

        self.progress_label = MDLabel(
            text="Bereit",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(32)
        )
        content_layout.add_widget(self.progress_label)

        # Log
        self.log_card = LogCard()
        content_layout.add_widget(self.log_card)

        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)

        # Action Buttons
        button_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(16)
        )

        self.generate_button = MDRaisedButton(
            text="UltraStar Datei generieren",
            size_hint_x=0.7,
            md_bg_color=self.theme_cls.primary_color
        )
        self.generate_button.bind(on_release=self._on_generate_clicked)
        button_layout.add_widget(self.generate_button)

        reset_button = MDRaisedButton(
            text="Zurücksetzen",
            size_hint_x=0.3
        )
        reset_button.bind(on_release=self._on_reset_clicked)
        button_layout.add_widget(reset_button)

        main_layout.add_widget(button_layout)

        self.add_widget(main_layout)

        # Bind File Card Events
        self._setup_file_card_bindings()

    def _setup_file_card_bindings(self):
        """Verbindet File Card Events"""
        # Override browse button behavior
        self.audio_card.browse_button.unbind(on_release=self.audio_card._on_browse_clicked)
        self.audio_card.browse_button.bind(
            on_release=lambda x: self._open_file_manager(
                self.audio_card.file_types,
                self._on_audio_selected
            )
        )

        self.lyrics_card.browse_button.unbind(on_release=self.lyrics_card._on_browse_clicked)
        self.lyrics_card.browse_button.bind(
            on_release=lambda x: self._open_file_manager(
                self.lyrics_card.file_types,
                self._on_lyrics_selected
            )
        )

    def update(self, event: str, data=None):
        """
        Observer Pattern: Wird vom Model aufgerufen bei Änderungen
        """
        if event == 'progress_updated':
            Clock.schedule_once(lambda dt: self._update_progress(data))
        elif event == 'log_added':
            Clock.schedule_once(lambda dt: self.log_card.add_log(data))
        elif event == 'song_generated':
            Clock.schedule_once(lambda dt: self._on_song_generated(data))
        elif event == 'model_reset':
            Clock.schedule_once(lambda dt: self._reset_ui())

    def _update_progress(self, progress):
        """Aktualisiert Progress-Anzeige"""
        self.progress_bar.value = progress.progress * 100
        self.progress_label.text = progress.message

        # Update Button State
        if progress.status in [ProcessingStatus.COMPLETED, ProcessingStatus.ERROR, ProcessingStatus.IDLE]:
            self.generate_button.disabled = False
            self.generate_button.text = "UltraStar Datei generieren"
        else:
            self.generate_button.disabled = True
            self.generate_button.text = "Verarbeitung läuft..."

    def _on_generate_clicked(self, instance):
        """Generate Button wurde geklickt"""
        if self.controller:
            title = self.title_field.text.strip() or None
            artist = self.artist_field.text.strip() or None
            self.controller.start_generation(title, artist)

    def _on_reset_clicked(self, instance):
        """Reset Button wurde geklickt"""
        if self.controller:
            self.controller.reset()

    def _reset_ui(self):
        """Setzt die UI zurück"""
        self.audio_card.clear_file()
        self.lyrics_card.clear_file()
        self.title_field.text = ""
        self.artist_field.text = ""
        self.progress_bar.value = 0
        self.progress_label.text = "Bereit"
        self.log_card.clear_log()

    def _open_file_manager(self, file_types: list, callback):
        """Öffnet den File Manager"""
        self._current_file_callback = callback

        if not self.file_manager:
            self.file_manager = MDFileManager(
                exit_manager=self._exit_file_manager,
                select_path=self._select_file,
                ext=file_types
            )
        else:
            self.file_manager.ext = file_types

        self.file_manager.show('/')

    def _select_file(self, path: str):
        """Datei wurde ausgewählt"""
        self._exit_file_manager()
        if self._current_file_callback:
            self._current_file_callback(path)

    def _exit_file_manager(self, *args):
        """Schließt File Manager"""
        if self.file_manager:
            self.file_manager.close()

    def _on_audio_selected(self, path: str):
        """Audio-Datei wurde ausgewählt"""
        self.audio_card.set_file(path)
        if self.controller:
            self.controller.set_audio_file(path)

    def _on_lyrics_selected(self, path: str):
        """Lyrics-Datei wurde ausgewählt"""
        self.lyrics_card.set_file(path)
        if self.controller:
            self.controller.set_lyrics_file(path)

    def _on_song_generated(self, song):
        """Song wurde erfolgreich generiert"""
        dialog = MDDialog(
            title="Erfolgreich!",
            text=f"UltraStar Datei wurde erfolgreich erstellt!\n\n{song.metadata.artist} - {song.metadata.title}",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
