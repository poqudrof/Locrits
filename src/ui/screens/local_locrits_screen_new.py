"""
Écran de gestion des Locrits locaux avec synchronisation Firestore
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Static, Log
from textual.screen import Screen
from ...services.config_service import config_service
from ...services.firestore_admin_service import firestore_admin_service


class LocalLocritsScreen(Screen):
    """Écran des Locrits locaux avec synchronisation Firestore"""
    
    CSS = """
    LocalLocritsScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .local-container {
        padding: 2;
        height: auto;
        min-height: 100vh;
        layout: vertical;
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
    
    .sync-status {
        height: 6;
        border: solid $primary;
        margin: 1 0;
        padding: 1;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="local-container"):
            yield Label("🏠 Mes Locrits Locaux", classes="user-info")
            
            # Zone de statut de synchronisation Firestore
            with Container(classes="sync-status"):
                yield Log(id="sync_log", auto_scroll=True)
            
            with Container(classes="locrits-list", id="locrits_container"):
                yield Static("🔍 Chargement des Locrits locaux...", id="local_status")
            
            with Horizontal():
                yield Button("➕ Créer Nouveau", id="create_new_btn", variant="success")
                yield Button("🔄 Synchroniser Firestore", id="sync_btn", variant="warning")
                yield Button("🔙 Retour", id="back_btn", variant="primary")

    def on_mount(self):
        asyncio.create_task(self._load_local_locrits())
        asyncio.create_task(self._check_firestore_sync_status())

    def on_screen_resume(self):
        """Appelé quand on revient à cet écran"""
        asyncio.create_task(self._load_local_locrits())
    
    async def _check_firestore_sync_status(self):
        """Vérifie le statut de synchronisation Firestore et synchronise automatiquement"""
        sync_log = self.query_one("#sync_log", Log)
        sync_log.write_line("🔍 Vérification de la synchronisation avec Firestore...")
        
        try:
            # Obtenir les Locrits locaux
            local_locrits = config_service.list_locrits()
            sync_log.write_line(f"📋 {len(local_locrits)} Locrit(s) trouvé(s) en local: {', '.join(local_locrits)}")
            
            # Vérifier le statut Firestore
            status = firestore_admin_service.get_status()
            if not status["firestore_initialized"]:
                if not status["admin_sdk_available"]:
                    sync_log.write_line("❌ Firebase Admin SDK non installé")
                    sync_log.write_line("💡 Exécutez: pip install firebase-admin google-cloud-firestore")
                elif not status["service_account_found"]:
                    sync_log.write_line("⚠️ Fichier Admin SDK non trouvé dans admin/")
                    sync_log.write_line("💡 Placez votre fichier *-adminsdk-*.json dans le dossier admin/")
                else:
                    sync_log.write_line("❌ Erreur d'initialisation Firestore")
                return
            
            sync_log.write_line(f"🔥 Firestore initialisé - SDK: {status['service_account_file']}")
            
            if local_locrits:
                # Configurer l'auth pour Firestore
                app_user = getattr(self.app, 'current_user', None)
                if app_user:
                    firestore_admin_service.set_auth_info(app_user)
                    sync_log.write_line("🔄 Synchronisation automatique en cours...")
                    
                    # Synchroniser automatiquement
                    result = await firestore_admin_service.sync_all_locrits()
                    
                    if result.get("status") == "success":
                        sync_log.write_line("✅ Synchronisation terminée avec succès")
                        if result.get("uploaded"):
                            sync_log.write_line(f"📤 Uploadés vers Firestore: {', '.join(result['uploaded'])}")
                        if result.get("downloaded"):
                            sync_log.write_line(f"📥 Téléchargés depuis Firestore: {', '.join(result['downloaded'])}")
                    else:
                        sync_log.write_line(f"⚠️ Erreur: {result.get('message', 'Erreur inconnue')}")
                        
                    if result.get("errors"):
                        for error in result["errors"]:
                            sync_log.write_line(f"❌ {error}")
                else:
                    sync_log.write_line("⚠️ Authentification requise pour Firestore")
            else:
                sync_log.write_line("ℹ️  Aucun Locrit local à synchroniser")
                
        except Exception as e:
            sync_log.write_line(f"⚠️  Erreur de synchronisation: {str(e)}")
    
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
        created_at = settings.get('created_at', 'Inconnu')[:19] if settings.get('created_at') else 'Inconnu'
        model = settings.get('ollama_model', 'Non spécifié')
        public_address = settings.get('public_address', 'Aucune') 
        
        # Créer le container pour cet item
        item_container = Container(classes="locrit-item")
        
        # Informations du locrit
        info_container = Container(classes="locrit-info")
        await info_container.mount(Static(f"{status_icon} {name}"))
        await info_container.mount(Static(f"📝 {description}"))
        await info_container.mount(Static(f"📅 Créé: {created_at} | 🤖 {model} | 🌐 {public_address}"))
        
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
        from .create_locrit_screen import CreateLocritScreen
        from .chat_screen import ChatScreen
        
        button_id = event.button.id
        
        if button_id == "back_btn":
            self.app.pop_screen()
        elif button_id == "create_new_btn":
            self.app.push_screen(CreateLocritScreen())
        elif button_id == "sync_btn":
            asyncio.create_task(self._manual_firestore_sync())
        elif button_id.startswith("start_"):
            locrit_name = button_id[6:]  # Enlever "start_"
            self._start_locrit(locrit_name)
        elif button_id.startswith("stop_"):
            locrit_name = button_id[5:]  # Enlever "stop_"
            self._stop_locrit(locrit_name)
        elif button_id.startswith("chat_"):
            locrit_name = button_id[5:]  # Enlever "chat_"
            chat_screen = ChatScreen(locrit_name)
            self.app.push_screen(chat_screen)
        elif button_id.startswith("config_"):
            locrit_name = button_id[7:]  # Enlever "config_"
            self._configure_locrit(locrit_name)
        elif button_id.startswith("delete_"):
            locrit_name = button_id[7:]  # Enlever "delete_"
            self._delete_locrit(locrit_name)
    
    async def _manual_firestore_sync(self):
        """Synchronisation manuelle Firestore déclenchée par l'utilisateur"""
        sync_log = self.query_one("#sync_log", Log)
        sync_log.write_line("🔄 Synchronisation manuelle Firestore démarrée...")
        
        try:
            # Configurer l'auth pour Firestore
            app_user = getattr(self.app, 'current_user', None)
            if app_user:
                firestore_admin_service.set_auth_info(app_user)
            
            result = await firestore_admin_service.sync_all_locrits()
            
            if result.get("status") == "success":
                sync_log.write_line("✅ Synchronisation manuelle terminée avec succès")
                self.notify("✅ Synchronisation Firestore réussie")
                if result.get("uploaded"):
                    sync_log.write_line(f"📤 Uploadés: {', '.join(result['uploaded'])}")
                if result.get("downloaded"):
                    sync_log.write_line(f"📥 Téléchargés: {', '.join(result['downloaded'])}")
            else:
                sync_log.write_line(f"⚠️ Erreur: {result.get('message', 'Erreur inconnue')}")
                self.notify(f"⚠️ {result.get('message', 'Erreur de synchronisation')}")
                
            if result.get("errors"):
                for error in result["errors"]:
                    sync_log.write_line(f"❌ {error}")
                    
            # Recharger l'affichage des Locrits
            await self._load_local_locrits()
            
        except Exception as e:
            sync_log.write_line(f"❌ Erreur de synchronisation manuelle: {str(e)}")
            self.notify(f"❌ Erreur de synchronisation: {str(e)}")
    
    def _start_locrit(self, name: str):
        """Démarre un locrit"""
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
        self.notify(f"🔴 Arrêt de {name}...")
        
        # Mettre à jour la configuration
        settings = config_service.get_locrit_settings(name)
        settings['active'] = False
        config_service.update_locrit_settings(name, settings)
        config_service.save_config()
        
        # Recharger l'affichage
        asyncio.create_task(self._load_local_locrits())
    
    def _configure_locrit(self, name: str):
        """Configure un locrit"""
        from .edit_locrit_screen import EditLocritScreen
        try:
            settings = config_service.get_locrit_settings(name)
            edit_screen = EditLocritScreen(name, settings)
            self.app.push_screen(edit_screen)
        except Exception as e:
            self.notify(f"❌ Erreur lors de l'ouverture de l'édition: {str(e)}")
    
    def _delete_locrit(self, name: str):
        """Supprime un locrit"""
        success = config_service.delete_locrit(name)
        if success:
            config_service.save_config()
            self.notify(f"🗑️ {name} supprimé")
            asyncio.create_task(self._load_local_locrits())
        else:
            self.notify(f"❌ Erreur lors de la suppression de {name}")
