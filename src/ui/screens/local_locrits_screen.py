"""
Écran de gestion des Locrits locaux avec synchronisation Firestore
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static, Log, ListItem, ListView
from textual.screen import Screen
from ...services.config_service import config_service
from ...services.firestore_admin_service import firestore_admin_service
from ...services.ui_logging_service import ScreenLogger, ui_logging_service


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
        layout: horizontal;
    }
    
    .left-panel {
        width: 1fr;
        padding-right: 1;
    }
    
    .right-panel {
        width: 2fr;
        padding-left: 1;
        border-left: solid $primary;
    }
    
    .locrits-list {
        height: 25;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }
    
    .locrit-item {
        height: 4;
        border: solid $secondary;
        margin: 1 0;
        padding: 1;
    }
    
    .locrit-item:hover {
        background: $primary 10%;
    }
    
    .locrit-item.selected {
        background: $primary 30%;
        border: solid $primary;
    }
    
    .locrit-basic-info {
        height: 3;
    }
    
    .no-locrits {
        text-align: center;
        color: $warning;
        margin: 2;
    }
    
    .sync-status {
        height: 8;
        border: solid $primary;
        margin: 1 0;
        padding: 1;
        overflow-y: auto;
    }
    
    .preview-container {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        overflow-y: auto;
    }
    
    .preview-header {
        height: 3;
        border-bottom: solid $secondary;
        margin-bottom: 1;
        padding-bottom: 1;
    }
    
    .preview-section {
        margin: 1 0;
        padding: 1;
        border: solid $secondary;
    }
    
    .preview-actions {
        height: 8;
        layout: vertical;
        margin-top: 2;
    }
    
    .action-button {
        width: 100%;
        height: 2;
        margin: 1 0;
    }
    
    .status-active {
        color: $success;
    }
    
    .status-inactive {
        color: $error;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_locrit = None
        self.locrits_data = {}
        self.logger = ScreenLogger("LocalLocrits", self)

    def compose(self) -> ComposeResult:
        with Container(classes="local-container"):
            # Panneau gauche - Liste des Locrits
            with Container(classes="left-panel"):
                yield Label("🏠 Mes Locrits Locaux", classes="user-info")
                
                # Zone de statut de synchronisation Firestore
                with Container(classes="sync-status"):
                    yield Log(id="sync_log", auto_scroll=True)
                
                with Container(classes="locrits-list", id="locrits_container"):
                    yield Static("🔍 Chargement des Locrits locaux...", id="local_status")
                
                with Horizontal():
                    yield Button("➕ Créer Nouveau", id="create_new_btn", variant="success")
                    yield Button("🔄 Synchroniser", id="sync_btn", variant="warning")
                    yield Button("🔙 Retour", id="back_btn", variant="primary")
            
            # Panneau droit - Aperçu détaillé du Locrit sélectionné
            with Container(classes="right-panel"):
                with Container(classes="preview-container", id="preview_container"):
                    yield Static("👈 Sélectionnez un Locrit pour voir les détails", id="preview_content")

    def on_mount(self):
        # Enregistrer le widget de log pour synchronisation
        sync_log = self.query_one("#sync_log", Log)
        ui_logging_service.register_log_widget("sync_log", sync_log)

        asyncio.create_task(self._load_local_locrits())
        asyncio.create_task(self._check_firestore_sync_status())

    def on_screen_resume(self):
        """Appelé quand on revient à cet écran"""
        self.logger.debug("Retour à l'écran, rechargement des locrits")
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
            self.logger.debug(f"Chargement de {len(locrits)} locrit(s) depuis config")

            # Nettoyer le container
            await container.remove_children()

            if locrits:
                # Stocker les données des locrits
                self.locrits_data = {}

                # Afficher chaque locrit
                for locrit_name in locrits:
                    settings = config_service.get_locrit_settings(locrit_name)
                    if settings:  # Vérifier que les settings ne sont pas None
                        self.locrits_data[locrit_name] = settings
                        await self._add_locrit_item(container, locrit_name, settings)
                        self.logger.debug(f"Locrit ajouté à l'affichage: {locrit_name}")
                    else:
                        self.logger.warning(f"Impossible de charger les settings pour: {locrit_name}")

                self.logger.info(f"{len(self.locrits_data)} locrit(s) chargé(s) avec succès")
            else:
                # Aucun locrit trouvé
                no_locrits = Static("🏠 Aucun Locrit local trouvé.\n💡 Utilisez 'Créer Nouveau' pour en créer un.",
                                  classes="no-locrits")
                await container.mount(no_locrits)
                self.logger.info("Aucun locrit trouvé")

        except Exception as e:
            error_msg = f"Erreur lors du chargement des locrits: {str(e)}"
            status.update(f"❌ {error_msg}")
            self.logger.error(error_msg)

    async def _add_locrit_item(self, container: Container, name: str, settings: dict):
        """Ajoute un item de locrit au container"""
        
        # Récupérer les informations du locrit
        description = settings.get('description', 'Aucune description')
        is_active = settings.get('active', False)
        status_icon = "🟢" if is_active else "🔴"
        model = settings.get('ollama_model', 'Non spécifié')
        
        # Créer le container pour cet item cliquable
        item_container = Button(
            f"{status_icon} {name}\n📝 {description[:50]}{'...' if len(description) > 50 else ''}\n🤖 {model}",
            id=f"select_{name}",
            classes="locrit-item"
        )
        
        await container.mount(item_container)

    def _update_preview(self, locrit_name: str):
        """Met à jour l'aperçu du Locrit sélectionné"""
        preview_container = self.query_one("#preview_container", Container)
        
        if locrit_name not in self.locrits_data:
            return
        
        settings = self.locrits_data[locrit_name]
        
        # Marquer comme sélectionné
        self.selected_locrit = locrit_name
        
        # Mettre à jour l'affichage de sélection
        container = self.query_one("#locrits_container", Container)
        for child in container.children:
            if hasattr(child, 'id') and child.id and child.id.startswith("select_"):
                selected_name = child.id[7:]  # Enlever "select_"
                if selected_name == locrit_name:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")
        
        # Construire l'aperçu détaillé
        is_active = settings.get('active', False)
        status_text = "🟢 Actif" if is_active else "🔴 Inactif"
        status_class = "status-active" if is_active else "status-inactive"
        
        description = settings.get('description', 'Aucune description')
        model = settings.get('ollama_model', 'Non spécifié')
        created_at = settings.get('created_at', 'Inconnu')[:19] if settings.get('created_at') else 'Inconnu'
        updated_at = settings.get('updated_at', 'Inconnu')[:19] if settings.get('updated_at') else 'Inconnu'
        public_address = settings.get('public_address', 'Aucune')
        
        # Paramètres d'accès
        open_to = settings.get('open_to', {})
        access_to = settings.get('access_to', {})
        
        # Construire le contenu de l'aperçu
        preview_html = f"""
[bold]{locrit_name}[/bold]
[{status_class}]{status_text}[/{status_class}]

📝 [bold]Description[/bold]
{description}

🤖 [bold]Modèle Ollama[/bold]
{model}

🌐 [bold]Adresse Publique[/bold]
{public_address}

📅 [bold]Dates[/bold]
Créé: {created_at}
Modifié: {updated_at}

🔐 [bold]Ouvert à[/bold]
• Humains: {'✅' if open_to.get('humans', True) else '❌'}
• Autres Locrits: {'✅' if open_to.get('locrits', True) else '❌'}
• Invitations: {'✅' if open_to.get('invitations', True) else '❌'}
• Internet: {'✅' if open_to.get('internet', False) else '❌'}
• Plateforme: {'✅' if open_to.get('platform', False) else '❌'}

📊 [bold]Accès aux données[/bold]
• Logs: {'✅' if access_to.get('logs', True) else '❌'}
• Mémoire rapide: {'✅' if access_to.get('quick_memory', True) else '❌'}
• Mémoire complète: {'✅' if access_to.get('full_memory', False) else '❌'}
• Infos LLM: {'✅' if access_to.get('llm_info', True) else '❌'}
"""
        
        # Remplacer le contenu
        asyncio.create_task(self._replace_preview_content(preview_html, locrit_name))

    async def _replace_preview_content(self, content: str, locrit_name: str):
        """Remplace le contenu de l'aperçu avec les actions"""
        preview_container = self.query_one("#preview_container", Container)
        
        # Nettoyer le container
        await preview_container.remove_children()
        
        # Ajouter l'en-tête
        await preview_container.mount(Static(content, markup=True))
        
        # Ajouter les actions
        with preview_container:
            actions_container = Container(classes="preview-actions")
            
            # Boutons d'action selon l'état
            settings = self.locrits_data[locrit_name]
            is_active = settings.get('active', False)
            
            if is_active:
                await actions_container.mount(Button("⏹️ Arrêter le Locrit", id=f"stop_{locrit_name}", 
                                                    variant="error", classes="action-button"))
                await actions_container.mount(Button("💬 Parler avec le Locrit", id=f"chat_{locrit_name}", 
                                                    variant="success", classes="action-button"))
            else:
                await actions_container.mount(Button("▶️ Démarrer le Locrit", id=f"start_{locrit_name}", 
                                                    variant="success", classes="action-button"))
            
            await actions_container.mount(Button("📄 Page Descriptive", id=f"info_{locrit_name}", 
                                                variant="primary", classes="action-button"))
            await actions_container.mount(Button("⚙️ Éditer Configuration", id=f"config_{locrit_name}", 
                                                variant="default", classes="action-button"))
            await actions_container.mount(Button("🗑️ Supprimer", id=f"delete_{locrit_name}", 
                                                variant="error", classes="action-button"))
            
            await preview_container.mount(actions_container)
    
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
        elif button_id.startswith("select_"):
            # Sélection d'un locrit pour l'aperçu
            locrit_name = button_id[7:]  # Enlever "select_"
            self._update_preview(locrit_name)
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
        elif button_id.startswith("info_"):
            locrit_name = button_id[5:]  # Enlever "info_"
            self._show_locrit_info_page(locrit_name)
        elif button_id.startswith("config_"):
            locrit_name = button_id[7:]  # Enlever "config_"
            self._configure_locrit(locrit_name)
        elif button_id.startswith("delete_"):
            locrit_name = button_id[7:]  # Enlever "delete_"
            self._delete_locrit(locrit_name)
    
    async def _manual_firestore_sync(self):
        """Synchronisation manuelle Firestore déclenchée par l'utilisateur"""

        self.logger.info("Synchronisation manuelle Firestore démarrée",
                        notify_user=False, ui_widget="sync_log")

        try:
            # Configurer l'auth pour Firestore
            app_user = getattr(self.app, 'current_user', None)
            if app_user:
                firestore_admin_service.set_auth_info(app_user)

            result = await firestore_admin_service.sync_all_locrits()

            if result.get("status") == "success":
                self.logger.success("Synchronisation Firestore réussie", ui_widget="sync_log")
                if result.get("uploaded"):
                    self.logger.info(f"Uploadés: {', '.join(result['uploaded'])}",
                                   notify_user=False, ui_widget="sync_log")
                if result.get("downloaded"):
                    self.logger.info(f"Téléchargés: {', '.join(result['downloaded'])}",
                                   notify_user=False, ui_widget="sync_log")
            else:
                error_msg = result.get('message', 'Erreur de synchronisation')
                self.logger.warning(f"Synchronisation échouée: {error_msg}", ui_widget="sync_log")

            if result.get("errors"):
                for error in result["errors"]:
                    self.logger.error(error, ui_widget="sync_log")

            # Recharger l'affichage des Locrits
            await self._load_local_locrits()

        except Exception as e:
            self.logger.error(f"Erreur de synchronisation: {str(e)}", ui_widget="sync_log")
    
    def _start_locrit(self, name: str):
        """Démarre un locrit"""
        self.logger.success(f"Démarrage de {name}")

        # Mettre à jour la configuration
        settings = config_service.get_locrit_settings(name)
        settings['active'] = True
        config_service.update_locrit_settings(name, settings)
        config_service.save_config()

        # Mettre à jour les données locales et l'affichage
        self.locrits_data[name] = settings
        self._update_preview(name)
        asyncio.create_task(self._load_local_locrits())

    def _stop_locrit(self, name: str):
        """Arrête un locrit"""
        self.logger.success(f"Arrêt de {name}")

        # Mettre à jour la configuration
        settings = config_service.get_locrit_settings(name)
        settings['active'] = False
        config_service.update_locrit_settings(name, settings)
        config_service.save_config()

        # Mettre à jour les données locales et l'affichage
        self.locrits_data[name] = settings
        self._update_preview(name)
        asyncio.create_task(self._load_local_locrits())
    
    def _show_locrit_info_page(self, name: str):
        """Affiche la page descriptive détaillée du Locrit"""
        from .locrit_info_screen import LocritInfoScreen
        try:
            info_screen = LocritInfoScreen(name, self.locrits_data[name])
            self.app.push_screen(info_screen)
        except Exception:
            # Si l'écran d'info n'existe pas encore, afficher une notification
            settings = self.locrits_data[name]
            info_text = f"""
📄 Page Descriptive - {name}

📝 Description: {settings.get('description', 'N/A')}
🤖 Modèle: {settings.get('ollama_model', 'N/A')}
🌐 Adresse: {settings.get('public_address', 'N/A')}
📅 Créé: {settings.get('created_at', 'N/A')[:19] if settings.get('created_at') else 'N/A'}
📊 Statut: {'🟢 Actif' if settings.get('active', False) else '🔴 Inactif'}

🔐 Paramètres d'accès:
{self._format_access_settings(settings)}
            """
            self.logger.info(f"Page d'infos de {name} (page dédiée à implémenter)", notify_user=True)
    
    def _format_access_settings(self, settings: dict) -> str:
        """Formate les paramètres d'accès pour affichage"""
        open_to = settings.get('open_to', {})
        access_to = settings.get('access_to', {})
        
        open_settings = []
        for key, value in open_to.items():
            open_settings.append(f"• {key.title()}: {'✅' if value else '❌'}")
        
        access_settings = []
        for key, value in access_to.items():
            access_settings.append(f"• {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")
        
        return f"Ouvert à:\n" + "\n".join(open_settings) + f"\n\nAccès aux données:\n" + "\n".join(access_settings)
    
    def _configure_locrit(self, name: str):
        """Configure un locrit"""
        from .edit_locrit_screen import EditLocritScreen
        try:
            edit_screen = EditLocritScreen(name, self.locrits_data[name])
            self.app.push_screen(edit_screen)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ouverture de l'édition de {name}: {str(e)}")
    
    def _delete_locrit(self, name: str):
        """Supprime un locrit"""
        success = config_service.delete_locrit(name)
        if success:
            config_service.save_config()
            # Nettoyer les données locales
            if name in self.locrits_data:
                del self.locrits_data[name]
            # Réinitialiser la sélection si c'était le locrit sélectionné
            if self.selected_locrit == name:
                self.selected_locrit = None
                preview_container = self.query_one("#preview_container", Container)
                asyncio.create_task(self._reset_preview())
            self.logger.success(f"Locrit {name} supprimé")
            asyncio.create_task(self._load_local_locrits())
        else:
            self.logger.error(f"Erreur lors de la suppression de {name}")

    async def _reset_preview(self):
        """Remet l'aperçu à son état initial"""
        preview_container = self.query_one("#preview_container", Container)
        await preview_container.remove_children()
        await preview_container.mount(Static("👈 Sélectionnez un Locrit pour voir les détails", id="preview_content"))
