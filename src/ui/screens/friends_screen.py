"""
Écran des Locrits amis en réseau
"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label, Static
from textual.screen import Screen


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
