"""
Dashboard routes for Locrit Web UI
"""

from flask import Blueprint, render_template, session, flash
from backend.middleware.auth import login_required
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

dashboard_bp = Blueprint('dashboard', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    try:
        # Récupérer les locrits locaux
        locrits = config_service.list_locrits()
        locrits_data = []

        for locrit_name in locrits:
            settings = config_service.get_locrit_settings(locrit_name)
            if settings:
                locrits_data.append({
                    'name': locrit_name,
                    'description': settings.get('description', 'Aucune description'),
                    'active': settings.get('active', False),
                    'model': settings.get('ollama_model', 'Non spécifié'),
                    'public_address': settings.get('public_address', ''),
                    'created_at': settings.get('created_at', ''),
                    'updated_at': settings.get('updated_at', '')
                })

        # Statistiques
        stats = {
            'total_locrits': len(locrits_data),
            'active_locrits': len([l for l in locrits_data if l['active']]),
            'inactive_locrits': len([l for l in locrits_data if not l['active']])
        }

        return render_template('dashboard.html',
                             locrits=locrits_data,
                             stats=stats,
                             user_name=session.get('user_name'))

    except Exception as e:
        logger.error(f"Erreur lors du chargement du tableau de bord: {str(e)}")
        flash('Erreur lors du chargement des données.', 'error')
        return render_template('dashboard.html', locrits=[], stats={})


@dashboard_bp.route('/locrits')
@login_required
def locrits_list():
    """Liste détaillée des locrits locaux"""
    try:
        locrits = config_service.list_locrits()
        locrits_data = []

        for locrit_name in locrits:
            settings = config_service.get_locrit_settings(locrit_name)
            if settings:
                locrits_data.append({
                    'name': locrit_name,
                    'description': settings.get('description', 'Aucune description'),
                    'active': settings.get('active', False),
                    'model': settings.get('ollama_model', 'Non spécifié'),
                    'public_address': settings.get('public_address', ''),
                    'created_at': settings.get('created_at', ''),
                    'updated_at': settings.get('updated_at', ''),
                    'open_to': settings.get('open_to', {}),
                    'access_to': settings.get('access_to', {})
                })

        return render_template('locrits_list.html', locrits=locrits_data)

    except Exception as e:
        logger.error(f"Erreur lors du chargement des locrits: {str(e)}")
        flash('Erreur lors du chargement des locrits.', 'error')
        return render_template('locrits_list.html', locrits=[])