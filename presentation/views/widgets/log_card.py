# presentation/views/widgets/log_card.py
"""
Widget: Log Card
Scrollbare Log-Anzeige für Verarbeitungsmeldungen
"""
from datetime import datetime
from typing import List

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout


class LogCard(MDCard):
    """
    Card-Widget für scrollbare Log-Ausgabe
    """
    
    def __init__(self, max_messages: int = 100, **kwargs):
        super().__init__(**kwargs)
        
        self.max_messages = max_messages
        self.messages: List[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt die UI-Komponenten"""
        # Card Eigenschaften
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(200)
        self.elevation = 2
        
        # Header
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32)
        )
        
        # Title
        self.title_label = MDLabel(
            text="Verarbeitungslog",
            theme_text_color="Primary",
            font_style="H6"
        )
        header_layout.add_widget(self.title_label)
        
        # Message Count
        self.count_label = MDLabel(
            text="0 Nachrichten",
            theme_text_color="Hint",
            halign="right"
        )
        header_layout.add_widget(self.count_label)
        
        self.add_widget(header_layout)
        
        # Scrollable Log Area
        self.scroll_view = MDScrollView(
            bar_width=dp(4),
            bar_color=self.theme_cls.primary_color,
            bar_inactive_color=self.theme_cls.disabled_hint_text_color
        )
        
        # Log Container
        self.log_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
            padding=[0, dp(4)]
        )
        self.log_container.bind(minimum_height=self.log_container.setter('height'))
        
        # Initial Message
        self._add_message_widget("Bereit für Verarbeitung...", is_hint=True)
        
        self.scroll_view.add_widget(self.log_container)
        self.add_widget(self.scroll_view)
    
    def add_log(self, message: str, log_type: str = "info"):
        """
        Fügt eine Log-Nachricht hinzu
        
        Args:
            message: Die Nachricht
            log_type: Typ der Nachricht (info, warning, error, success)
        """
        # Timestamp hinzufügen
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Zur internen Liste hinzufügen
        self.messages.append(formatted_message)
        
        # Limit überschritten?
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            self._rebuild_log()
        else:
            # Nur neue Nachricht hinzufügen
            self._add_message_widget(message, log_type=log_type, timestamp=timestamp)
        
        # Update Count
        self.count_label.text = f"{len(self.messages)} Nachrichten"
        
        # Auto-scroll nach unten
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
    
    def _add_message_widget(self, message: str, log_type: str = "info", 
                           timestamp: str = None, is_hint: bool = False):
        """Fügt ein Message-Widget zum Container hinzu"""
        # Entferne initiale Hint-Nachricht wenn erste echte Nachricht
        if not is_hint and len(self.log_container.children) == 1:
            first_child = self.log_container.children[0]
            if hasattr(first_child, 'is_hint') and first_child.is_hint:
                self.log_container.clear_widgets()
        
        # Erstelle Message Layout
        message_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8)
        )
        
        # Timestamp Label (wenn vorhanden)
        if timestamp:
            time_label = MDLabel(
                text=f"[{timestamp}]",
                theme_text_color="Hint",
                size_hint_x=None,
                width=dp(80),
                font_style="Caption"
            )
            message_layout.add_widget(time_label)
        
        # Message Label
        text_color = self._get_text_color(log_type, is_hint)
        message_label = MDLabel(
            text=message,
            theme_text_color="Custom" if not is_hint else "Hint",
            text_color=text_color if not is_hint else None,
            font_style="Body2",
            markup=True  # Erlaubt Markup für Formatierung
        )
        
        # Markiere Hint-Messages
        if is_hint:
            message_label.is_hint = True
        
        message_layout.add_widget(message_label)
        
        # Füge zum Container hinzu
        self.log_container.add_widget(message_layout)
    
    def _get_text_color(self, log_type: str, is_hint: bool):
        """Gibt die Textfarbe basierend auf Log-Typ zurück"""
        if is_hint:
            return None
        
        color_map = {
            'info': self.theme_cls.primary_color,
            'warning': [1, 0.7, 0, 1],  # Orange
            'error': self.theme_cls.error_color,
            'success': [0, 0.8, 0.2, 1]  # Grün
        }
        
        return color_map.get(log_type, self.theme_cls.primary_color)
    
    def _rebuild_log(self):
        """Baut das Log neu auf (nach Limit-Überschreitung)"""
        self.log_container.clear_widgets()
        
        for msg in self.messages:
            # Extrahiere Timestamp und Message
            if msg.startswith('[') and '] ' in msg:
                timestamp = msg[1:msg.index(']')]
                message = msg[msg.index('] ') + 2:]
                
                # Bestimme Log-Typ aus Message-Präfix
                log_type = 'info'
                if message.startswith('❌'):
                    log_type = 'error'
                elif message.startswith('⚠️'):
                    log_type = 'warning'
                elif message.startswith('✅'):
                    log_type = 'success'
                
                self._add_message_widget(message, log_type, timestamp)
    
    def _scroll_to_bottom(self):
        """Scrollt zum Ende des Logs"""
        self.scroll_view.scroll_y = 0
    
    def clear_log(self):
        """Löscht alle Log-Nachrichten"""
        self.messages.clear()
        self.log_container.clear_widgets()
        self._add_message_widget("Bereit für Verarbeitung...", is_hint=True)
        self.count_label.text = "0 Nachrichten"
    
    def get_log_text(self) -> str:
        """Gibt das komplette Log als Text zurück"""
        return '\n'.join(self.messages)
    
    def save_to_file(self, file_path: str):
        """Speichert das Log in eine Datei"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.get_log_text())