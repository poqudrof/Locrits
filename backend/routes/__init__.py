"""
Routes package for Locrit Backend
"""

from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.locrits import locrits_bp
from backend.routes.chat import chat_bp
from backend.routes.config import config_bp
from backend.routes.errors import errors_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'locrits_bp',
    'chat_bp',
    'config_bp',
    'errors_bp'
]