"""
Error handlers for Locrit Web UI
"""

from flask import Blueprint, render_template, request

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    # Don't handle SocketIO routes - let SocketIO handle them
    if request.path.startswith('/socket.io/'):
        return error
    return render_template('error.html',
                         error_code=404,
                         error_message="Page non trouvée"), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Erreur interne du serveur"), 500