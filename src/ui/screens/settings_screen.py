"""
Écran des paramètres de l'application
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label, Input, Static
from textual.screen import Screen
from ...services.config_service import config_service
from ...services.local_backup_service import local_backup_service


class SettingsScreen(Screen):
    """Écran des paramètres de l'application"""
    
    CSS = """
    SettingsScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .settings-container {
        padding: 2;
        height: auto;
        max-height: 100vh;
    }
    
    .settings-section {
        height: auto;
        border: solid $secondary;
        padding: 2;
        margin: 1 0;
    }
    
    .status-indicator {
        color: $success;
        text-style: bold;
    }
    
    .status-error {
        color: $error;
        text-style: bold;
    }
    
    .input-with-button {
        layout: horizontal;
        height: 3;
    }
    
    .input-with-button Input {
        width: 1fr;
        margin-right: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(classes="settings-container"):
            yield Label("⚙️ Paramètres de l'Application", classes="user-info")
            
            with Container(classes="settings-section"):
                yield Label("🤖 Configuration Ollama")
                
                # Charger l'URL actuelle depuis la config
                current_url = config_service.get_ollama_url()
                
                with Container(classes="input-with-button"):
                    yield Input(value=current_url, placeholder="Adresse serveur Ollama (ex: http://localhost:11434)", id="ollama_input")
                    yield Button("🔗 Tester", id="test_ollama", variant="primary")
                
                yield Button("💾 Sauvegarder URL", id="save_ollama", variant="success")
                yield Static("📡 Statut: Non testé", id="ollama_status")
            
            with Container(classes="settings-section"):
                yield Label("🚇 Configuration Tunnel")
                
                tunnel_config = config_service.get_tunnel_config()
                custom_subdomain = tunnel_config.get('custom_subdomain', '')
                
                with Container(classes="input-with-button"):
                    yield Input(value=custom_subdomain, placeholder="Sous-domaine personnalisé (optionnel)", id="tunnel_input")
                    yield Button("🌐 Activer", id="enable_tunnel", variant="primary")
                
                yield Static("🚇 Statut tunnel: Inactif", id="tunnel_status")
            
            with Container(classes="settings-section"):
                yield Label("📊 Informations & Diagnostics")
                yield Button("📋 Voir logs application", id="view_logs")
                yield Button("🔍 Diagnostics système", id="diagnostics")
                yield Button("⚠️ Voir erreurs", id="view_errors")
                yield Button("🔄 Recharger config", id="reload_config")
            
            with Container(classes="settings-section"):
                yield Label("📁 Chemins et stockage")
                memory_path = config_service.get('memory.database_path', 'data/locrit_memory.db')
                yield Static(f"🗃️ Base de données: {memory_path}")
                yield Static(f"⚙️ Fichier config: {config_service.config_path}")
                
                ui_config = config_service.get_ui_config()
                theme = ui_config.get('theme', 'dark')
                yield Static(f"🎨 Thème actuel: {theme}")
            
            yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_mount(self):
        """Initialiser l'affichage des statuts"""
        asyncio.create_task(self._update_status_indicators())
    
    async def _update_status_indicators(self):
        """Met à jour les indicateurs de statut"""
        # Statut Ollama
        await self._test_ollama_connection(show_message=False)
        
        # Statut tunnel
        tunnel_config = config_service.get_tunnel_config()
        tunnel_status = self.query_one("#tunnel_status", Static)
        if tunnel_config.get('enabled', False):
            tunnel_status.update("🟢 Tunnel: Activé")
            tunnel_status.add_class("status-indicator")
        else:
            tunnel_status.update("🔴 Tunnel: Inactif")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "back_btn":
            self.app.pop_screen()
        elif button_id == "test_ollama":
            asyncio.create_task(self._test_ollama_connection())
        elif button_id == "save_ollama":
            self._save_ollama_config()
        elif button_id == "enable_tunnel":
            asyncio.create_task(self._toggle_tunnel())
        elif button_id == "view_logs":
            self._view_logs()
        elif button_id == "diagnostics":
            self._show_diagnostics()
        elif button_id == "view_errors":
            self._view_errors()
        elif button_id == "reload_config":
            self._reload_config()
    
    def _save_ollama_config(self):
        """Sauvegarde la configuration Ollama"""
        url_input = self.query_one("#ollama_input", Input)
        new_url = url_input.value.strip()
        
        if not new_url:
            self.notify("❌ Veuillez entrer une URL")
            return
        
        # Sauvegarder dans la configuration
        config_service.set_ollama_url(new_url)
        success = config_service.save_config()
        
        if success:
            self.notify("✅ Configuration Ollama sauvegardée")
        else:
            self.notify("❌ Erreur lors de la sauvegarde")
    
    async def _test_ollama_connection(self, show_message=True):
        """Teste la connexion au serveur Ollama"""
        status_widget = self.query_one("#ollama_status", Static)
        
        if show_message:
            status_widget.update("🔄 Test en cours...")
        
        try:
            import httpx
            url = config_service.get_ollama_url()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/tags")
                
                if response.status_code == 200:
                    status_widget.update("🟢 Connexion Ollama: OK")
                    status_widget.add_class("status-indicator")
                    status_widget.remove_class("status-error")
                    if show_message:
                        self.notify("✅ Serveur Ollama accessible")
                else:
                    status_widget.update(f"🔴 Erreur HTTP: {response.status_code}")
                    status_widget.add_class("status-error")
                    if show_message:
                        self.notify(f"❌ Erreur HTTP: {response.status_code}")
                        
        except Exception as e:
            status_widget.update(f"🔴 Connexion impossible: {str(e)[:50]}")
            status_widget.add_class("status-error")
            if show_message:
                self.notify(f"❌ Erreur: {str(e)}")
    
    async def _toggle_tunnel(self):
        """Active/désactive le tunnel"""
        tunnel_status = self.query_one("#tunnel_status", Static)
        tunnel_input = self.query_one("#tunnel_input", Input)
        
        tunnel_config = config_service.get_tunnel_config()
        is_enabled = tunnel_config.get('enabled', False)
        
        if is_enabled:
            # Désactiver le tunnel
            config_service.set('network.tunnel.enabled', False)
            tunnel_status.update("🔴 Tunnel: Désactivé")
            tunnel_status.remove_class("status-indicator")
            self.notify("🔴 Tunnel désactivé")
        else:
            # Activer le tunnel
            custom_subdomain = tunnel_input.value.strip()
            config_service.set('network.tunnel.enabled', True)
            if custom_subdomain:
                config_service.set('network.tunnel.custom_subdomain', custom_subdomain)
            
            tunnel_status.update("🟢 Tunnel: Activé")
            tunnel_status.add_class("status-indicator")
            self.notify("🟢 Tunnel activé")
        
        config_service.save_config()
    
    def _view_logs(self):
        """Affiche les logs de l'application"""
        # TODO: Implémenter l'affichage des logs
        self.notify("📋 Affichage des logs (à implémenter)")
    
    def _show_diagnostics(self):
        """Affiche les diagnostics système"""
        # TODO: Implémenter les diagnostics
        self.notify("🔍 Diagnostics système (à implémenter)")
    
    def _view_errors(self):
        """Affiche les erreurs"""
        # TODO: Implémenter l'affichage des erreurs
        self.notify("⚠️ Affichage des erreurs (à implémenter)")
    
    def _reload_config(self):
        """Recharge la configuration depuis le fichier"""
        config_service.reload_config()
        self.notify("🔄 Configuration rechargée")
        
        # Mettre à jour l'affichage
        ollama_input = self.query_one("#ollama_input", Input)
        ollama_input.value = config_service.get_ollama_url()
        
        tunnel_config = config_service.get_tunnel_config()
        tunnel_input = self.query_one("#tunnel_input", Input)
        tunnel_input.value = tunnel_config.get('custom_subdomain', '')
        
        # Remettre à jour les statuts
        asyncio.create_task(self._update_status_indicators())
