#!/usr/bin/env python3
"""
UltraStar Deluxe Karaoke Generator - GUI
Moderne Benutzeroberfläche mit KivyMD
"""

import os
import threading
from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.scrollview import MDScrollView

# Import unseres UltraStar Generators
try:
    from ultrastar_generator import UltraStarGenerator
except ImportError:
    print("Bitte stelle sicher, dass ultrastar_generator.py im gleichen Verzeichnis ist!")
    exit(1)


class FileCard(MDCard):
    """Card für Datei-Auswahl"""
    
    def __init__(self, title: str, file_types: list, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.file_types = file_types
        self.callback = callback
        self.selected_file = None
        
        # Card Styling
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(120)
        self.elevation = 2
        
        # Title Label
        title_label = MDLabel(
            text=title,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        self.add_widget(title_label)
        
        # File Path Display
        self.file_label = MDLabel(
            text="Keine Datei ausgewählt",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(32)
        )
        self.add_widget(self.file_label)
        
        # Button Layout
        button_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        
        # Browse Button
        browse_btn = MDRaisedButton(
            text="Durchsuchen",
            on_release=self.open_file_manager,
            size_hint_x=0.7
        )
        button_layout.add_widget(browse_btn)
        
        # Clear Button
        clear_btn = MDIconButton(
            icon="close",
            on_release=self.clear_file,
            size_hint_x=0.3
        )
        button_layout.add_widget(clear_btn)
        
        self.add_widget(button_layout)
    
    def open_file_manager(self, instance):
        """Öffnet File Manager"""
        self.callback(self.file_types, self.on_file_selected)
    
    def on_file_selected(self, file_path: str):
        """Callback wenn Datei ausgewählt wurde"""
        self.selected_file = file_path
        filename = Path(file_path).name
        self.file_label.text = filename
        self.file_label.theme_text_color = "Primary"
    
    def clear_file(self, instance):
        """Löscht ausgewählte Datei"""
        self.selected_file = None
        self.file_label.text = "Keine Datei ausgewählt"
        self.file_label.theme_text_color = "Hint"


class LogCard(MDCard):
    """Card für Log-Ausgabe"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(200)
        self.elevation = 2
        
        # Title
        title = MDLabel(
            text="Verarbeitungslog",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        self.add_widget(title)
        
        # Scrollable Log
        scroll = MDScrollView()
        self.log_label = MDLabel(
            text="Bereit für Verarbeitung...",
            theme_text_color="Hint",
            valign="top",
            text_size=(None, None)
        )
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)
    
    def add_log(self, message: str):
        """Fügt Log-Nachricht hinzu"""
        current_text = self.log_label.text
        if current_text == "Bereit für Verarbeitung...":
            self.log_label.text = message
        else:
            self.log_label.text = current_text + "\n" + message
        
        # Auto-scroll nach unten
        self.log_label.text_size = (self.log_label.width, None)
    
    def clear_log(self):
        """Löscht Log"""
        self.log_label.text = "Bereit für Verarbeitung..."


class UltraStarGUI(MDScreen):
    """Hauptbildschirm der UltraStar Generator GUI"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.file_manager = None
        self.generator = UltraStarGenerator()
        self.processing = False
        
        self.build_ui()
    
    def build_ui(self):
        """Baut die Benutzeroberfläche auf"""
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
        
        # Scroll Container für Cards
        scroll = MDScrollView()
        cards_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None
        )
        cards_layout.bind(minimum_height=cards_layout.setter('height'))
        
        # Audio File Card
        self.audio_card = FileCard(
            title="Audio-Datei (MP3, WAV, etc.)",
            file_types=[".mp3", ".wav", ".flac", ".m4a", ".ogg"],
            callback=self.open_file_manager
        )
        cards_layout.add_widget(self.audio_card)
        
        # Lyrics File Card (Optional)
        self.lyrics_card = FileCard(
            title="Lyrics-Datei (optional)",
            file_types=[".txt", ".lrc"],
            callback=self.open_file_manager
        )
        cards_layout.add_widget(self.lyrics_card)
        
        # Reference File Card (Optional)
        self.reference_card = FileCard(
            title="Referenz UltraStar-Datei (optional)",
            file_types=[".txt"],
            callback=self.open_file_manager
        )
        cards_layout.add_widget(self.reference_card)
        
        # Metadata Card
        metadata_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(160),
            elevation=2
        )
        
        metadata_title = MDLabel(
            text="Song-Informationen",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        metadata_card.add_widget(metadata_title)
        
        # Input Fields
        self.title_field = MDTextField(
            hint_text="Song-Titel (optional)",
            helper_text="Wird aus Dateiname extrahiert falls leer",
            helper_text_mode="on_focus"
        )
        metadata_card.add_widget(self.title_field)
        
        self.artist_field = MDTextField(
            hint_text="Künstler (optional)",
            helper_text="Standard: 'Unknown Artist'",
            helper_text_mode="on_focus"
        )
        metadata_card.add_widget(self.artist_field)
        
        cards_layout.add_widget(metadata_card)
        
        # Progress Card
        progress_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(100),
            elevation=2
        )
        
        progress_title = MDLabel(
            text="Fortschritt",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        progress_card.add_widget(progress_title)
        
        self.progress_bar = MDProgressBar(
            value=0,
            size_hint_y=None,
            height=dp(8)
        )
        progress_card.add_widget(self.progress_bar)
        
        self.progress_label = MDLabel(
            text="Bereit",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(32)
        )
        progress_card.add_widget(self.progress_label)
        
        cards_layout.add_widget(progress_card)
        
        # Log Card
        self.log_card = LogCard()
        cards_layout.add_widget(self.log_card)
        
        scroll.add_widget(cards_layout)
        main_layout.add_widget(scroll)
        
        # Action Buttons
        button_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(16)
        )
        
        self.generate_btn = MDRaisedButton(
            text="UltraStar Datei generieren",
            on_release=self.start_generation,
            size_hint_x=0.7,
            md_bg_color=self.theme_cls.primary_color
        )
        button_layout.add_widget(self.generate_btn)
        
        clear_btn = MDRaisedButton(
            text="Zurücksetzen",
            on_release=self.reset_form,
            size_hint_x=0.3
        )
        button_layout.add_widget(clear_btn)
        
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)
    
    def open_file_manager(self, file_types: list, callback):
        """Öffnet File Manager"""
        if not self.file_manager:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_file_manager,
                select_path=lambda path: self.select_file(path, callback),
                ext=file_types
            )
        else:
            self.file_manager.ext = file_types
            self.file_manager.select_path = lambda path: self.select_file(path, callback)
        
        self.file_manager.show('/')
    
    def select_file(self, path: str, callback):
        """Datei wurde ausgewählt"""
        self.exit_file_manager()
        callback(path)
    
    def exit_file_manager(self, *args):
        """Schließt File Manager"""
        if self.file_manager:
            self.file_manager.close()
    
    def start_generation(self, instance):
        """Startet UltraStar Generierung in separatem Thread"""
        if self.processing:
            return
        
        # Validierung
        if not self.audio_card.selected_file:
            self.show_error("Bitte wähle eine Audio-Datei aus!")
            return
        
        if not Path(self.audio_card.selected_file).exists():
            self.show_error("Audio-Datei nicht gefunden!")
            return
        
        # UI für Processing vorbereiten
        self.processing = True
        self.generate_btn.text = "Verarbeitung läuft..."
        self.generate_btn.disabled = True
        self.progress_bar.value = 0
        self.log_card.clear_log()
        
        # Starte in separatem Thread
        thread = threading.Thread(target=self.generate_ultrastar)
        thread.daemon = True
        thread.start()
    
    def generate_ultrastar(self):
        """Generiert UltraStar Datei (läuft in separatem Thread)"""
        try:
            # Parameter sammeln
            audio_path = self.audio_card.selected_file
            lyrics_path = self.lyrics_card.selected_file
            reference_path = self.reference_card.selected_file
            title = self.title_field.text.strip() or None
            artist = self.artist_field.text.strip() or None
            
            # Progress Updates
            Clock.schedule_once(lambda dt: self.update_progress(10, "Lade Audio..."))
            
            # Custom Generator mit Progress Callbacks
            class ProgressGenerator(UltraStarGenerator):
                def __init__(self, gui, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.gui = gui
                
                def separate_vocals(self, audio_path):
                    Clock.schedule_once(lambda dt: self.gui.update_progress(20, "Separiere Vocals..."))
                    Clock.schedule_once(lambda dt: self.gui.log_message("🎤 Separiere Vocals..."))
                    return super().separate_vocals(audio_path)
                
                def estimate_bpm(self, audio, sr):
                    Clock.schedule_once(lambda dt: self.gui.update_progress(40, "Schätze BPM..."))
                    Clock.schedule_once(lambda dt: self.gui.log_message("🥁 Schätze BPM..."))
                    return super().estimate_bpm(audio, sr)
                
                def detect_pitch(self, audio, sr):
                    Clock.schedule_once(lambda dt: self.gui.update_progress(60, "Erkenne Tonhöhen..."))
                    Clock.schedule_once(lambda dt: self.gui.log_message("🎼 Erkenne Tonhöhen..."))
                    return super().detect_pitch(audio, sr)
                
                def smooth_pitch_data(self, pitch_data, min_duration=0.4):
                    Clock.schedule_once(lambda dt: self.gui.update_progress(80, "Verarbeite Noten..."))
                    Clock.schedule_once(lambda dt: self.gui.log_message("🎯 Verarbeite Noten..."))
                    return super().smooth_pitch_data(pitch_data, min_duration)
                
                def parse_lyrics(self, lyrics_path):
                    Clock.schedule_once(lambda dt: self.gui.update_progress(90, "Lade Lyrics..."))
                    Clock.schedule_once(lambda dt: self.gui.log_message("📝 Lade Lyrics..."))
                    return super().parse_lyrics(lyrics_path)
            
            # Generiere mit Progress Tracking
            generator = ProgressGenerator(self)
            result = generator.process_files(audio_path, lyrics_path, title, artist, reference_path)
            
            if result:
                Clock.schedule_once(lambda dt: self.update_progress(100, "Erfolgreich abgeschlossen!"))
                Clock.schedule_once(lambda dt: self.log_message(f"✅ UltraStar Datei erstellt: {result}"))
                Clock.schedule_once(lambda dt: self.show_success(f"UltraStar Datei erfolgreich erstellt!\n\n{result}"))
            else:
                Clock.schedule_once(lambda dt: self.show_error("Fehler bei der Generierung!"))
                Clock.schedule_once(lambda dt: self.log_message("❌ Generierung fehlgeschlagen"))
        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(f"Fehler: {str(e)}"))
            Clock.schedule_once(lambda dt: self.log_message(f"❌ Fehler: {str(e)}"))
        
        finally:
            # UI zurücksetzen
            Clock.schedule_once(lambda dt: self.reset_ui())
    
    def update_progress(self, value: int, text: str):
        """Aktualisiert Progress Bar"""
        self.progress_bar.value = value
        self.progress_label.text = text
    
    def log_message(self, message: str):
        """Fügt Log-Nachricht hinzu"""
        self.log_card.add_log(message)
    
    def reset_ui(self):
        """Setzt UI nach Processing zurück"""
        self.processing = False
        self.generate_btn.text = "UltraStar Datei generieren"
        self.generate_btn.disabled = False
    
    def reset_form(self, instance):
        """Setzt das gesamte Formular zurück"""
        self.audio_card.clear_file(None)
        self.lyrics_card.clear_file(None)
        self.reference_card.clear_file(None)
        self.title_field.text = ""
        self.artist_field.text = ""
        self.progress_bar.value = 0
        self.progress_label.text = "Bereit"
        self.log_card.clear_log()
    
    def show_error(self, message: str):
        """Zeigt Fehler-Dialog"""
        dialog = MDDialog(
            title="Fehler",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def show_success(self, message: str):
        """Zeigt Erfolg-Dialog"""
        dialog = MDDialog(
            title="Erfolgreich!",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class UltraStarApp(MDApp):
    """Hauptanwendung"""
    
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.title = "UltraStar Generator"
        
        return UltraStarGUI()


if __name__ == "__main__":
    UltraStarApp().run()