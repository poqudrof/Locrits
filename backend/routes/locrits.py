"""
Locrit management routes for Locrit Web UI
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from backend.middleware.auth import login_required
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

locrits_bp = Blueprint('locrits', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@locrits_bp.route('/locrits/create', methods=['GET', 'POST'])
@login_required
def create_locrit():
    """Création d'un nouveau locrit"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            model = request.form.get('model', '').strip()
            public_address = request.form.get('public_address', '').strip()

            # Validation
            if not name:
                flash('Le nom du Locrit est obligatoire.', 'error')
                return render_template('create_locrit.html')

            if not description:
                flash('La description est obligatoire.', 'error')
                return render_template('create_locrit.html')

            if not model:
                flash('Le modèle Ollama est obligatoire.', 'error')
                return render_template('create_locrit.html')

            # Vérifier que le nom n'existe pas déjà
            existing_locrits = config_service.list_locrits()
            if name in existing_locrits:
                flash(f'Un Locrit avec le nom "{name}" existe déjà.', 'error')
                return render_template('create_locrit.html')

            # Paramètres open_to
            open_to = {
                'humans': 'humans' in request.form,
                'locrits': 'locrits' in request.form,
                'invitations': 'invitations' in request.form,
                'internet': 'internet' in request.form,
                'platform': 'platform' in request.form
            }

            # Paramètres access_to
            access_to = {
                'logs': 'logs' in request.form,
                'quick_memory': 'quick_memory' in request.form,
                'full_memory': 'full_memory' in request.form,
                'llm_info': 'llm_info' in request.form
            }

            # Créer les settings du nouveau locrit
            settings = {
                'description': description,
                'ollama_model': model,
                'public_address': public_address if public_address else None,
                'active': False,  # Nouveau locrit inactif par défaut
                'open_to': open_to,
                'access_to': access_to,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            # Sauvegarder
            config_service.update_locrit_settings(name, settings)
            success = config_service.save_config()

            if success:
                logger.info(f"Nouveau Locrit créé via web: {name}")
                flash(f'Locrit "{name}" créé avec succès !', 'success')
                return redirect(url_for('dashboard.locrits_list'))
            else:
                flash('Erreur lors de la sauvegarde.', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de la création du locrit: {str(e)}")
            flash('Erreur lors de la création du Locrit.', 'error')

    return render_template('create_locrit.html')


@locrits_bp.route('/locrits/<locrit_name>/edit', methods=['GET', 'POST'])
@login_required
def edit_locrit(locrit_name):
    """Édition d'un locrit existant"""

    # Récupérer les settings actuels
    settings = config_service.get_locrit_settings(locrit_name)
    if not settings:
        flash(f'Locrit "{locrit_name}" non trouvé.', 'error')
        return redirect(url_for('dashboard.locrits_list'))

    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            description = request.form.get('description', '').strip()
            model = request.form.get('model', '').strip()
            public_address = request.form.get('public_address', '').strip()

            # Validation
            if not description:
                flash('La description est obligatoire.', 'error')
                return render_template('edit_locrit.html', locrit_name=locrit_name, settings=settings)

            if not model:
                flash('Le modèle Ollama est obligatoire.', 'error')
                return render_template('edit_locrit.html', locrit_name=locrit_name, settings=settings)

            # Paramètres open_to
            open_to = {
                'humans': 'humans' in request.form,
                'locrits': 'locrits' in request.form,
                'invitations': 'invitations' in request.form,
                'internet': 'internet' in request.form,
                'platform': 'platform' in request.form
            }

            # Paramètres access_to
            access_to = {
                'logs': 'logs' in request.form,
                'quick_memory': 'quick_memory' in request.form,
                'full_memory': 'full_memory' in request.form,
                'llm_info': 'llm_info' in request.form
            }

            # Mettre à jour les settings
            settings.update({
                'description': description,
                'ollama_model': model,
                'public_address': public_address if public_address else None,
                'open_to': open_to,
                'access_to': access_to,
                'updated_at': datetime.now().isoformat()
            })

            # Sauvegarder
            config_service.update_locrit_settings(locrit_name, settings)
            success = config_service.save_config()

            if success:
                logger.info(f"Locrit mis à jour via web: {locrit_name}")
                flash(f'Locrit "{locrit_name}" mis à jour avec succès !', 'success')
                return redirect(url_for('dashboard.locrits_list'))
            else:
                flash('Erreur lors de la sauvegarde.', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du locrit: {str(e)}")
            flash('Erreur lors de la mise à jour du Locrit.', 'error')

    return render_template('edit_locrit.html', locrit_name=locrit_name, settings=settings)


@locrits_bp.route('/locrits/<locrit_name>/toggle', methods=['POST'])
@login_required
def toggle_locrit(locrit_name):
    """Active/désactive un locrit"""
    try:
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        # Inverser le statut
        settings['active'] = not settings.get('active', False)
        settings['updated_at'] = datetime.now().isoformat()

        # Sauvegarder
        config_service.update_locrit_settings(locrit_name, settings)
        success = config_service.save_config()

        if success:
            status = "activé" if settings['active'] else "désactivé"
            logger.info(f"Locrit {status} via web: {locrit_name}")
            return jsonify({
                'success': True,
                'active': settings['active'],
                'message': f'Locrit "{locrit_name}" {status}'
            })
        else:
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500

    except Exception as e:
        logger.error(f"Erreur lors du toggle du locrit: {str(e)}")
        return jsonify({'error': str(e)}), 500


@locrits_bp.route('/locrits/<locrit_name>/delete', methods=['POST'])
@login_required
def delete_locrit(locrit_name):
    """Supprime un locrit"""
    try:
        success = config_service.delete_locrit(locrit_name)
        if success:
            config_service.save_config()
            logger.info(f"Locrit supprimé via web: {locrit_name}")
            flash(f'Locrit "{locrit_name}" supprimé avec succès.', 'success')
        else:
            flash(f'Erreur lors de la suppression du Locrit "{locrit_name}".', 'error')

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du locrit: {str(e)}")
        flash('Erreur lors de la suppression.', 'error')

    return redirect(url_for('dashboard.locrits_list'))