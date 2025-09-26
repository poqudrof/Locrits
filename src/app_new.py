"""
Application Locrit refaite - Interface de gestion des Locrits
Architecture modulaire avec écrans séparés
"""

import asyncio
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .services.locrit_manager import LocritManager
from .services.auth_service import AuthService
from .services.config_service import config_service
from .ui.auth_screen import AuthScreen
from .ui.screens import HomeScreen


class LocritApp(App):
    """Application Locrit principale refaite avec architecture modulaire"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .user-info {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("d", "toggle_dark", "Mode sombre"),
        ("q", "quit", "Quitter"),
    ]

    def __init__(self):
        """Initialise l'application Locrit."""
        super().__init__()
        self.auth_service = AuthService()
        self.locrit_manager = LocritManager()
        self.current_user = None

    def compose(self) -> ComposeResult:
        """Interface vide au démarrage - l'auth screen sera pushé"""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Affiche l'écran d'authentification au démarrage"""
        auto_auth = os.getenv("LOCRIT_AUTO_AUTH", "false").lower() == "true"
        
        if auto_auth:
            asyncio.create_task(self._auto_authenticate())
        else:
            self._show_auth_screen()

    def _show_auth_screen(self):
        """Affiche l'écran d'authentification"""
        auth_screen = AuthScreen(self.auth_service)
        self.push_screen(auth_screen)

    async def _auto_authenticate(self):
        """Authentification automatique anonyme"""
        try:
            result = self.auth_service.sign_in_anonymous()
            
            if result["success"]:
                await self._on_auth_success_async(result)
            else:
                self._show_auth_screen()
        except Exception:
            self._show_auth_screen()

    async def _on_auth_success_async(self, auth_result: dict):
        """Appelé quand l'authentification réussit"""
        self.current_user = auth_result
        
        # Passer les informations d'auth au LocritManager
        self.locrit_manager.set_auth_info(auth_result)
        
        # Afficher l'écran d'accueil refait
        home_screen = HomeScreen(auth_result)
        self.push_screen(home_screen)

    def _on_auth_success(self, auth_result: dict):
        """Méthode appelée par AuthScreen lors de la réussite de l'auth"""
        asyncio.create_task(self._on_auth_success_async(auth_result))

    def action_toggle_dark(self) -> None:
        """Basculer entre mode sombre et clair."""
        self.toggle_dark()

    def action_quit(self) -> None:
        """Quitter l'application."""
        if hasattr(self, 'locrit_manager'):
            asyncio.create_task(self.locrit_manager.shutdown())
        self.exit()
