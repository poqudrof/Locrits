"""
Application Locrit refaite - Interface de gestion des Locrits
"""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Log, Static, Label
from textual.screen import Screen
from .services.locrit_manager import LocritManager
from .services.auth_service import AuthService
from .services.config_service import config_service
from .ui.auth_screen import AuthScreen


class HomeScreen(Screen):
    """Écran d'accueil principal après connexion"""
    
    CSS = """
    HomeScreen {
        background: $surface;
    }
    
    .main-container {
        padding: 2;
        height: 100%;
    }
    
    .header-section {
        height: 5;
        border: solid $primary;
        margin-bottom: 1;
        padding: 1;
    }
    
    .user-info {
        text-align: center;
        text-style: bold;
        color: $primary;
    }
    
    .buttons-grid {
        height: 1fr;
        layout: grid;
        grid-size: 2 3;
        grid-gutter: 1;
    }
    
    .menu-button {
        height: 8;
        border: solid $secondary;
        text-align: center;
        content-align: center middle;
    }
    
    .friends-button {
        background: $success;
    }
    
    .local-button {
        background: $warning;
    }
    
    .create-button {
        background: $accent;
    }
    
    .settings-button {
        background: $error;
    }
    """
    
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            with Container(classes="header-section"):
                yield Label(f"👤 Bienvenue {self.user_info['email']}", classes="user-info")
                yield Label("🏠 Tableau de bord Locrit", classes="user-info")
            
            with Container(classes="buttons-grid"):
                yield Button("👥 Locrits Amis\nEn ligne", id="friends_btn", classes="menu-button friends-button")
                yield Button("🏠 Mes Locrits\nLocaux", id="local_btn", classes="menu-button local-button")
                yield Button("➕ Créer\nNouveaux Locrit", id="create_btn", classes="menu-button create-button")
                yield Button("⚙️ Paramètres\nApplication", id="settings_btn", classes="menu-button settings-button")
                yield Button("🔐 Déconnexion", id="logout_btn", classes="menu-button")
                yield Button("ℹ️ À propos", id="about_btn", classes="menu-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "friends_btn":
            self.app.push_screen(FriendsScreen())
        elif event.button.id == "local_btn":
            self.app.push_screen(LocalLocritsScreen())
        elif event.button.id == "create_btn":
            self.app.push_screen(CreateLocritScreen())
        elif event.button.id == "settings_btn":
            self.app.push_screen(SettingsScreen())
        elif event.button.id == "logout_btn":
            self.app.pop_screen()  # Retour à l'écran de login
        elif event.button.id == "about_btn":
            self.app.push_screen(AboutScreen())


class FriendsScreen(Screen):
    """Écran des Locrits amis en ligne"""
    
    CSS = """
    FriendsScreen {
        background: $surface;
    }
    
    .friends-container {
        padding: 2;
        height: 100%;
    }
    
    .friends-list {
        height: 1fr;
        border: solid $success;
        padding: 1;
    }
    
    .friend-item {
        height: 3;
        border: solid $secondary;
        margin: 1 0;
        padding: 1;
    }
    
    .back-button {
        height: 3;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(classes="friends-container"):
            yield Label("👥 Locrits Amis En Ligne", classes="user-info")
            
            with Container(classes="friends-list"):
                yield Static("🔍 Recherche des amis en ligne...", id="friends_status")
                # TODO: Liste dynamique des amis
            
            yield Button("🔙 Retour", id="back_btn", classes="back-button", variant="primary")
    
    def on_mount(self):
        asyncio.create_task(self._load_friends())
    
    async def _load_friends(self):
        # TODO: Charger la liste des amis depuis Firebase
        status = self.query_one("#friends_status", Static)
        status.update("📡 Recherche en cours...")
        await asyncio.sleep(1)
        status.update("👥 Aucun ami en ligne pour le moment")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_btn":
            self.app.pop_screen()


class LocalLocritsScreen(Screen):
    """Écran des Locrits locaux"""
    
    CSS = """
    LocalLocritsScreen {
        background: $surface;
    }
    
    .local-container {
        padding: 2;
        height: 100%;
    }
    
    .locrits-list {
        height: 1fr;
        border: solid $warning;
        padding: 1;
    }
    
    .locrit-item {
        height: 4;
        border: solid $secondary;
        margin: 1 0;
        padding: 1;
        layout: horizontal;
    }
    
    .locrit-info {
        width: 1fr;
    }
    
    .locrit-actions {
        width: auto;
        layout: horizontal;
    }
    
    .no-locrits {
        text-align: center;
        color: $warning;
        margin: 2;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(classes="local-container"):
            yield Label("🏠 Mes Locrits Locaux", classes="user-info")
            
            with Container(classes="locrits-list", id="locrits_container"):
                yield Static("🔍 Chargement des Locrits locaux...", id="local_status")
            
            with Horizontal():
                yield Button("➕ Créer Nouveau", id="create_new_btn", variant="success")
                yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_mount(self):
        asyncio.create_task(self._load_local_locrits())
    
    async def _load_local_locrits(self):
        """Charge la liste des Locrits locaux depuis la configuration"""
        container = self.query_one("#locrits_container", Container)
        status = self.query_one("#local_status", Static)
        
        try:
            # Charger les locrits depuis la configuration
            locrits = config_service.list_locrits()
            
            # Nettoyer le container
            await container.remove_children()
            
            if locrits:
                # Afficher chaque locrit
                for locrit_name in locrits:
                    settings = config_service.get_locrit_settings(locrit_name)
                    await self._add_locrit_item(container, locrit_name, settings)
            else:
                # Aucun locrit trouvé
                no_locrits = Static("🏠 Aucun Locrit local trouvé.\n💡 Utilisez 'Créer Nouveau' pour en créer un.", 
                                  classes="no-locrits")
                await container.mount(no_locrits)
                
        except Exception as e:
            status.update(f"❌ Erreur lors du chargement: {str(e)}")
    
    async def _add_locrit_item(self, container: Container, name: str, settings: dict):
        """Ajoute un item de locrit au container"""
        
        # Récupérer les informations du locrit
        description = settings.get('description', 'Aucune description')
        is_active = settings.get('active', False)
        status_icon = "🟢" if is_active else "🔴"
        
        # Créer le container pour cet item
        item_container = Container(classes="locrit-item")
        
        # Informations du locrit
        info_container = Container(classes="locrit-info")
        await info_container.mount(Static(f"{status_icon} {name}"))
        await info_container.mount(Static(f"📝 {description}"))
        
        # Actions pour ce locrit
        actions_container = Container(classes="locrit-actions")
        
        if is_active:
            await actions_container.mount(Button("⏹️ Arrêter", id=f"stop_{name}", variant="error"))
            await actions_container.mount(Button("💬 Chat", id=f"chat_{name}", variant="success"))
        else:
            await actions_container.mount(Button("▶️ Démarrer", id=f"start_{name}", variant="success"))
        
        await actions_container.mount(Button("⚙️", id=f"config_{name}"))
        await actions_container.mount(Button("🗑️", id=f"delete_{name}", variant="error"))
        
        await item_container.mount(info_container)
        await item_container.mount(actions_container)
        await container.mount(item_container)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "back_btn":
            self.app.pop_screen()
        elif button_id == "create_new_btn":
            self.app.push_screen(CreateLocritScreen())
        elif button_id.startswith("start_"):
            locrit_name = button_id[6:]  # Enlever "start_"
            self._start_locrit(locrit_name)
        elif button_id.startswith("stop_"):
            locrit_name = button_id[5:]  # Enlever "stop_"
            self._stop_locrit(locrit_name)
        elif button_id.startswith("chat_"):
            locrit_name = button_id[5:]  # Enlever "chat_"
            self._chat_with_locrit(locrit_name)
        elif button_id.startswith("config_"):
            locrit_name = button_id[7:]  # Enlever "config_"
            self._configure_locrit(locrit_name)
        elif button_id.startswith("delete_"):
            locrit_name = button_id[7:]  # Enlever "delete_"
            self._delete_locrit(locrit_name)
    
    def _start_locrit(self, name: str):
        """Démarre un locrit"""
        # TODO: Implémenter le démarrage du locrit
        self.notify(f"🟢 Démarrage de {name}...")
        
        # Mettre à jour la configuration
        settings = config_service.get_locrit_settings(name)
        settings['active'] = True
        config_service.update_locrit_settings(name, settings)
        config_service.save_config()
        
        # Recharger l'affichage
        asyncio.create_task(self._load_local_locrits())
    
    def _stop_locrit(self, name: str):
        """Arrête un locrit"""
        # TODO: Implémenter l'arrêt du locrit
        self.notify(f"🔴 Arrêt de {name}...")
        
        # Mettre à jour la configuration
        settings = config_service.get_locrit_settings(name)
        settings['active'] = False
        config_service.update_locrit_settings(name, settings)
        config_service.save_config()
        
        # Recharger l'affichage
        asyncio.create_task(self._load_local_locrits())
    
    def _chat_with_locrit(self, name: str):
        """Ouvre le chat avec un locrit"""
        chat_screen = ChatScreen(name)
        self.app.push_screen(chat_screen)
    
    def _configure_locrit(self, name: str):
        """Configure un locrit"""
        # TODO: Implémenter l'écran de configuration
        self.notify(f"⚙️ Configuration de {name} (à implémenter)")
    
    def _delete_locrit(self, name: str):
        """Supprime un locrit"""
        # TODO: Ajouter une confirmation
        success = config_service.delete_locrit(name)
        if success:
            config_service.save_config()
            self.notify(f"🗑️ {name} supprimé")
            asyncio.create_task(self._load_local_locrits())
        else:
            self.notify(f"❌ Erreur lors de la suppression de {name}")


class CreateLocritScreen(Screen):
    """Écran de création de nouveau Locrit"""
    
    CSS = """
    CreateLocritScreen {
        background: $surface;
    }
    
    .create-container {
        padding: 2;
        height: 100%;
    }
    
    .form-section {
        height: auto;
        border: solid $accent;
        padding: 2;
        margin: 1 0;
    }
    
    .form-input {
        margin: 1 0;
    }
    
    .settings-section {
        height: auto;
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }
    
    .checkbox-group {
        layout: horizontal;
        height: 3;
    }
    
    .actions {
        height: 3;
        layout: horizontal;
        margin-top: 1;
    }
    
    .error-message {
        color: $error;
        text-style: bold;
        margin: 1 0;
    }
    
    .success-message {
        color: $success;
        text-style: bold;
        margin: 1 0;
    }
    """
    
    def __init__(self):
        super().__init__()
        # État des paramètres
        self.open_settings = {
            'humans': True,
            'locrits': True,
            'invitations': True,
            'internet': False,
            'platform': False
        }
        self.access_settings = {
            'logs': True,
            'quick': True,
            'full': False,
            'llm': True
        }
    
    def compose(self) -> ComposeResult:
        with Container(classes="create-container"):
            yield Label("➕ Créer un Nouveau Locrit", classes="user-info")
            
            with Container(classes="form-section"):
                yield Label("📝 Informations de base")
                yield Input(placeholder="Nom du Locrit (ex: Pixie l'Organisateur)", id="name_input", classes="form-input")
                yield Input(placeholder="Description courte", id="description_input", classes="form-input")
                yield Input(placeholder="Adresse publique (ex: pixie.mondomaine.com)", id="address_input", classes="form-input")
            
            with Container(classes="settings-section"):
                yield Label("🔓 Paramètres d'accès - Ouvert à :")
                yield Button("👥 Humains", id="open_humans", variant="success")
                yield Button("🤖 Autres Locrits", id="open_locrits", variant="success")
                yield Button("📧 Invitations", id="open_invitations", variant="success")
                yield Button("🌐 Internet public", id="open_internet")
                yield Button("🏢 Plateforme publique", id="open_platform")
            
            with Container(classes="settings-section"):
                yield Label("🔍 Accès autorisé à :")
                yield Button("📋 Logs", id="access_logs", variant="success")
                yield Button("🧠 Mémoire rapide", id="access_quick", variant="success")
                yield Button("🗂️ Mémoire complète", id="access_full")
                yield Button("🤖 Infos LLM", id="access_llm", variant="success")
            
            # Zone de messages
            yield Static("", id="message_display")
            
            with Container(classes="actions"):
                yield Button("✅ Créer Locrit", id="create_btn", variant="success")
                yield Button("🔙 Annuler", id="cancel_btn", variant="error")
    
    def on_mount(self):
        """Initialiser l'état des boutons selon les paramètres par défaut"""
        defaults = config_service.get_locrits_default_settings()
        
        # Mettre à jour les paramètres depuis les défauts
        self.open_settings.update(defaults.get('open_to', {}))
        self.access_settings.update(defaults.get('access_to', {}))
        
        # Mettre à jour l'affichage des boutons
        self._update_button_states()
    
    def _update_button_states(self):
        """Met à jour l'état visuel des boutons selon les paramètres"""
        # Boutons d'ouverture
        for setting, enabled in self.open_settings.items():
            button_id = f"open_{setting}"
            try:
                button = self.query_one(f"#{button_id}", Button)
                button.variant = "success" if enabled else "default"
            except:
                pass
        
        # Boutons d'accès
        access_mapping = {
            'logs': 'access_logs',
            'quick': 'access_quick', 
            'full': 'access_full',
            'llm': 'access_llm'
        }
        
        for setting, button_id in access_mapping.items():
            enabled = self.access_settings.get(setting, False)
            try:
                button = self.query_one(f"#{button_id}", Button)
                button.variant = "success" if enabled else "default"
            except:
                pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        # Gestion des boutons toggle pour l'ouverture
        if button_id.startswith("open_"):
            setting = button_id[5:]  # Enlever "open_"
            if setting in self.open_settings:
                self.open_settings[setting] = not self.open_settings[setting]
                self._update_button_states()
        
        # Gestion des boutons toggle pour l'accès
        elif button_id.startswith("access_"):
            setting_map = {
                'access_logs': 'logs',
                'access_quick': 'quick',
                'access_full': 'full',
                'access_llm': 'llm'
            }
            setting = setting_map.get(button_id)
            if setting:
                self.access_settings[setting] = not self.access_settings[setting]
                self._update_button_states()
        
        elif button_id == "create_btn":
            self._create_locrit()
        elif button_id == "cancel_btn":
            self.app.pop_screen()
    
    def _create_locrit(self):
        """Crée un nouveau Locrit avec les paramètres définis"""
        # Récupérer les valeurs des champs
        name = self.query_one("#name_input", Input).value.strip()
        description = self.query_one("#description_input", Input).value.strip()
        address = self.query_one("#address_input", Input).value.strip()
        
        message_display = self.query_one("#message_display", Static)
        
        # Validation
        if not name:
            message_display.update("❌ Le nom du Locrit est obligatoire")
            message_display.add_class("error-message")
            return
        
        # Vérifier si le nom existe déjà
        existing_locrits = config_service.list_locrits()
        if name in existing_locrits:
            message_display.update(f"❌ Un Locrit nommé '{name}' existe déjà")
            message_display.add_class("error-message")
            return
        
        # Créer la configuration du Locrit
        locrit_config = {
            'name': name,
            'description': description or f"Locrit {name}",
            'public_address': address,
            'created_at': self._get_current_timestamp(),
            'active': False,
            'open_to': self.open_settings.copy(),
            'access_to': self.access_settings.copy(),
            # Configuration par défaut
            'ollama_model': config_service.get('ollama.default_model', 'llama3.2'),
            'memory_enabled': True,
            'search_enabled': True
        }
        
        try:
            # Sauvegarder dans la configuration
            config_service.update_locrit_settings(name, locrit_config)
            success = config_service.save_config()
            
            if success:
                message_display.update(f"✅ Locrit '{name}' créé avec succès!")
                message_display.remove_class("error-message")
                message_display.add_class("success-message")
                
                # Attendre un peu puis retourner à l'écran précédent
                asyncio.create_task(self._success_and_return())
            else:
                message_display.update("❌ Erreur lors de la sauvegarde")
                message_display.add_class("error-message")
                
        except Exception as e:
            message_display.update(f"❌ Erreur: {str(e)}")
            message_display.add_class("error-message")
    
    async def _success_and_return(self):
        """Attend puis retourne à l'écran précédent"""
        await asyncio.sleep(2)
        self.app.pop_screen()
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO"""
        from datetime import datetime
        return datetime.now().isoformat()


class SettingsScreen(Screen):
    """Écran des paramètres de l'application"""
    
    CSS = """
    SettingsScreen {
        background: $surface;
    }
    
    .settings-container {
        padding: 2;
        height: 100%;
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


class ChatScreen(Screen):
    """Écran de chat avec un Locrit"""
    
    CSS = """
    ChatScreen {
        background: $surface;
    }
    
    .chat-container {
        padding: 2;
        height: 100%;
    }
    
    .chat-header {
        height: 3;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    .chat-messages {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
    }
    
    .chat-input-section {
        height: 4;
        border: solid $accent;
        padding: 1;
    }
    
    .input-with-send {
        layout: horizontal;
        height: 3;
    }
    
    .input-with-send Input {
        width: 1fr;
        margin-right: 1;
    }
    
    .message-item {
        margin: 1 0;
        padding: 1;
    }
    
    .user-message {
        background: $primary;
        color: $surface;
    }
    
    .locrit-message {
        background: $secondary;
        color: $text;
    }
    """
    
    def __init__(self, locrit_name: str):
        super().__init__()
        self.locrit_name = locrit_name
        self.conversation_history = []
    
    def compose(self) -> ComposeResult:
        with Container(classes="chat-container"):
            with Container(classes="chat-header"):
                yield Label(f"💬 Chat avec {self.locrit_name}")
                yield Label("🟢 En ligne" if self._is_locrit_active() else "🔴 Hors ligne")
            
            with Container(classes="chat-messages", id="messages_container"):
                yield Static("🤖 Conversation démarrée. Tapez votre message ci-dessous.", id="initial_message")
            
            with Container(classes="chat-input-section"):
                yield Label("📝 Votre message :")
                with Container(classes="input-with-send"):
                    yield Input(placeholder="Tapez votre message...", id="message_input")
                    yield Button("📤 Envoyer", id="send_btn", variant="primary")
                
                with Horizontal():
                    yield Button("🔄 Effacer", id="clear_btn")
                    yield Button("💾 Sauvegarder", id="save_btn")
                    yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_mount(self):
        """Focus sur le champ de message au démarrage"""
        self.query_one("#message_input", Input).focus()
    
    def _is_locrit_active(self) -> bool:
        """Vérifie si le Locrit est actif"""
        settings = config_service.get_locrit_settings(self.locrit_name)
        return settings.get('active', False)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "send_btn":
            self._send_message()
        elif button_id == "clear_btn":
            self._clear_conversation()
        elif button_id == "save_btn":
            self._save_conversation()
        elif button_id == "back_btn":
            self.app.pop_screen()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Envoyer le message quand on appuie sur Entrée"""
        if event.input.id == "message_input":
            self._send_message()
    
    def _send_message(self):
        """Envoie un message au Locrit"""
        message_input = self.query_one("#message_input", Input)
        message = message_input.value.strip()
        
        if not message:
            self.notify("❌ Veuillez taper un message")
            return
        
        # Vérifier si le Locrit est actif
        if not self._is_locrit_active():
            self.notify("❌ Locrit hors ligne. Démarrez-le d'abord.")
            return
        
        # Ajouter le message utilisateur
        self._add_message("user", message)
        
        # Effacer le champ
        message_input.value = ""
        
        # Simuler la réponse du Locrit
        asyncio.create_task(self._get_locrit_response(message))
    
    def _add_message(self, sender: str, content: str):
        """Ajoute un message à la conversation"""
        messages_container = self.query_one("#messages_container", Container)
        
        # Créer le widget de message
        if sender == "user":
            message_widget = Static(f"👤 Vous: {content}")
            message_widget.add_class("message-item", "user-message")
        else:
            message_widget = Static(f"🤖 {self.locrit_name}: {content}")
            message_widget.add_class("message-item", "locrit-message")
        
        # Ajouter à l'historique
        self.conversation_history.append({
            'sender': sender,
            'content': content,
            'timestamp': self._get_current_timestamp()
        })
        
        # Monter le widget (de façon asynchrone)
        asyncio.create_task(self._mount_message(messages_container, message_widget))
    
    async def _mount_message(self, container: Container, message_widget: Static):
        """Monte un message de façon asynchrone"""
        await container.mount(message_widget)
        # Faire défiler vers le bas
        container.scroll_end()
    
    async def _get_locrit_response(self, user_message: str):
        """Obtient la réponse du Locrit (simulation pour l'instant)"""
        # Afficher un indicateur de frappe
        typing_indicator = Static("🤖 Frappe en cours...")
        messages_container = self.query_one("#messages_container", Container)
        await messages_container.mount(typing_indicator)
        
        # Simuler un délai de réponse
        await asyncio.sleep(1)
        
        # Supprimer l'indicateur de frappe
        typing_indicator.remove()
        
        # TODO: Intégrer avec le vrai système Ollama/LocritManager
        # Pour l'instant, simuler une réponse
        if "bonjour" in user_message.lower():
            response = f"Bonjour ! Je suis {self.locrit_name}, comment puis-je vous aider ?"
        elif "comment" in user_message.lower():
            response = "Je vais bien, merci ! Je suis prêt à vous aider avec vos questions."
        elif "aide" in user_message.lower():
            response = "Je peux vous aider avec diverses tâches : recherche, analyse, conversation... Que voulez-vous faire ?"
        else:
            response = f"J'ai bien reçu votre message : '{user_message}'. Je traite cela... (Système Ollama à connecter)"
        
        # Ajouter la réponse
        self._add_message("locrit", response)
    
    def _clear_conversation(self):
        """Efface la conversation"""
        self.conversation_history.clear()
        messages_container = self.query_one("#messages_container", Container)
        
        asyncio.create_task(self._clear_messages_async(messages_container))
    
    async def _clear_messages_async(self, container: Container):
        """Efface les messages de façon asynchrone"""
        await container.remove_children()
        initial_message = Static("🤖 Conversation effacée. Nouvelle conversation démarrée.", id="initial_message")
        await container.mount(initial_message)
        self.notify("🗑️ Conversation effacée")
    
    def _save_conversation(self):
        """Sauvegarde la conversation"""
        if not self.conversation_history:
            self.notify("❌ Aucune conversation à sauvegarder")
            return
        
        # TODO: Sauvegarder dans la mémoire du Locrit
        self.notify(f"💾 Conversation sauvegardée ({len(self.conversation_history)} messages)")
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()


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

Créé avec ❤️ pour la communauté des Locrits
            """)
            yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_btn":
            self.app.pop_screen()
    """Écran à propos"""
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("ℹ️ À propos de Locrit")
            yield Static("""
Locrit - Plateforme de Locrits Autonomes

Version: 2.0.0
Authentification: Firebase
Interface: Textual TUI

Créé avec ❤️ pour la communauté des Locrits
            """)
            yield Button("🔙 Retour", id="back_btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_btn":
            self.app.pop_screen()


class LocritApp(App):
    """Application Locrit principale refaite"""
    
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
    
    .back-button {
        height: 3;
        margin-top: 1;
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
        import os
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
        
        # Afficher l'écran d'accueil
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

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Log, Static
from .services.locrit_manager import LocritManager
from .services.auth_service import AuthService
from .ui.auth_screen import AuthScreen


class LocritApp(App):
    """Application TUI principale utilisant Textual."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .container {
        height: 100%;
        padding: 1;
    }
    
    .input-section {
        height: 3;
        margin: 1 0;
    }
    
    .button-section {
        height: 3;
        margin: 1 0;
    }
    
    .log-section {
        height: 1fr;
        border: solid white;
    }
    
    Input {
        margin: 0 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    Log {
        height: 100%;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("d", "toggle_dark", "Mode sombre"),
        ("q", "quit", "Quitter"),
    ]

    def compose(self) -> ComposeResult:
        """Interface utilisateur de l'application."""
        yield Header()
        
        with Container(classes="container"):
            yield Static("🔍 Locrit - Recherche et analyse intelligente", id="title")
            
            with Vertical(classes="input-section"):
                yield Input(placeholder="Entrez votre requête de recherche...", id="search_input")
            
            with Horizontal(classes="button-section"):
                yield Button("🔍 Rechercher", id="search_btn", variant="primary")
                yield Button("🤖 Chat", id="chat_btn")
                yield Button("💾 Statut", id="status_btn")
                yield Button("🧠 Mémoire", id="memory_btn")
            
            with Horizontal(classes="button-section"):
                yield Button("🌐 Serveur", id="server_btn")
                yield Button("🚇 Tunnel", id="tunnel_btn")
                yield Button("🔗 Connecter", id="connect_btn")
                yield Button("📡 Locrits", id="locrits_btn")
                yield Button("🌍 Découvrir", id="discover_btn")
                yield Button("� Auth", id="auth_btn")
            
            with Horizontal(classes="button-section"):
                yield Button("�🗑️ Effacer", id="clear_btn")
            
            with Container(classes="log-section"):
                yield Log(id="results_log")
        
        yield Footer()

    def __init__(self):
        """Initialise l'application Locrit."""
        super().__init__()
        self.locrit = LocritManager()
        self.auth_service = AuthService()
        self.is_locrit_ready = False
        self.current_user = None

    def on_mount(self) -> None:
        """Actions à effectuer au démarrage de l'application."""
        log = self.query_one("#results_log", Log)
        log.write_line("🚀 Démarrage de Locrit...")
        
        # Vérifier si l'authentification automatique est activée
        import os
        auto_auth = os.getenv("LOCRIT_AUTO_AUTH", "false").lower() == "true"
        
        if auto_auth:
            log.write_line("🔓 Authentification automatique activée...")
            asyncio.create_task(self._auto_authenticate())
        else:
            log.write_line("🔐 Ouverture de l'écran d'authentification...")
            self._show_auth_screen()
        
        # Focus sur le champ de saisie
        self.query_one("#search_input", Input).focus()
    
    def _show_auth_screen(self):
        """Affiche l'écran d'authentification"""
        auth_screen = AuthScreen(self.auth_service)
        self.push_screen(auth_screen)
    
    async def _auto_authenticate(self):
        """Authentification automatique anonyme"""
        log = self.query_one("#results_log", Log)
        
        try:
            result = self.auth_service.sign_in_anonymous()
            
            if result["success"]:
                log.write_line("✅ Connexion anonyme automatique réussie")
                await self._on_auth_success_async(result)
            else:
                log.write_line(f"❌ Échec connexion auto: {result['error']}")
                log.write_line("🔐 Ouverture de l'écran d'authentification...")
                self._show_auth_screen()
        except Exception as e:
            log.write_line(f"❌ Erreur authentification auto: {e}")
            self._show_auth_screen()
    
    async def _on_auth_success_async(self, auth_result: dict):
        """Appelé quand l'authentification réussit"""
        log = self.query_one("#results_log", Log)
        self.current_user = auth_result
        
        # Mettre à jour l'affichage utilisateur
        user_info = f"👤 Connecté: {auth_result['email']} ({auth_result['auth_type']})"
        title = self.query_one("#title", Static)
        title.update(f"🔍 Locrit - {user_info}")
        
        log.write_line(f"✅ {user_info}")
        log.write_line("⚙️ Initialisation des services...")
        
        # Passer les informations d'auth au LocritManager
        self.locrit.set_auth_info(auth_result)
        
        # Initialiser Locrit de manière asynchrone
        await self._initialize_locrit()
    
    def _on_auth_success(self, auth_result: dict):
        """Méthode appelée par AuthScreen lors de la réussite de l'auth"""
        asyncio.create_task(self._on_auth_success_async(auth_result))

    async def _initialize_locrit(self) -> None:
        """Initialise les services Locrit de manière asynchrone."""
        log = self.query_one("#results_log", Log)
        
        try:
            # Initialiser les services
            initialization_results = await self.locrit.initialize()
            
            # Vérifier que l'initialisation s'est bien passée
            if initialization_results["overall"]:
                log.write_line("✅ Locrit prêt!")
                log.write_line("💡 Tapez votre requête et cliquez sur un bouton.")
                self.is_locrit_ready = True
                
                # Démarrer une nouvelle session
                session_id = self.locrit.start_new_session()
                log.write_line(f"📝 Session démarrée : {session_id}")
            else:
                log.write_line("⚠️ Certains services ne sont pas disponibles.")
                log.write_line("�� Vérifiez qu'Ollama est démarré sur localhost:11434")
                
        except Exception as e:
            log.write_line(f"❌ Erreur lors de l'initialisation : {str(e)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestionnaire des clics sur les boutons."""
        log = self.query_one("#results_log", Log)
        search_input = self.query_one("#search_input", Input)
        
        if not self.is_locrit_ready and event.button.id not in ["clear_btn", "status_btn"]:
            log.write_line("⚠️ Locrit n'est pas encore prêt. Patientez...")
            return

        if event.button.id == "search_btn":
            query = search_input.value.strip()
            if query:
                log.write_line(f"🔍 Recherche en cours : {query}")
                asyncio.create_task(self._handle_search(query))
            else:
                log.write_line("❌ Veuillez entrer une requête de recherche")
        
        elif event.button.id == "chat_btn":
            query = search_input.value.strip()
            if query:
                log.write_line(f"🤖 Chat : {query}")
                asyncio.create_task(self._handle_chat(query))
            else:
                log.write_line("❌ Veuillez entrer un message")
        
        elif event.button.id == "status_btn":
            log.write_line("📊 Vérification du statut...")
            asyncio.create_task(self._handle_status())
        
        elif event.button.id == "memory_btn":
            query = search_input.value.strip()
            if query:
                log.write_line(f"🧠 Recherche en mémoire : {query}")
                asyncio.create_task(self._handle_memory_search(query))
            else:
                log.write_line("❌ Veuillez entrer un terme à rechercher en mémoire")
        
        elif event.button.id == "server_btn":
            log.write_line("🌐 Basculement du mode serveur...")
            asyncio.create_task(self._handle_server_toggle())
        
        elif event.button.id == "tunnel_btn":
            log.write_line("🚇 Gestion du tunnel...")
            asyncio.create_task(self._handle_tunnel_toggle())
        
        elif event.button.id == "connect_btn":
            query = search_input.value.strip()
            if query:
                log.write_line(f"🔗 Connexion au locrit : {query}")
                asyncio.create_task(self._handle_connect_locrit(query))
            else:
                log.write_line("❌ Veuillez entrer l'URL du locrit (ex: http://autre-locrit:8000)")
        
        elif event.button.id == "locrits_btn":
            log.write_line("📡 Liste des locrits connus...")
            asyncio.create_task(self._handle_list_locrits())
        
        elif event.button.id == "discover_btn":
            query = search_input.value.strip()
            log.write_line("🌍 Découverte via serveur central...")
            asyncio.create_task(self._handle_discover_locrits(query or None))
        
        elif event.button.id == "clear_btn":
            log.clear()
            search_input.value = ""
            log.write_line("🗑️ Journal effacé")
        
        elif event.button.id == "auth_btn":
            self._handle_auth_management()

    async def _handle_search(self, query: str) -> None:
        """Gère une recherche web."""
        log = self.query_one("#results_log", Log)
        try:
            result = await self.locrit.search_and_analyze(query, "web")
            log.write_line(result)
        except Exception as e:
            log.write_line(f"❌ Erreur lors de la recherche : {str(e)}")

    async def _handle_chat(self, message: str) -> None:
        """Gère un message de chat."""
        log = self.query_one("#results_log", Log)
        search_input = self.query_one("#search_input", Input)
        
        try:
            # Vérifier si l'utilisateur veut parler à un locrit distant
            # Format: "URL::message" ou juste le message pour le locrit local
            if "::" in message:
                url, actual_message = message.split("::", 1)
                log.write_line(f"📡 Envoi à {url}: {actual_message}")
                
                result = await self.locrit.chat_with_locrit(url.strip(), actual_message.strip())
                if result['success']:
                    log.write_line(f"🤖 Réponse de {result['remote_url']}: {result['response']}")
                else:
                    log.write_line(f"❌ {result['message']}")
            else:
                # Chat local normal
                response = await self.locrit.chat(message)
                log.write_line(f"🤖 {response}")
                
            # Effacer le champ après envoi
            search_input.value = ""
            
        except Exception as e:
            log.write_line(f"❌ Erreur lors du chat : {str(e)}")

    async def _handle_status(self) -> None:
        """Affiche le statut du système."""
        log = self.query_one("#results_log", Log)
        try:
            status = await self.locrit.get_status()
            
            log.write_line("📊 Statut du système :")
            log.write_line(f"🤖 Ollama : {'✅' if status['ollama']['connected'] else '❌'} ({status['ollama']['model']})")
            log.write_line(f"🧠 Mémoire : {status['memory']['messages']} messages, {status['memory']['sessions']} sessions")
            log.write_line(f"🔍 Recherche : ✅ {status['search']['provider']}")
            log.write_line(f"🌐 Serveur : {'✅' if status.get('server_mode', False) else '❌'}")
            if status.get('api', {}).get('running', False):
                log.write_line(f"🌐 API : Port {status['api']['port']}")
            if status.get('tunneling', {}).get('active', False):
                log.write_line(f"🚇 Tunnel : {status['tunneling']['url']}")
            log.write_line(f"📝 Session : {status['session_id']}")
            
        except Exception as e:
            log.write_line(f"❌ Erreur lors de la vérification du statut : {str(e)}")

    async def _handle_memory_search(self, query: str) -> None:
        """Gère une recherche en mémoire."""
        log = self.query_one("#results_log", Log)
        try:
            result = await self.locrit.remember(query)
            log.write_line(result)
        except Exception as e:
            log.write_line(f"❌ Erreur lors de la recherche en mémoire : {str(e)}")

    async def _handle_server_toggle(self) -> None:
        """Bascule le mode serveur."""
        log = self.query_one("#results_log", Log)
        try:
            status = await self.locrit.get_status()
            
            if status.get('server_mode', False):
                # Arrêter le serveur
                result = await self.locrit.stop_server_mode()
                if result['success']:
                    log.write_line("🛑 Serveur arrêté")
                else:
                    log.write_line(f"❌ {result['message']}")
            else:
                # Démarrer le serveur
                result = await self.locrit.start_server_mode()
                if result['success']:
                    log.write_line(f"🌐 Serveur démarré sur le port {result['port']}")
                    log.write_line("💡 Utilisez le bouton Tunnel pour l'accès distant")
                else:
                    log.write_line(f"❌ {result['message']}")
                    
        except Exception as e:
            log.write_line(f"❌ Erreur serveur : {str(e)}")

    async def _handle_tunnel_toggle(self) -> None:
        """Bascule le tunnel SSH."""
        log = self.query_one("#results_log", Log)
        try:
            status = await self.locrit.get_status()
            
            if status.get('tunneling', {}).get('active', False):
                # Fermer le tunnel
                result = await self.locrit.close_tunnel()
                if result['success']:
                    log.write_line("🚇 Tunnel fermé")
                else:
                    log.write_line(f"❌ {result['message']}")
            else:
                # Créer un tunnel
                if not status.get('server_mode', False):
                    log.write_line("⚠️ Le serveur doit être démarré avant de créer un tunnel")
                    return
                
                log.write_line("🚇 Création du tunnel en cours...")
                result = await self.locrit.create_tunnel()
                if result['success']:
                    log.write_line(f"✅ Tunnel créé : {result['url']}")
                    log.write_line("🌍 Votre Locrit est maintenant accessible publiquement!")
                else:
                    log.write_line(f"❌ {result['message']}")
                    
        except Exception as e:
            log.write_line(f"❌ Erreur tunnel : {str(e)}")
    
    async def _handle_connect_locrit(self, url: str) -> None:
        """Connecte à un autre locrit."""
        log = self.query_one("#results_log", Log)
        try:
            # Extraire le nom du locrit de l'URL si possible
            locrit_name = url.split('/')[-1] if '/' in url else f"locrit_{url.split(':')[0]}"
            
            # S'assurer que l'URL a le bon format
            if not url.startswith('http'):
                url = f"http://{url}"
            
            result = await self.locrit.connect_to_locrit(url, locrit_name)
            if result['success']:
                log.write_line(f"✅ {result['message']}")
                if 'remote_status' in result:
                    remote_id = result['remote_status'].get('identity', {})
                    log.write_line(f"🤖 Locrit distant: {remote_id.get('name', 'Inconnu')}")
            else:
                log.write_line(f"❌ {result['message']}")
                
        except Exception as e:
            log.write_line(f"❌ Erreur connexion : {str(e)}")
    
    async def _handle_list_locrits(self) -> None:
        """Liste les locrits connus."""
        log = self.query_one("#results_log", Log)
        try:
            known_locrits = await self.locrit.list_known_locrits()
            
            if not known_locrits:
                log.write_line("📡 Aucun locrit connu dans la mémoire")
                log.write_line("💡 Utilisez le bouton Connecter pour ajouter des locrits")
            else:
                log.write_line(f"📡 Locrits connus ({len(known_locrits)}) :")
                for locrit in known_locrits:
                    name = locrit.get('name', 'Inconnu')
                    url = locrit.get('url', '')
                    log.write_line(f"  🤖 {name} - {url}")
                    
                log.write_line("💡 Entrez une URL et cliquez Chat pour parler avec un locrit")
                
        except Exception as e:
            log.write_line(f"❌ Erreur liste locrits : {str(e)}")
    
    async def _handle_discover_locrits(self, search_query: str = None) -> None:
        """Découvre des locrits via le serveur central."""
        log = self.query_one("#results_log", Log)
        try:
            # D'abord s'enregistrer si pas déjà fait
            registration = await self.locrit.register_with_central_server()
            if not registration['success']:
                log.write_line(f"⚠️ Serveur central non disponible: {registration['message']}")
                log.write_line("💡 Utilisation des locrits connus en local...")
                await self._handle_list_locrits()
                return
            
            # Découvrir des locrits
            discovered = await self.locrit.discover_locrits_from_central(search_query)
            
            if not discovered:
                log.write_line("🌍 Aucun locrit découvert via le serveur central")
            else:
                log.write_line(f"🌍 Locrits découverts ({len(discovered)}) :")
                for locrit in discovered:
                    identity = locrit.get('identity', {})
                    name = identity.get('name', 'Inconnu')
                    url = locrit.get('public_url', 'URL non disponible')
                    description = identity.get('description', '')
                    log.write_line(f"  🤖 {name} - {url}")
                    if description:
                        log.write_line(f"     📝 {description}")
                
                log.write_line("💡 Utilisez le bouton Connecter avec l'URL pour vous connecter")
                
        except Exception as e:
            log.write_line(f"❌ Erreur découverte : {str(e)}")
    
    def _handle_auth_management(self):
        """Gère l'authentification - affiche infos ou permet de se reconnecter"""
        log = self.query_one("#results_log", Log)
        
        if self.current_user:
            # Utilisateur connecté - afficher infos et option de déconnexion
            user_info = self.current_user
            log.write_line("🔐 Informations d'authentification :")
            log.write_line(f"👤 Email: {user_info['email']}")
            log.write_line(f"🏷️ Type: {user_info['auth_type']}")
            log.write_line(f"🆔 ID: {user_info['user_id'][:12]}...")
            log.write_line("💡 Pour changer d'utilisateur, relancez l'application")
            
            # Option de déconnexion
            if user_info['auth_type'] != 'anonymous':
                log.write_line("🔄 Vous pouvez vous déconnecter et vous reconnecter")
                # TODO: Implémenter la déconnexion si nécessaire
        else:
            # Pas d'utilisateur connecté - ouvrir l'écran d'auth
            log.write_line("🔐 Ouverture de l'écran d'authentification...")
            self._show_auth_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Gestionnaire de soumission du champ de saisie (Entrée)."""
        if event.input.id == "search_input":
            # Déclencher le chat par défaut
            chat_btn = self.query_one("#chat_btn", Button)
            self.on_button_pressed(Button.Pressed(chat_btn))

    def action_toggle_dark(self) -> None:
        """Basculer entre mode sombre et clair."""
        self.toggle_dark()

    def action_quit(self) -> None:
        """Quitter l'application."""
        # Fermer proprement les services
        if hasattr(self, 'locrit'):
            asyncio.create_task(self.locrit.shutdown())
        self.exit()
