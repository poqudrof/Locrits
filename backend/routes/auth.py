"""
Authentication routes for Locrit Web UI
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from src.services.auth_service import auth_service
from src.services.ui_logging_service import ui_logging_service

auth_bp = Blueprint('auth', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@auth_bp.route('/')
def index():
    """Page d'accueil - redirige vers le tableau de bord si connecté, sinon vers la connexion"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Veuillez saisir un email et un mot de passe.', 'error')
            return render_template('login.html')

        try:
            # Utiliser le service d'authentification existant
            auth_result = auth_service.sign_in_with_email(email, password)

            if auth_result and auth_result.get('success'):
                # Connexion réussie
                session['user_id'] = auth_result.get('localId')
                session['user_email'] = email
                session['user_name'] = auth_result.get('displayName', email.split('@')[0])

                logger.info(f"Connexion web réussie: {email}")
                flash(f'Bienvenue, {session["user_name"]} !', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                error_msg = auth_result.get('error', 'Identifiants incorrects')
                flash(f'Erreur de connexion: {error_msg}', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de l'authentification web: {str(e)}")
            flash('Erreur lors de la connexion. Veuillez réessayer.', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Déconnexion"""
    user_email = session.get('user_email', 'Utilisateur inconnu')
    session.clear()
    logger.info(f"Déconnexion web: {user_email}")
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))