"""
Flask configuration for Locrit Web UI
"""

import os


class Config:
    """Configuration de base pour Flask"""

    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Configuration des sessions
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuration CORS pour React frontend
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:5173',
        'http://localhost:5174'
    ]


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    FLASK_ENV = 'development'

    # More permissive CORS in development
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',  # Common React dev port
        'http://localhost:3000'
    ]


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True  # HTTPS requis en production


# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}