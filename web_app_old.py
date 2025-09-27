#!/usr/bin/env python3
"""
Web UI pour Locrit - Interface web moderne pour gérer les Locrits
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from functools import wraps
from src.services.config_service import config_service
from src.services.auth_service import auth_service
from src.services.ui_logging_service import ui_logging_service

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for React frontend
CORS(app, origins=['http://localhost:5174', 'http://localhost:5174'])

# Configuration Flask
app.config.update(
    SESSION_COOKIE_SECURE=False,  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Logger pour l'application web
logger = ui_logging_service.logger


def login_required(f):
    """Décorateur pour protéger les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Page d'accueil - redirige vers le tableau de bord si connecté, sinon vers la connexion"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('dashboard'))
            else:
                error_msg = auth_result.get('error', 'Identifiants incorrects')
                flash(f'Erreur de connexion: {error_msg}', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de l'authentification web: {str(e)}")
            flash('Erreur lors de la connexion. Veuillez réessayer.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Déconnexion"""
    user_email = session.get('user_email', 'Utilisateur inconnu')
    session.clear()
    logger.info(f"Déconnexion web: {user_email}")
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
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


@app.route('/locrits')
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


@app.route('/locrits/create', methods=['GET', 'POST'])
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
                return redirect(url_for('locrits_list'))
            else:
                flash('Erreur lors de la sauvegarde.', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de la création du locrit: {str(e)}")
            flash('Erreur lors de la création du Locrit.', 'error')

    return render_template('create_locrit.html')


@app.route('/locrits/<locrit_name>/edit', methods=['GET', 'POST'])
@login_required
def edit_locrit(locrit_name):
    """Édition d'un locrit existant"""

    # Récupérer les settings actuels
    settings = config_service.get_locrit_settings(locrit_name)
    if not settings:
        flash(f'Locrit "{locrit_name}" non trouvé.', 'error')
        return redirect(url_for('locrits_list'))

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
                return redirect(url_for('locrits_list'))
            else:
                flash('Erreur lors de la sauvegarde.', 'error')

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du locrit: {str(e)}")
            flash('Erreur lors de la mise à jour du Locrit.', 'error')

    return render_template('edit_locrit.html', locrit_name=locrit_name, settings=settings)


@app.route('/locrits/<locrit_name>/toggle', methods=['POST'])
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


@app.route('/locrits/<locrit_name>/delete', methods=['POST'])
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

    return redirect(url_for('locrits_list'))


@app.route('/config')
@login_required
def app_config():
    """Configuration de l'application"""
    try:
        # Récupérer les configurations actuelles
        config_data = {
            'ollama': config_service.get_ollama_config(),
            'network': config_service.get_network_config(),
            'memory': config_service.get_memory_config(),
            'ui': config_service.get_ui_config()
        }

        return render_template('app_config.html', config=config_data)

    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        flash('Erreur lors du chargement de la configuration.', 'error')
        return render_template('app_config.html', config={})


@app.route('/api/ollama/status', methods=['GET'])
def ollama_status():
    """Récupère le statut du serveur Ollama"""
    try:
        from src.services.ollama_service import ollama_service

        # Tester la connexion rapidement
        result = ollama_service.test_connection()

        return jsonify({
            'success': result.get('success', False),
            'status': 'connected' if result.get('success') else 'disconnected',
            'models_count': len(result.get('models', [])) if result.get('success') else 0
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/ollama/models', methods=['GET'])
def ollama_models():
    """API pour récupérer la liste des modèles Ollama disponibles"""
    try:
        import requests

        # Récupérer l'URL Ollama depuis la configuration
        ollama_url = config_service.get('ollama.base_url', 'http://localhost:11434')
        api_url = f"{ollama_url.rstrip('/')}/api/tags"

        logger.info(f"Récupération des modèles Ollama depuis: {api_url}")

        # Récupérer la liste des modèles
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        models = []

        for model in data.get('models', []):
            models.append({
                'name': model['name'],
                'modified_at': model.get('modified_at'),
                'size': model.get('size', 0)
            })

        # Trier par nom
        models.sort(key=lambda x: x['name'])

        return jsonify({
            'success': True,
            'models': models,
            'total_models': len(models)
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur connexion Ollama pour récupérer modèles: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Impossible de se connecter au serveur Ollama: {str(e)}',
            'models': []
        }), 500

    except Exception as e:
        logger.error(f"Erreur récupération modèles Ollama: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}',
            'models': []
        }), 500


@app.route('/config/test-ollama', methods=['POST'])
def test_ollama_connection():
    """Test la connexion au serveur Ollama côté serveur"""
    try:
        import requests

        # Récupérer l'URL depuis le formulaire en priorité
        data = request.get_json() if request.is_json else {}
        test_url = data.get('ollama_url') or data.get('base_url')

        logger.info(f"Données reçues pour test Ollama: {data}")
        logger.info(f"URL extraite du formulaire: {test_url}")

        if not test_url:
            # Fallback vers la config uniquement si aucune URL n'est fournie
            test_url = config_service.get('ollama.base_url', 'http://localhost:11434')
            logger.info(f"Utilisation de la config par défaut: {test_url}")

        # Nettoyer l'URL et s'assurer qu'elle se termine correctement
        test_url = test_url.rstrip('/')
        api_url = f"{test_url}/api/tags"

        logger.info(f"Test de connexion Ollama vers: {api_url}")

        # Test de connexion direct
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        models = [model['name'] for model in data.get('models', [])]

        return jsonify({
            'success': True,
            'message': 'Connexion réussie',
            'models': models[:5],  # Limiter à 5 modèles pour l'affichage
            'total_models': len(models),
            'tested_url': test_url
        })

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Impossible de se connecter au serveur Ollama. Vérifiez que le serveur est démarré."
        logger.error(f"Erreur connexion Ollama: {error_msg} - {str(e)}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'technical_details': str(e),
            'tested_url': test_url
        }), 500

    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout lors de la connexion au serveur Ollama."
        logger.error(f"Timeout Ollama: {error_msg} - {str(e)}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'tested_url': test_url
        }), 500

    except requests.exceptions.RequestException as e:
        error_msg = f"Erreur de requête: {str(e)}"
        logger.error(f"Erreur requête Ollama: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'tested_url': test_url
        }), 500

    except Exception as e:
        logger.error(f"Erreur test connexion Ollama: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur inattendue: {str(e)}'
        }), 500


@app.route('/config/save', methods=['POST'])
def save_config():
    """Sauvegarde la configuration de l'application"""
    try:
        # Récupérer les données du formulaire
        form_data = request.form.to_dict()

        # Mettre à jour la configuration Ollama
        if 'ollama_base_url' in form_data:
            config_service.set('ollama.base_url', form_data['ollama_base_url'])
        if 'ollama_default_model' in form_data:
            config_service.set('ollama.default_model', form_data['ollama_default_model'])
        if 'ollama_timeout' in form_data:
            config_service.set('ollama.timeout', int(form_data['ollama_timeout']))

        # Mettre à jour la configuration réseau
        if 'api_port' in form_data:
            config_service.set('network.api_server.port', int(form_data['api_port']))
        if 'api_host' in form_data:
            config_service.set('network.api_server.host', form_data['api_host'])

        # Mettre à jour la configuration UI
        if 'ui_theme' in form_data:
            config_service.set('ui.theme', form_data['ui_theme'])
        if 'refresh_interval' in form_data:
            config_service.set('ui.refresh_interval', int(form_data['refresh_interval']))

        # Sauvegarder
        success = config_service.save_config()

        if success:
            logger.info("Configuration mise à jour via web")
            flash('Configuration sauvegardée avec succès !', 'success')
        else:
            flash('Erreur lors de la sauvegarde de la configuration.', 'error')

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
        flash('Erreur lors de la sauvegarde de la configuration.', 'error')

    return redirect(url_for('app_config'))


@app.route('/locrits/<locrit_name>/chat')
@login_required
def chat_with_locrit(locrit_name):
    """Interface de chat avec un Locrit"""
    try:
        # Vérifier que le Locrit existe
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            flash(f'Locrit "{locrit_name}" non trouvé.', 'error')
            return redirect(url_for('locrits_list'))

        return render_template('chat.html',
                             locrit_name=locrit_name,
                             locrit_settings=settings,
                             user_name=session.get('user_name'))

    except Exception as e:
        logger.error(f"Erreur lors du chargement du chat: {str(e)}")
        flash('Erreur lors du chargement du chat.', 'error')
        return redirect(url_for('locrits_list'))


@app.route('/api/locrits/<locrit_name>/chat', methods=['POST'])
@login_required
def api_chat_with_locrit(locrit_name):
    """API pour envoyer un message à un Locrit"""
    try:
        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Récupérer le message
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message vide'}), 400

        # Utiliser le service Ollama pour générer la réponse
        from src.services.ollama_service import get_ollama_service
        ollama_service = get_ollama_service()

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Préparer le prompt système basé sur la description du Locrit
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

        # Pour l'instant, utiliser une réponse synchrone simple
        # Le streaming sera ajouté dans la prochaine étape
        try:
            import asyncio
            ollama_service.current_model = model
            ollama_service.is_connected = True
            ollama_service.available_models = connection_test.get('models', [])

            response = asyncio.run(ollama_service.chat(message, system_prompt))

            return jsonify({
                'success': True,
                'response': response,
                'locrit_name': locrit_name,
                'model': model
            })

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return jsonify({'error': f'Erreur de génération: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Erreur dans l'API chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


from flask import Response
import asyncio
import json
import threading

@app.route('/api/locrits/<locrit_name>/chat/stream', methods=['POST'])
@login_required
def api_chat_stream_with_locrit(locrit_name):
    """API pour chat en streaming avec un Locrit"""
    try:
        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Récupérer le message
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message vide'}), 400

        # Utiliser le service Ollama pour générer la réponse
        from src.services.ollama_service import get_ollama_service
        ollama_service = get_ollama_service()

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Préparer le prompt système
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

        def generate_stream():
            """Générateur pour le streaming"""
            try:
                # Utiliser le client Ollama synchrone avec streaming
                import ollama

                client = ollama.Client(host=ollama_service.base_url)

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": message})

                stream = client.chat(
                    model=model,
                    messages=messages,
                    stream=True
                )

                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        if content:
                            yield f"data: {json.dumps({'chunk': content, 'done': False})}\n\n"

                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                logger.error(f"Erreur lors du streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )

    except Exception as e:
        logger.error(f"Erreur dans l'API chat stream: {str(e)}")
        return jsonify({'error': str(e)}), 500


# API directe pour communication entre Locrits (sans authentification web)
@app.route('/api/v1/locrits', methods=['GET'])
def api_list_locrits():
    """API publique pour lister les Locrits disponibles"""
    try:
        locrits = config_service.list_locrits()
        locrits_info = []

        for locrit_name in locrits:
            settings = config_service.get_locrit_settings(locrit_name)
            if settings and settings.get('active', False):
                # Vérifier si le Locrit est ouvert aux autres Locrits
                open_to_locrits = settings.get('open_to', {}).get('locrits', False)
                if open_to_locrits:
                    locrits_info.append({
                        'name': locrit_name,
                        'description': settings.get('description', ''),
                        'model': settings.get('ollama_model', ''),
                        'public_address': settings.get('public_address'),
                        'capabilities': {
                            'chat': True,
                            'stream': True
                        }
                    })

        return jsonify({
            'success': True,
            'locrits': locrits_info,
            'count': len(locrits_info)
        })

    except Exception as e:
        logger.error(f"Erreur dans l'API list locrits: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/locrits/<locrit_name>/info', methods=['GET'])
def api_get_locrit_info(locrit_name):
    """API pour obtenir les informations d'un Locrit spécifique"""
    try:
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Vérifier si le Locrit est ouvert aux autres Locrits
        open_to_locrits = settings.get('open_to', {}).get('locrits', False)
        if not open_to_locrits:
            return jsonify({'error': 'Locrit non accessible aux autres Locrits'}), 403

        return jsonify({
            'success': True,
            'locrit': {
                'name': locrit_name,
                'description': settings.get('description', ''),
                'model': settings.get('ollama_model', ''),
                'public_address': settings.get('public_address'),
                'open_to': settings.get('open_to', {}),
                'access_to': settings.get('access_to', {}),
                'capabilities': {
                    'chat': True,
                    'stream': True
                }
            }
        })

    except Exception as e:
        logger.error(f"Erreur dans l'API get locrit info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/locrits/<locrit_name>/chat', methods=['POST'])
def api_v1_chat_with_locrit(locrit_name):
    """API publique pour chat avec un Locrit (pour communication inter-Locrits)"""
    try:
        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Vérifier si le Locrit est ouvert aux autres Locrits
        open_to_locrits = settings.get('open_to', {}).get('locrits', False)
        if not open_to_locrits:
            return jsonify({'error': 'Locrit non accessible aux autres Locrits'}), 403

        # Récupérer le message et les métadonnées
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message vide'}), 400

        # Métadonnées optionnelles pour le contexte
        sender_name = data.get('sender_name', 'Locrit externe')
        sender_type = data.get('sender_type', 'locrit')
        context = data.get('context', '')

        # Utiliser le service Ollama pour générer la réponse
        from src.services.ollama_service import get_ollama_service
        ollama_service = get_ollama_service()

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Préparer le prompt système enrichi avec le contexte
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"
        if sender_name and sender_type == 'locrit':
            system_prompt += f"\n\nTu es en train de communiquer avec {sender_name}, un autre Locrit."
        if context:
            system_prompt += f"\n\nContexte de la conversation: {context}"

        try:
            import asyncio
            ollama_service.current_model = model
            ollama_service.is_connected = True
            ollama_service.available_models = connection_test.get('models', [])

            response = asyncio.run(ollama_service.chat(message, system_prompt))

            # Log de la communication inter-Locrits
            logger.info(f"Communication inter-Locrits: {sender_name} -> {locrit_name}")

            return jsonify({
                'success': True,
                'response': response,
                'locrit_name': locrit_name,
                'model': model,
                'timestamp': datetime.now().isoformat(),
                'sender_acknowledged': sender_name
            })

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return jsonify({'error': f'Erreur de génération: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Erreur dans l'API v1 chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/locrits/<locrit_name>/chat/stream', methods=['POST'])
def api_v1_chat_stream_with_locrit(locrit_name):
    """API publique pour chat en streaming avec un Locrit (pour communication inter-Locrits)"""
    try:
        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Vérifier si le Locrit est ouvert aux autres Locrits
        open_to_locrits = settings.get('open_to', {}).get('locrits', False)
        if not open_to_locrits:
            return jsonify({'error': 'Locrit non accessible aux autres Locrits'}), 403

        # Récupérer le message et les métadonnées
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message vide'}), 400

        # Métadonnées optionnelles
        sender_name = data.get('sender_name', 'Locrit externe')
        sender_type = data.get('sender_type', 'locrit')
        context = data.get('context', '')

        # Utiliser le service Ollama pour générer la réponse
        from src.services.ollama_service import get_ollama_service
        ollama_service = get_ollama_service()

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Préparer le prompt système enrichi
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"
        if sender_name and sender_type == 'locrit':
            system_prompt += f"\n\nTu es en train de communiquer avec {sender_name}, un autre Locrit."
        if context:
            system_prompt += f"\n\nContexte de la conversation: {context}"

        def generate_stream():
            """Générateur pour le streaming"""
            try:
                # Log de la communication inter-Locrits
                logger.info(f"Communication inter-Locrits (streaming): {sender_name} -> {locrit_name}")

                # Utiliser le client Ollama synchrone avec streaming
                import ollama

                client = ollama.Client(host=ollama_service.base_url)

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": message})

                stream = client.chat(
                    model=model,
                    messages=messages,
                    stream=True
                )

                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        if content:
                            yield f"data: {json.dumps({'chunk': content, 'done': False, 'locrit_name': locrit_name, 'timestamp': datetime.now().isoformat()})}\n\n"

                yield f"data: {json.dumps({'done': True, 'locrit_name': locrit_name, 'sender_acknowledged': sender_name})}\n\n"

            except Exception as e:
                logger.error(f"Erreur lors du streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )

    except Exception as e:
        logger.error(f"Erreur dans l'API v1 chat stream: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Endpoint pour tester la disponibilité de l'API
@app.route('/api/v1/ping', methods=['GET'])
def api_ping():
    """Endpoint de test pour vérifier que l'API est disponible"""
    return jsonify({
        'success': True,
        'message': 'Locrit API v1 is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html',
                         error_code=404,
                         error_message="Page non trouvée"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Erreur interne du serveur"), 500


if __name__ == '__main__':
    # Configuration pour le développement
    host = os.getenv('WEB_HOST', 'localhost')
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Démarrage de l'interface web sur http://{host}:{port}")
    print(f"🌐 Interface web Locrit démarrée sur http://{host}:{port}")

    app.run(host=host, port=port, debug=debug)