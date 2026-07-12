# presentation/views/widgets/file_card.py
"""
Widget: File Card
Wiederverwendbare Komponente für Datei-Auswahl
"""
from pathlib import Path
from typing import List, Callable, Optional

from kivy.metrics import dp
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton


class FileCard(MDCard):
    """
    Card-Widget für Datei-Auswahl
    """

    def __init__(self,
                 title: str,
                 file_types: List[str],
                 on_file_selected: Optional[Callable[[str], None]] = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.title = title
        self.file_types = file_types
        self.on_file_selected = on_file_selected
        self.selected_file: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Erstellt die UI-Komponenten"""
        # Card Eigenschaften
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(120)
        self.elevation = 2

        # Title Label
        self.title_label = MDLabel(
            text=self.title,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        self.add_widget(self.title_label)

        # File Path Label
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
        self.browse_button = MDRaisedButton(
            text="Durchsuchen",
            size_hint_x=0.7
        )
        self.browse_button.bind(on_release=self._on_browse_clicked)
        button_layout.add_widget(self.browse_button)

        # Clear Button
        self.clear_button = MDIconButton(
            icon="close",
            size_hint_x=0.3
        )
        self.clear_button.bind(on_release=self._on_clear_clicked)
        button_layout.add_widget(self.clear_button)

        self.add_widget(button_layout)

    def _on_browse_clicked(self, instance):
        """Browse Button wurde geklickt"""
        # Dies sollte vom Parent-Widget behandelt werden
        # das den FileManager öffnet
        pass

    def _on_clear_clicked(self, instance):
        """Clear Button wurde geklickt"""
        self.clear_file()

    def set_file(self, file_path: str):
        """Setzt die ausgewählte Datei"""
        self.selected_file = file_path
        filename = Path(file_path).name
        self.file_label.text = filename
        self.file_label.theme_text_color = "Primary"

        if self.on_file_selected:
            self.on_file_selected(file_path)

    def clear_file(self):
        """Löscht die ausgewählte Datei"""
        self.selected_file = None
        self.file_label.text = "Keine Datei ausgewählt"
        self.file_label.theme_text_color = "Hint"

    def get_file(self) -> Optional[str]:
        """Gibt die ausgewählte Datei zurück"""
        return self.selected_file
