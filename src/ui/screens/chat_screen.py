"""
Écran de chat avec un Locrit
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Input, Static
from textual.screen import Screen
from ...services.config_service import config_service


class ChatScreen(Screen):
    """Écran de chat avec un Locrit"""
    
    CSS = """
    ChatScreen {
        background: $surface;
        layout: vertical;
        overflow-y: auto;
    }
    
    .chat-container {
        padding: 2;
        height: 100vh;
        layout: vertical;
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
