"""
Écran à propos de l'application
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label, Static
from textual.screen import Screen


class AboutScreen(Screen):
    """Écran à propos"""
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("ℹ️ À propos de Locrit")
            yield Static("""
Locrit - Plateforme de Locrits Autonomes

Version: 2.0.0
Authentification: Firebase
Interface: Textual TUI
Configuration: YAML

Créé avec ❤️ pour la communauté des Locrits
            """)
            yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_btn":
            self.app.pop_screen()
