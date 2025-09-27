"""
Flask application factory for Locrit Web UI
"""

import os
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO

from backend.config.flask_config import config
from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.locrits import locrits_bp
from backend.routes.chat import chat_bp
from backend.routes.config import config_bp
from backend.routes.api.v1 import api_v1_bp
from backend.routes.errors import errors_bp
from backend.routes.websocket import chat_namespace
from src.services.ui_logging_service import ui_logging_service


def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Load configuration
    app.config.from_object(config[config_name])

    # Set up secret key
    app.secret_key = app.config['SECRET_KEY']

    # Initialize SocketIO
    socketio = SocketIO(cors_allowed_origins=app.config['CORS_ORIGINS'])
    socketio.init_app(app)

    # Enable CORS for React frontend
    cors_config = {
        'origins': app.config['CORS_ORIGINS'],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'supports_credentials': True,
        'automatic_options': True
    }

    # More permissive headers in development
    if app.config.get('DEBUG', False):
        cors_config['allow_headers'] = '*'
    else:
        cors_config['allow_headers'] = ['Content-Type', 'Authorization', 'X-Requested-With']

    CORS(app, **cors_config)

    # Initialize logger
    logger = ui_logging_service.logger

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(locrits_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(errors_bp)

    # Register WebSocket namespace
    socketio.on_namespace(chat_namespace)


    logger.info("Flask application created and configured")

    return app, socketio


def run_app():
    """Run the Flask application"""
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'default')
    host = os.getenv('WEB_HOST', 'localhost')
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Create app and socketio
    app, socketio = create_app(config_name)

    # Get logger
    logger = ui_logging_service.logger

    logger.info(f"Démarrage de l'interface web sur http://{host}:{port}")
    print(f"🌐 Interface web Locrit démarrée sur http://{host}:{port}")

    # Run the app with socketio
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

    return app