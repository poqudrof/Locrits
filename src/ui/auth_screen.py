"""
Écran d'authentification Firebase pour Locrit
Interface TUI pour connexion anonyme ou email/mot de passe
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Input, Label, Static
from textual.screen import Screen
from typing import Optional
import asyncio

class AuthScreen(Screen):
    """Écran d'authentification Firebase"""
    
    CSS = """
    AuthScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
        align: center top;
    }
    
    .auth-container {
        width: 60;
        height: auto;
        margin: 2;
        border: thick $primary;
        background: $panel;
        padding: 2;
    }
    
    .auth-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .auth-section {
        margin: 1;
        padding: 1;
        border: solid $secondary;
    }
    
    .auth-buttons {
        margin-top: 1;
        height: auto;
    }
    
    .auth-input {
        margin: 1 0;
    }
    
    .auth-error {
        color: $error;
        text-align: center;
        margin: 1 0;
    }
    
    .auth-success {
        color: $success;
        text-align: center;
        margin: 1 0;
    }
    
    .auth-info {
        color: $text-muted;
        text-align: center;
        margin: 1 0;
    }
    """
    
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.message_widget = None
        self.email_input = None
        self.password_input = None
        self.confirm_password_input = None
        self.is_create_mode = False
    
    def compose(self) -> ComposeResult:
        """Composition de l'interface d'authentification"""
        with Container(classes="auth-container"):
            yield Label("🔥 Authentification Firebase", classes="auth-title")
            
            # Section connexion anonyme
            with Vertical(classes="auth-section"):
                yield Label("Connexion Rapide", classes="auth-title")
                yield Label("Connexion anonyme (recommandé pour tester)", classes="auth-info")
                yield Button("🎭 Se connecter en anonyme", id="btn_anonymous", variant="primary")
            
            # Section email/mot de passe
            with Vertical(classes="auth-section"):
                yield Label("Connexion avec Compte", classes="auth-title")
                
                yield Input(
                    placeholder="Adresse email",
                    id="email_input",
                    classes="auth-input"
                )
                
                yield Input(
                    placeholder="Mot de passe",
                    password=True,
                    id="password_input", 
                    classes="auth-input"
                )
                
                yield Input(
                    placeholder="Confirmer mot de passe (création seulement)",
                    password=True,
                    id="confirm_password_input",
                    classes="auth-input"
                )
                
                with Horizontal(classes="auth-buttons"):
                    yield Button("🔑 Se connecter", id="btn_signin", variant="success")
                    yield Button("📝 Créer un compte", id="btn_create")
                    yield Button("🔄 Mot de passe oublié", id="btn_reset")
            
            # Zone des messages
            yield Static("", id="auth_message", classes="auth-info")
            
            # Bouton quitter
            with Horizontal(classes="auth-buttons"):
                yield Button("❌ Quitter", id="btn_quit", variant="error")
    
    def on_mount(self):
        """Appelé au montage de l'écran"""
        self.message_widget = self.query_one("#auth_message", Static)
        self.email_input = self.query_one("#email_input", Input)
        self.password_input = self.query_one("#password_input", Input)
        self.confirm_password_input = self.query_one("#confirm_password_input", Input)
        
        # Focus sur le premier input
        self.email_input.focus()
        
        # Masquer la confirmation de mot de passe par défaut
        self.confirm_password_input.display = False
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestionnaire des boutons"""
        button_id = event.button.id
        
        if button_id == "btn_anonymous":
            self._handle_anonymous_signin()
        elif button_id == "btn_signin":
            self._handle_email_signin()
        elif button_id == "btn_create":
            self._toggle_create_mode()
        elif button_id == "btn_reset":
            self._handle_password_reset()
        elif button_id == "btn_quit":
            self.app.exit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Gestionnaire de soumission des inputs"""
        if event.input.id == "confirm_password_input" and self.is_create_mode:
            self._handle_create_account()
        elif event.input.id == "password_input" and not self.is_create_mode:
            self._handle_email_signin()
        elif event.input.id == "email_input":
            self.password_input.focus()
    
    def _handle_anonymous_signin(self):
        """Gère la connexion anonyme"""
        self._show_message("🔄 Connexion anonyme en cours...", "info")
        
        async def do_anonymous_signin():
            result = self.auth_service.sign_in_anonymous()
            
            if result["success"]:
                self._show_message("✅ Connexion anonyme réussie!", "success")
                await asyncio.sleep(1)
                self._on_auth_success(result)
            else:
                self._show_message(f"❌ Erreur: {result['error']}", "error")
        
        asyncio.create_task(do_anonymous_signin())
    
    def _handle_email_signin(self):
        """Gère la connexion par email"""
        email = self.email_input.value.strip()
        password = self.password_input.value
        
        if not email or not password:
            self._show_message("❌ Veuillez saisir email et mot de passe", "error")
            return
        
        self._show_message("🔄 Connexion en cours...", "info")
        
        async def do_email_signin():
            result = self.auth_service.sign_in_with_email(email, password)
            
            if result["success"]:
                self._show_message("✅ Connexion réussie!", "success")
                await asyncio.sleep(1)
                self._on_auth_success(result)
            else:
                self._show_message(f"❌ {result['error']}", "error")
        
        asyncio.create_task(do_email_signin())
    
    def _handle_create_account(self):
        """Gère la création de compte"""
        email = self.email_input.value.strip()
        password = self.password_input.value
        confirm_password = self.confirm_password_input.value
        
        if not email or not password:
            self._show_message("❌ Veuillez saisir email et mot de passe", "error")
            return
        
        if password != confirm_password:
            self._show_message("❌ Les mots de passe ne correspondent pas", "error")
            return
        
        if len(password) < 6:
            self._show_message("❌ Le mot de passe doit contenir au moins 6 caractères", "error")
            return
        
        self._show_message("🔄 Création du compte...", "info")
        
        async def do_create_account():
            result = self.auth_service.create_user_with_email(email, password)
            
            if result["success"]:
                self._show_message("✅ Compte créé avec succès!", "success")
                await asyncio.sleep(1)
                self._on_auth_success(result)
            else:
                self._show_message(f"❌ {result['error']}", "error")
        
        asyncio.create_task(do_create_account())
    
    def _handle_password_reset(self):
        """Gère la réinitialisation de mot de passe"""
        email = self.email_input.value.strip()
        
        if not email:
            self._show_message("❌ Veuillez saisir votre adresse email", "error")
            return
        
        self._show_message("🔄 Envoi de l'email de réinitialisation...", "info")
        
        async def do_password_reset():
            result = self.auth_service.reset_password(email)
            
            if result["success"]:
                self._show_message("✅ Email de réinitialisation envoyé!", "success")
            else:
                self._show_message(f"❌ {result['error']}", "error")
        
        asyncio.create_task(do_password_reset())
    
    def _toggle_create_mode(self):
        """Bascule entre mode connexion et création"""
        self.is_create_mode = not self.is_create_mode
        
        if self.is_create_mode:
            self.confirm_password_input.display = True
            self.query_one("#btn_create", Button).label = "🔙 Retour à la connexion"
            self._show_message("💡 Mode création de compte activé", "info")
        else:
            self.confirm_password_input.display = False
            self.query_one("#btn_create", Button).label = "📝 Créer un compte"
            self._show_message("💡 Mode connexion activé", "info")
    
    def _show_message(self, message: str, message_type: str = "info"):
        """Affiche un message à l'utilisateur"""
        if message_type == "error":
            self.message_widget.update(message)
            self.message_widget.remove_class("auth-info", "auth-success")
            self.message_widget.add_class("auth-error")
        elif message_type == "success":
            self.message_widget.update(message)
            self.message_widget.remove_class("auth-info", "auth-error")
            self.message_widget.add_class("auth-success")
        else:
            self.message_widget.update(message)
            self.message_widget.remove_class("auth-error", "auth-success")
            self.message_widget.add_class("auth-info")
    
    def _on_auth_success(self, auth_result: dict):
        """Appelé quand l'authentification réussit"""
        # Retourner à l'écran principal avec les informations d'auth
        self.app.pop_screen()
        
        # Notifier l'app principale de la réussite de l'auth
        if hasattr(self.app, '_on_auth_success'):
            self.app._on_auth_success(auth_result)
