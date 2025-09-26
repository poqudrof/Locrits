"""
Écran de création de nouveau Locrit
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label, Input, Static
from textual.screen import Screen
from ...services.config_service import config_service


class CreateLocritScreen(Screen):
    """Écran de création de nouveau Locrit"""
    
    CSS = """
    CreateLocritScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }
    
    .create-container {
        padding: 1;
        height: auto;
        layout: vertical;
        overflow-y: auto;
    }
    
    .title-section {
        height: 3;
        text-align: center;
        margin: 1 0;
        border-bottom: solid $primary;
    }
    
    .scrollable-content {
        height: auto;
        overflow-y: auto;
        max-height: 70vh;
        padding: 1;
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
            # Titre fixe en haut
            with Container(classes="title-section"):
                yield Label("➕ Créer un Nouveau Locrit", classes="user-info")
            
            # Contenu scrollable
            with Container(classes="scrollable-content"):
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
            
            # Actions fixes en bas (non-scrollables)
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
