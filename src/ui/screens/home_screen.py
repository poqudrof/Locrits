"""
Écran d'accueil principal après authentification
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label
from textual.screen import Screen


class HomeScreen(Screen):
    """Écran d'accueil principal après connexion"""
    
    CSS = """
    HomeScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .main-container {
        padding: 2;
        height: auto;
        min-height: 100vh;
        layout: vertical;
    }
    
    .header-section {
        height: 6;
        border: solid $primary;
        margin-bottom: 2;
        padding: 1;
    }
    
    .user-info {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    .welcome-message {
        text-align: center;
        color: $accent;
        margin: 1 0;
    }
    
    .buttons-section {
        height: 1fr;
        margin: 2 0;
    }
    
    .buttons-row {
        height: auto;
        margin: 2 0;
        layout: horizontal;
    }
    
    .menu-button {
        width: 1fr;
        height: 8;
        margin: 0 1;
        border: solid $secondary;
        text-align: center;
        content-align: center middle;
    }
    
    .primary-button {
        background: $primary;
        color: $surface;
    }
    
    .success-button {
        background: $success;
    }
    
    .warning-button {
        background: $warning;
    }
    
    .accent-button {
        background: $accent;
    }
    
    .error-button {
        background: $error;
    }
    
    .secondary-button {
        background: $secondary;
    }
    
    .footer-actions {
        height: 4;
        layout: horizontal;
        margin-top: 2;
    }
    
    .footer-button {
        width: 1fr;
        height: 3;
        margin: 0 1;
    }
    """
    
    def __init__(self, user_info: dict):
        super().__init__()
        # Assurer que user_info est un dictionnaire valide
        if not isinstance(user_info, dict):
            print(f"⚠️ Warning: user_info n'est pas un dict: {type(user_info)}")
            self.user_info = {"email": "Utilisateur", "user_id": "unknown"}
        else:
            self.user_info = user_info
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            # En-tête avec informations utilisateur
            with Container(classes="header-section"):
                # Gestion robuste des informations utilisateur
                email = "Utilisateur"
                if isinstance(self.user_info, dict):
                    email = self.user_info.get('email', 'Utilisateur')
                
                yield Label(f"👤 Bienvenue {email}", classes="user-info")
                yield Label("🏠 Centre de Contrôle Locrit", classes="welcome-message")
                yield Label("Gérez vos Locrits intelligents depuis cette interface", classes="welcome-message")
            
            # Section principale avec boutons organisés
            with Container(classes="buttons-section"):
                # Première rangée - Gestion des Locrits
                with Container(classes="buttons-row"):
                    yield Button("🏠 Mes Locrits\nLocaux", id="local_btn", classes="menu-button success-button")
                    yield Button("👥 Locrits Amis\nEn Réseau", id="friends_btn", classes="menu-button primary-button")
                    yield Button("➕ Créer\nNouveau Locrit", id="create_btn", classes="menu-button accent-button")
                
                # Deuxième rangée - Communication et réseau
                with Container(classes="buttons-row"):
                    yield Button("💬 Chat Global\nMulti-Locrits", id="global_chat_btn", classes="menu-button warning-button")
                    yield Button("🌐 Découvrir\nRéseau Public", id="discover_btn", classes="menu-button secondary-button")
                    yield Button("🔗 Connexions\nDistantes", id="connections_btn", classes="menu-button secondary-button")
                
                # Troisième rangée - Configuration et outils
                with Container(classes="buttons-row"):
                    yield Button("⚙️ Paramètres\nApplication", id="settings_btn", classes="menu-button secondary-button")
                    yield Button("📊 Monitoring\nPerformance", id="monitoring_btn", classes="menu-button secondary-button")
                    yield Button("🛠️ Outils\nDéveloppeur", id="dev_tools_btn", classes="menu-button secondary-button")
            
            # Pied de page avec actions rapides
            with Container(classes="footer-actions"):
                yield Button("� Synchroniser", id="sync_btn", classes="footer-button primary-button")
                yield Button("🔐 Déconnexion", id="logout_btn", classes="footer-button error-button")
                yield Button("ℹ️ À propos", id="about_btn", classes="footer-button secondary-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        from .local_locrits_screen import LocalLocritsScreen
        from .friends_screen import FriendsScreen
        from .create_locrit_screen import CreateLocritScreen
        from .settings_screen import SettingsScreen
        from .about_screen import AboutScreen
        
        button_id = event.button.id
        
        if button_id == "local_btn":
            self.app.push_screen(LocalLocritsScreen())
        elif button_id == "friends_btn":
            self.app.push_screen(FriendsScreen())
        elif button_id == "create_btn":
            self.app.push_screen(CreateLocritScreen())
        elif button_id == "sync_btn":
            asyncio.create_task(self._manual_sync())
        elif button_id == "global_chat_btn":
            self.notify("💬 Chat global (à implémenter)")
        elif button_id == "discover_btn":
            self.notify("🌐 Découverte réseau (à implémenter)")
        elif button_id == "connections_btn":
            self.notify("🔗 Connexions distantes (à implémenter)")
        elif button_id == "settings_btn":
            self.app.push_screen(SettingsScreen())
        elif button_id == "monitoring_btn":
            self.notify("📊 Monitoring (à implémenter)")
        elif button_id == "dev_tools_btn":
            self.notify("🛠️ Outils développeur (à implémenter)")
        elif button_id == "logout_btn":
            # Déconnexion propre avec nettoyage de session
            self.app.logout()
            self.app.pop_screen()  # Retour à l'écran de login
        elif button_id == "about_btn":
            self.app.push_screen(AboutScreen())

    async def _manual_sync(self):
        """Synchronisation manuelle déclenchée par l'utilisateur"""
        from ...services.sync_service import sync_service
        
        self.notify("🔄 Synchronisation en cours...")
        
        try:
            result = await sync_service.sync_all_locrits()
            
            if result.get("status") == "success":
                upload_count = len(result.get("upload_results", []))
                download_count = len(result.get("download_results", []))
                self.notify(f"✅ Sync réussie: {upload_count} envoyés, {download_count} reçus")
            elif result.get("status") == "no_auth":
                self.notify("⚠️ Authentification requise pour la sync")
            elif result.get("status") == "disabled":
                self.notify("📴 Synchronisation désactivée")
            else:
                errors = result.get("errors", [])
                if errors:
                    self.notify(f"❌ Erreurs sync: {errors[0]}")
                else:
                    self.notify("❌ Erreur de synchronisation")
                    
        except Exception as e:
            self.notify(f"❌ Erreur sync: {str(e)}")
