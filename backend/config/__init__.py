"""
Configuration package for Locrit Backend
"""

from backend.config.flask_config import config, Config, DevelopmentConfig, ProductionConfig

__all__ = ['config', 'Config', 'DevelopmentConfig', 'ProductionConfig']