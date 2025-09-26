"""
Module des écrans de l'interface utilisateur
"""

from .home_screen import HomeScreen
from .local_locrits_screen import LocalLocritsScreen
from .friends_screen import FriendsScreen
from .create_locrit_screen import CreateLocritScreen
from .chat_screen import ChatScreen
from .settings_screen import SettingsScreen
from .about_screen import AboutScreen
from .locrit_info_screen import LocritInfoScreen
from .edit_locrit_screen import EditLocritScreen

__all__ = [
    "HomeScreen",
    "LocalLocritsScreen", 
    "FriendsScreen",
    "CreateLocritScreen",
    "ChatScreen",
    "SettingsScreen",
    "AboutScreen",
    "LocritInfoScreen",
    "EditLocritScreen"
]
