"""
Écran d'informations détaillées d'un Locrit
Page descriptive complète avec toutes les informations
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static
from textual.screen import Screen


class LocritInfoScreen(Screen):
    """Écran d'informations détaillées d'un Locrit"""
    
    CSS = """
    LocritInfoScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .info-container {
        padding: 2;
        height: auto;
        min-height: 100vh;
        layout: vertical;
    }
    
    .info-header {
        height: 4;
        border: solid $primary;
        padding: 1;
        margin-bottom: 2;
        text-align: center;
    }
    
    .info-section {
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }
    
    .info-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .info-item {
        margin: 0.5 0;
    }
    
    .status-active {
        color: $success;
        text-style: bold;
    }
    
    .status-inactive {
        color: $error;
        text-style: bold;
    }
    
    .access-grid {
        layout: horizontal;
    }
    
    .access-column {
        width: 1fr;
        margin: 0 1;
    }
    """
    
    def __init__(self, locrit_name: str, settings: dict):
        super().__init__()
        self.locrit_name = locrit_name
        self.settings = settings
    
    def compose(self) -> ComposeResult:
        is_active = self.settings.get('active', False)
        status_text = "🟢 ACTIF" if is_active else "🔴 INACTIF"
        status_class = "status-active" if is_active else "status-inactive"
        
        with Container(classes="info-container"):
            # En-tête
            with Container(classes="info-header"):
                yield Label(f"📄 Page Descriptive", classes="info-title")
                yield Label(f"{self.locrit_name}", markup=True)
                yield Label(f"[{status_class}]{status_text}[/{status_class}]", markup=True)
            
            # Informations de base
            with Container(classes="info-section"):
                yield Label("📝 Informations Générales", classes="info-title")
                yield Static(f"Nom: {self.locrit_name}", classes="info-item")
                yield Static(f"Description: {self.settings.get('description', 'Aucune description')}", classes="info-item")
                yield Static(f"Modèle Ollama: {self.settings.get('ollama_model', 'Non spécifié')}", classes="info-item")
                yield Static(f"Adresse publique: {self.settings.get('public_address', 'Aucune')}", classes="info-item")
            
            # Dates et historique
            with Container(classes="info-section"):
                yield Label("📅 Historique", classes="info-title")
                created_at = self.settings.get('created_at', 'Inconnu')[:19] if self.settings.get('created_at') else 'Inconnu'
                updated_at = self.settings.get('updated_at', 'Inconnu')[:19] if self.settings.get('updated_at') else 'Inconnu'
                yield Static(f"Date de création: {created_at}", classes="info-item")
                yield Static(f"Dernière modification: {updated_at}", classes="info-item")
            
            # Paramètres d'accès
            with Container(classes="info-section"):
                yield Label("🔐 Paramètres d'Accès", classes="info-title")
                
                with Container(classes="access-grid"):
                    # Colonne "Ouvert à"
                    with Container(classes="access-column"):
                        yield Label("Ouvert à:", classes="info-title")
                        open_to = self.settings.get('open_to', {})
                        yield Static(f"• Humains: {'✅' if open_to.get('humans', True) else '❌'}", classes="info-item")
                        yield Static(f"• Autres Locrits: {'✅' if open_to.get('locrits', True) else '❌'}", classes="info-item")
                        yield Static(f"• Invitations: {'✅' if open_to.get('invitations', True) else '❌'}", classes="info-item")
                        yield Static(f"• Internet: {'✅' if open_to.get('internet', False) else '❌'}", classes="info-item")
                        yield Static(f"• Plateforme: {'✅' if open_to.get('platform', False) else '❌'}", classes="info-item")
                    
                    # Colonne "Accès aux données"
                    with Container(classes="access-column"):
                        yield Label("Accès aux données:", classes="info-title")
                        access_to = self.settings.get('access_to', {})
                        yield Static(f"• Logs: {'✅' if access_to.get('logs', True) else '❌'}", classes="info-item")
                        yield Static(f"• Mémoire rapide: {'✅' if access_to.get('quick_memory', True) else '❌'}", classes="info-item")
                        yield Static(f"• Mémoire complète: {'✅' if access_to.get('full_memory', False) else '❌'}", classes="info-item")
                        yield Static(f"• Infos LLM: {'✅' if access_to.get('llm_info', True) else '❌'}", classes="info-item")
            
            # Statistiques (si disponibles)
            with Container(classes="info-section"):
                yield Label("📊 Statistiques", classes="info-title")
                yield Static("• Messages échangés: À implémenter", classes="info-item")
                yield Static("• Dernière conversation: À implémenter", classes="info-item")
                yield Static("• Temps de fonctionnement: À implémenter", classes="info-item")
            
            # Actions
            with Horizontal():
                if is_active:
                    yield Button("💬 Parler avec le Locrit", id="chat_btn", variant="success")
                    yield Button("⏹️ Arrêter", id="stop_btn", variant="error")
                else:
                    yield Button("▶️ Démarrer", id="start_btn", variant="success")
                
                yield Button("⚙️ Éditer", id="edit_btn", variant="primary")
                yield Button("🔙 Retour", id="back_btn", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "back_btn":
            self.app.pop_screen()
        elif button_id == "chat_btn":
            from .chat_screen import ChatScreen
            chat_screen = ChatScreen(self.locrit_name)
            self.app.push_screen(chat_screen)
        elif button_id == "edit_btn":
            from .edit_locrit_screen import EditLocritScreen
            edit_screen = EditLocritScreen(self.locrit_name, self.settings)
            self.app.push_screen(edit_screen)
        elif button_id == "start_btn":
            self._start_locrit()
        elif button_id == "stop_btn":
            self._stop_locrit()
    
    def _start_locrit(self):
        """Démarre le locrit depuis la page d'info"""
        from ...services.config_service import config_service
        
        self.settings['active'] = True
        config_service.update_locrit_settings(self.locrit_name, self.settings)
        config_service.save_config()
        
        self.notify(f"🟢 {self.locrit_name} démarré")
        self.app.pop_screen()  # Retourner à la liste pour voir le changement
    
    def _stop_locrit(self):
        """Arrête le locrit depuis la page d'info"""
        from ...services.config_service import config_service
        
        self.settings['active'] = False
        config_service.update_locrit_settings(self.locrit_name, self.settings)
        config_service.save_config()
        
        self.notify(f"🔴 {self.locrit_name} arrêté")
        self.app.pop_screen()  # Retourner à la liste pour voir le changement
