"""
Service de logging pour l'interface utilisateur
Gère les logs de débogage vs les notifications utilisateur importantes
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from textual.widgets import Log


class UILoggingService:
    """Service de logging spécialement conçu pour l'interface utilisateur"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.ui_logs: Dict[str, Log] = {}  # Widgets Log par ID

    def _setup_logger(self) -> logging.Logger:
        """Configure le logger pour l'interface utilisateur"""
        # Créer le dossier logs s'il n'existe pas
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Créer le logger
        logger = logging.getLogger("ui_service")
        logger.setLevel(logging.DEBUG)

        # Éviter la duplication des handlers
        if logger.handlers:
            return logger

        # Handler pour fichier (tout)
        file_handler = logging.FileHandler(log_dir / "ui.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Handler pour console (erreurs seulement)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def register_log_widget(self, widget_id: str, log_widget: Log):
        """Enregistre un widget Log pour recevoir les messages"""
        self.ui_logs[widget_id] = log_widget
        self.logger.debug(f"Widget de log enregistré: {widget_id}")

    def unregister_log_widget(self, widget_id: str):
        """Désenregistre un widget Log"""
        if widget_id in self.ui_logs:
            del self.ui_logs[widget_id]
            self.logger.debug(f"Widget de log désenregistré: {widget_id}")

    def debug(self, message: str, to_ui: bool = False, ui_widget: Optional[str] = None):
        """Log de débogage - normalement pas affiché à l'utilisateur"""
        self.logger.debug(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"🔍 {message}")

    def info(self, message: str, to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log d'information - peut être affiché à l'utilisateur"""
        self.logger.info(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"ℹ️  {message}")

    def warning(self, message: str, to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log d'avertissement - généralement affiché à l'utilisateur"""
        self.logger.warning(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"⚠️  {message}")

    def error(self, message: str, to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log d'erreur - toujours affiché à l'utilisateur"""
        self.logger.error(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"❌ {message}")

    def success(self, message: str, to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log de succès - généralement affiché à l'utilisateur"""
        self.logger.info(f"SUCCESS: {message}")
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"✅ {message}")

    def operation_start(self, operation: str, details: str = "", to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log de début d'opération"""
        message = f"Début: {operation}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            self.ui_logs[ui_widget].write_line(f"🔄 {operation}...")

    def operation_end(self, operation: str, success: bool = True, details: str = "", to_ui: bool = True, ui_widget: Optional[str] = None):
        """Log de fin d'opération"""
        status = "réussie" if success else "échouée"
        message = f"Fin: {operation} - {status}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
        if to_ui and ui_widget and ui_widget in self.ui_logs:
            icon = "✅" if success else "❌"
            self.ui_logs[ui_widget].write_line(f"{icon} {operation} {status}")


# Instance globale du service de logging UI
ui_logging_service = UILoggingService()


def should_notify_user(message_type: str, context: str = "") -> bool:
    """
    Détermine si un message doit être affiché comme notification utilisateur
    ou simplement loggé
    """
    # Messages qui doivent toujours être des notifications
    user_notifications = [
        "error", "success", "warning",  # Types d'état
        "start", "stop", "delete",      # Actions utilisateur
        "save", "load", "sync"          # Opérations importantes
    ]

    # Messages qui ne doivent jamais être des notifications
    debug_only = [
        "debug", "trace", "verbose",
        "loading_item", "adding_item", "processing"
    ]

    if any(keyword in message_type.lower() for keyword in user_notifications):
        return True

    if any(keyword in message_type.lower() for keyword in debug_only):
        return False

    # Par défaut, ne pas notifier pour éviter le spam
    return False


class ScreenLogger:
    """Helper pour les écrans qui combine logging et notifications intelligentes"""

    def __init__(self, screen_name: str, screen_instance):
        self.screen_name = screen_name
        self.screen = screen_instance
        self.logger = ui_logging_service

    def log_and_notify(self, message: str, level: str = "info", notify_user: bool = None, ui_widget: Optional[str] = None):
        """Log un message et détermine automatiquement s'il faut notifier l'utilisateur"""

        # Détermination automatique si pas spécifié
        if notify_user is None:
            notify_user = should_notify_user(level, message)

        # Log selon le niveau
        if level == "debug":
            self.logger.debug(f"[{self.screen_name}] {message}", ui_widget=ui_widget)
        elif level == "info":
            self.logger.info(f"[{self.screen_name}] {message}", ui_widget=ui_widget)
        elif level == "warning":
            self.logger.warning(f"[{self.screen_name}] {message}", ui_widget=ui_widget)
        elif level == "error":
            self.logger.error(f"[{self.screen_name}] {message}", ui_widget=ui_widget)
        elif level == "success":
            self.logger.success(f"[{self.screen_name}] {message}", ui_widget=ui_widget)

        # Notification utilisateur si nécessaire
        if notify_user and hasattr(self.screen, 'notify'):
            self.screen.notify(message)

    def debug(self, message: str, ui_widget: Optional[str] = None):
        """Log de débogage - pas de notification utilisateur"""
        self.log_and_notify(message, "debug", notify_user=False, ui_widget=ui_widget)

    def info(self, message: str, notify_user: bool = False, ui_widget: Optional[str] = None):
        """Log d'info - notification optionnelle"""
        self.log_and_notify(message, "info", notify_user=notify_user, ui_widget=ui_widget)

    def success(self, message: str, ui_widget: Optional[str] = None):
        """Log de succès - avec notification utilisateur"""
        self.log_and_notify(message, "success", notify_user=True, ui_widget=ui_widget)

    def warning(self, message: str, ui_widget: Optional[str] = None):
        """Log d'avertissement - avec notification utilisateur"""
        self.log_and_notify(message, "warning", notify_user=True, ui_widget=ui_widget)

    def error(self, message: str, ui_widget: Optional[str] = None):
        """Log d'erreur - avec notification utilisateur"""
        self.log_and_notify(message, "error", notify_user=True, ui_widget=ui_widget)