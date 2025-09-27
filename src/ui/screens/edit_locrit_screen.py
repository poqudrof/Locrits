"""
Écran d'édition d'un Locrit existant
Permet de modifier tous les paramètres d'un Locrit
"""

from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, Checkbox, TextArea, Static
from textual.screen import Screen
from ...services.ui_logging_service import ScreenLogger


class EditLocritScreen(Screen):
    """Écran d'édition d'un Locrit existant"""
    
    CSS = """
    EditLocritScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .edit-container {
        padding: 2;
        height: auto;
        min-height: 100vh;
        layout: vertical;
    }
    
    .edit-header {
        height: 3;
        border: solid $primary;
        padding: 1;
        margin-bottom: 2;
        text-align: center;
    }
    
    .form-section {
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .form-row {
        margin: 1 0;
        layout: horizontal;
    }
    
    .form-label {
        width: 20;
        text-align: right;
        margin-right: 2;
    }
    
    .form-input {
        width: 1fr;
    }
    
    .checkbox-section {
        layout: vertical;
        margin: 1 0;
    }
    
    .checkbox-group {
        layout: horizontal;
        margin: 0.5 0;
    }
    
    .checkbox-label {
        width: 20;
        text-align: right;
        margin-right: 2;
    }
    """
    
    def __init__(self, locrit_name: str, settings: dict):
        super().__init__()
        self.locrit_name = locrit_name
        self.settings = settings.copy()  # Copie pour éviter les modifications directes
        self.form_data = {}
        self.logger = ScreenLogger("EditLocrit", self)
    
    def compose(self) -> ComposeResult:
        with Container(classes="edit-container"):
            # En-tête
            with Container(classes="edit-header"):
                yield Label(f"⚙️ Édition de {self.locrit_name}", classes="section-title")
            
            # Informations de base
            with Container(classes="form-section"):
                yield Label("📝 Informations Générales", classes="section-title")
                
                with Container(classes="form-row"):
                    yield Label("Description:", classes="form-label")
                    yield TextArea(
                        self.settings.get('description', ''),
                        id="description_input",
                        classes="form-input"
                    )
                
                with Container(classes="form-row"):
                    yield Label("Modèle Ollama:", classes="form-label")
                    yield Input(
                        value=self.settings.get('ollama_model', 'llama3.2'),
                        placeholder="llama3.2",
                        id="model_input",
                        classes="form-input"
                    )
                
                with Container(classes="form-row"):
                    yield Label("Adresse publique:", classes="form-label")
                    yield Input(
                        value=self.settings.get('public_address', ''),
                        placeholder="Ex: mon-locrit.localhost.run",
                        id="address_input",
                        classes="form-input"
                    )
            
            # Paramètres "Ouvert à"
            with Container(classes="form-section"):
                yield Label("🔐 Ouvert à", classes="section-title")
                
                open_to = self.settings.get('open_to', {})
                
                with Container(classes="checkbox-section"):
                    with Container(classes="checkbox-group"):
                        yield Label("Humains:", classes="checkbox-label")
                        yield Checkbox("Permettre aux humains de se connecter", 
                                     value=open_to.get('humans', True), 
                                     id="open_humans")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Autres Locrits:", classes="checkbox-label")
                        yield Checkbox("Permettre aux autres Locrits de se connecter", 
                                     value=open_to.get('locrits', True), 
                                     id="open_locrits")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Invitations:", classes="checkbox-label")
                        yield Checkbox("Accepter les invitations externes", 
                                     value=open_to.get('invitations', True), 
                                     id="open_invitations")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Internet:", classes="checkbox-label")
                        yield Checkbox("Accès autonome à Internet", 
                                     value=open_to.get('internet', False), 
                                     id="open_internet")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Plateforme:", classes="checkbox-label")
                        yield Checkbox("Interactions avec la plateforme", 
                                     value=open_to.get('platform', False), 
                                     id="open_platform")
            
            # Paramètres "Accès aux données"
            with Container(classes="form-section"):
                yield Label("📊 Accès aux Données", classes="section-title")
                
                access_to = self.settings.get('access_to', {})
                
                with Container(classes="checkbox-section"):
                    with Container(classes="checkbox-group"):
                        yield Label("Logs:", classes="checkbox-label")
                        yield Checkbox("Accès aux logs système", 
                                     value=access_to.get('logs', True), 
                                     id="access_logs")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Mémoire rapide:", classes="checkbox-label")
                        yield Checkbox("Accès à la mémoire de conversation récente", 
                                     value=access_to.get('quick_memory', True), 
                                     id="access_quick_memory")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Mémoire complète:", classes="checkbox-label")
                        yield Checkbox("Accès à toute la mémoire historique", 
                                     value=access_to.get('full_memory', False), 
                                     id="access_full_memory")
                    
                    with Container(classes="checkbox-group"):
                        yield Label("Infos LLM:", classes="checkbox-label")
                        yield Checkbox("Accès aux informations du modèle de langage", 
                                     value=access_to.get('llm_info', True), 
                                     id="access_llm_info")
            
            # Actions
            with Horizontal():
                yield Button("💾 Sauvegarder", id="save_btn", variant="success")
                yield Button("🔄 Restaurer", id="reset_btn", variant="warning")
                yield Button("❌ Annuler", id="cancel_btn", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "cancel_btn":
            self.app.pop_screen()
        elif button_id == "reset_btn":
            self._reset_form()
        elif button_id == "save_btn":
            self._save_changes()
    
    def _reset_form(self):
        """Restaure les valeurs originales du formulaire"""
        # Réinitialiser les inputs texte
        description_input = self.query_one("#description_input", TextArea)
        model_input = self.query_one("#model_input", Input)
        address_input = self.query_one("#address_input", Input)
        
        description_input.text = self.settings.get('description', '')
        model_input.value = self.settings.get('ollama_model', 'llama3.2')
        address_input.value = self.settings.get('public_address', '')
        
        # Réinitialiser les checkboxes "Ouvert à"
        open_to = self.settings.get('open_to', {})
        self.query_one("#open_humans", Checkbox).value = open_to.get('humans', True)
        self.query_one("#open_locrits", Checkbox).value = open_to.get('locrits', True)
        self.query_one("#open_invitations", Checkbox).value = open_to.get('invitations', True)
        self.query_one("#open_internet", Checkbox).value = open_to.get('internet', False)
        self.query_one("#open_platform", Checkbox).value = open_to.get('platform', False)
        
        # Réinitialiser les checkboxes "Accès aux données"
        access_to = self.settings.get('access_to', {})
        self.query_one("#access_logs", Checkbox).value = access_to.get('logs', True)
        self.query_one("#access_quick_memory", Checkbox).value = access_to.get('quick_memory', True)
        self.query_one("#access_full_memory", Checkbox).value = access_to.get('full_memory', False)
        self.query_one("#access_llm_info", Checkbox).value = access_to.get('llm_info', True)
        
        self.logger.info("Formulaire restauré aux valeurs originales", notify_user=True)
    
    def _save_changes(self):
        """Sauvegarde les modifications"""
        from ...services.config_service import config_service
        
        try:
            # Récupérer les valeurs du formulaire
            description = self.query_one("#description_input", TextArea).text
            model = self.query_one("#model_input", Input).value
            address = self.query_one("#address_input", Input).value
            
            # Paramètres "Ouvert à"
            open_to = {
                'humans': self.query_one("#open_humans", Checkbox).value,
                'locrits': self.query_one("#open_locrits", Checkbox).value,
                'invitations': self.query_one("#open_invitations", Checkbox).value,
                'internet': self.query_one("#open_internet", Checkbox).value,
                'platform': self.query_one("#open_platform", Checkbox).value,
            }
            
            # Paramètres "Accès aux données"
            access_to = {
                'logs': self.query_one("#access_logs", Checkbox).value,
                'quick_memory': self.query_one("#access_quick_memory", Checkbox).value,
                'full_memory': self.query_one("#access_full_memory", Checkbox).value,
                'llm_info': self.query_one("#access_llm_info", Checkbox).value,
            }
            
            # Validation basique
            if not description.strip():
                self.logger.warning("La description ne peut pas être vide")
                return

            if not model.strip():
                self.logger.warning("Le modèle Ollama ne peut pas être vide")
                return

            # Validation du modèle Ollama (format basique)
            if not model.strip().replace('.', '').replace('-', '').replace('_', '').replace(':', '').isalnum():
                self.logger.warning("Le nom du modèle Ollama contient des caractères invalides")
                return

            # Validation de l'adresse publique si fournie
            if address.strip() and not self._validate_public_address(address.strip()):
                self.logger.warning("Format d'adresse publique invalide")
                return
            
            # Créer les nouveaux paramètres
            new_settings = self.settings.copy()
            new_settings.update({
                'description': description.strip(),
                'ollama_model': model.strip(),
                'public_address': address.strip() if address.strip() else None,
                'open_to': open_to,
                'access_to': access_to,
                'updated_at': datetime.now().isoformat()
            })
            
            # Sauvegarder
            config_service.update_locrit_settings(self.locrit_name, new_settings)
            success = config_service.save_config()
            
            if success:
                self.logger.success(f"{self.locrit_name} sauvegardé avec succès")
                self.app.pop_screen()  # Retour à l'écran précédent
            else:
                self.logger.error("Erreur lors de la sauvegarde")

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {str(e)}")

    def _validate_public_address(self, address: str) -> bool:
        """Valide le format d'une adresse publique"""
        # Validation basique d'URL/hostname
        import re

        # Pattern pour hostname/URL basique
        pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9.-]+\.localhost\.run$'

        if re.match(pattern, address):
            return True

        # Accepter localhost et IP locales pour les tests
        if address in ['localhost', 'localhost'] or address.startswith('192.168.') or address.startswith('10.'):
            return True

        return False
