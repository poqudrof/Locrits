"""
Configuration routes for Locrit Web UI
"""

import requests
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from backend.middleware.auth import login_required
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

config_bp = Blueprint('config', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@config_bp.route('/config')
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


@config_bp.route('/api/ollama/models', methods=['GET', 'POST'])
def ollama_models():
    """API pour récupérer la liste des modèles Ollama disponibles"""
    try:
        # Récupérer l'URL depuis la requête ou la configuration
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
            ollama_url = data.get('ollama_url') or data.get('base_url')
            logger.info(f"URL Ollama reçue dans la requête: {ollama_url}")
        else:
            # GET request ou pas de données JSON - utiliser query param ou config
            ollama_url = request.args.get('ollama_url')
            logger.info(f"URL Ollama depuis query param: {ollama_url}")

        if not ollama_url:
            # Fallback vers la configuration
            ollama_url = config_service.get('ollama.base_url', 'http://localhost:11434')
            logger.info(f"Utilisation de la config par défaut: {ollama_url}")

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


@config_bp.route('/api/ollama/status', methods=['GET'])
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


@config_bp.route('/config/test-ollama', methods=['POST'])
def test_ollama_connection():
    """Test la connexion au serveur Ollama côté serveur"""
    try:
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


@config_bp.route('/api/config', methods=['GET'])
def get_config_api():
    """API pour récupérer la configuration actuelle"""
    try:
        config_data = {
            'ollama': config_service.get_ollama_config(),
            'network': config_service.get_network_config(),
            'memory': config_service.get_memory_config(),
            'ui': config_service.get_ui_config()
        }

        return jsonify({
            'success': True,
            'config': config_data
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de la configuration',
            'details': str(e)
        }), 500


@config_bp.route('/api/config/save', methods=['POST'])
def save_config_api():
    """API pour sauvegarder la configuration (JSON only)"""
    try:
        # Récupérer les données JSON
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400

        form_data = request.get_json()
        logger.info(f"Sauvegarde configuration API: {form_data}")

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
            logger.info("Configuration mise à jour via API")
            return jsonify({
                'success': True,
                'message': 'Configuration sauvegardée avec succès !'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde de la configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde via API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la sauvegarde de la configuration.',
            'details': str(e)
        }), 500


@config_bp.route('/config/save', methods=['POST'])
def save_config():
    """Sauvegarde la configuration de l'application"""
    try:
        # Récupérer les données du formulaire ou JSON
        if request.is_json:
            form_data = request.get_json()
            logger.info(f"Données JSON reçues: {form_data}")
        else:
            form_data = request.form.to_dict()
            logger.info(f"Données de formulaire reçues: {form_data}")

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
            message = 'Configuration sauvegardée avec succès !'

            # Réponse différente selon le type de requête
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                flash(message, 'success')
                return redirect(url_for('config.app_config'))
        else:
            error_msg = 'Erreur lors de la sauvegarde de la configuration.'

            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500
            else:
                flash(error_msg, 'error')
                return redirect(url_for('config.app_config'))

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
        error_msg = 'Erreur lors de la sauvegarde de la configuration.'

        if request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg,
                'details': str(e)
            }), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('config.app_config'))


@config_bp.route('/api/locrits', methods=['GET'])
def get_locrits_config():
    """API pour récupérer la configuration des Locrits"""
    try:
        locrits_config = config_service.get_locrits_config()

        return jsonify({
            'success': True,
            'locrits': locrits_config
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration des Locrits: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de la configuration des Locrits',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/config', methods=['GET'])
def get_locrit_config(locrit_name):
    """API pour récupérer la configuration d'un Locrit spécifique"""
    try:
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé'
            }), 404

        return jsonify({
            'success': True,
            'settings': settings
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration du Locrit {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de la configuration du Locrit',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/config', methods=['PUT'])
def update_locrit_config(locrit_name):
    """API pour mettre à jour la configuration d'un Locrit"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400

        settings = request.get_json()
        logger.info(f"Mise à jour configuration Locrit {locrit_name}: {settings}")

        # Récupérer les settings actuels
        current_settings = config_service.get_locrit_settings(locrit_name)
        if not current_settings:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé'
            }), 404

        # Mettre à jour les settings
        current_settings.update({
            'description': settings.get('description', current_settings.get('description', '')),
            'ollama_model': settings.get('ollama_model', current_settings.get('ollama_model', '')),
            'public_address': settings.get('public_address', current_settings.get('public_address', '')),
            'open_to': settings.get('open_to', current_settings.get('open_to', {})),
            'access_to': settings.get('access_to', current_settings.get('access_to', {})),
            'active': settings.get('active', current_settings.get('active', False)),
            'updated_at': datetime.now().isoformat()
        })

        # Sauvegarder
        config_service.update_locrit_settings(locrit_name, current_settings)
        success = config_service.save_config()

        if success:
            logger.info(f"Configuration Locrit mise à jour via API: {locrit_name}")
            return jsonify({
                'success': True,
                'message': f'Configuration du Locrit "{locrit_name}" sauvegardée avec succès !',
                'settings': current_settings
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde de la configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la configuration du Locrit {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la mise à jour de la configuration du Locrit.',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/toggle-edit', methods=['POST'])
def toggle_locrit_edit(locrit_name):
    """API pour activer/désactiver les permissions d'édition d'un Locrit"""
    try:
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé'
            }), 404

        # Inverser les permissions d'accès aux logs et mémoire complète
        access_to = settings.get('access_to', {})
        access_to['logs'] = not access_to.get('logs', False)
        access_to['full_memory'] = not access_to.get('full_memory', False)

        settings.update({
            'access_to': access_to,
            'updated_at': datetime.now().isoformat()
        })

        # Sauvegarder
        config_service.update_locrit_settings(locrit_name, settings)
        success = config_service.save_config()

        if success:
            edit_enabled = access_to.get('logs', False) and access_to.get('full_memory', False)
            status = "édition activée" if edit_enabled else "édition désactivée"
            logger.info(f"Permissions d'{status} pour le Locrit: {locrit_name}")
            return jsonify({
                'success': True,
                'edit_enabled': edit_enabled,
                'access_to': access_to,
                'message': f'Édition {status} pour le Locrit "{locrit_name}"'
            })
        else:
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500

    except Exception as e:
        logger.error(f"Erreur lors du toggle des permissions d'édition du Locrit {locrit_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/api/test-create', methods=['POST'])
def test_create_api():
    """Test endpoint to verify route registration"""
    try:
        return jsonify({
            'success': True,
            'message': 'Test endpoint working'
        })
    except Exception as e:
        logger.error(f"Erreur test endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/api/create-locrit', methods=['POST'])
def create_locrit_api():
    """API pour créer un nouveau Locrit"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400

        data = request.get_json()
        logger.info(f"Création nouveau Locrit via API: {data}")

        # Récupérer les données
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        model = data.get('model', '').strip()
        public_address = data.get('public_address', '').strip()

        # Validation
        if not name:
            return jsonify({
                'success': False,
                'error': 'Le nom du Locrit est obligatoire'
            }), 400

        if not description:
            return jsonify({
                'success': False,
                'error': 'La description est obligatoire'
            }), 400

        if not model:
            return jsonify({
                'success': False,
                'error': 'Le modèle Ollama est obligatoire'
            }), 400

        # Vérifier que le nom n'existe pas déjà
        existing_locrits = config_service.list_locrits()
        if name in existing_locrits:
            return jsonify({
                'success': False,
                'error': f'Un Locrit avec le nom "{name}" existe déjà'
            }), 400

        # Paramètres open_to
        open_to = {
            'humans': data.get('humans', True),
            'locrits': data.get('locrits', True),
            'invitations': data.get('invitations', True),
            'internet': data.get('internet', False),
            'platform': data.get('platform', False)
        }

        # Paramètres access_to
        access_to = {
            'logs': data.get('logs', True),
            'quick_memory': data.get('quick_memory', True),
            'full_memory': data.get('full_memory', False),
            'llm_info': data.get('llm_info', True)
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
            logger.info(f"Nouveau Locrit créé via API: {name}")
            return jsonify({
                'success': True,
                'message': f'Locrit "{name}" créé avec succès !',
                'locrit': {
                    'name': name,
                    'settings': settings
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde de la configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Erreur lors de la création du Locrit via API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la création du Locrit.',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/rename', methods=['POST'])
def rename_locrit_api(locrit_name):
    """API pour renommer un Locrit"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400

        data = request.get_json()
        logger.info(f"Renommage du Locrit {locrit_name} vers: {data}")

        # Récupérer le nouveau nom
        new_name = data.get('new_name', '').strip()

        # Validation
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'Le nouveau nom du Locrit est obligatoire'
            }), 400

        if new_name == locrit_name:
            return jsonify({
                'success': False,
                'error': 'Le nouveau nom doit être différent de l\'ancien'
            }), 400

        # Vérifier que le nouveau nom n'existe pas déjà
        existing_locrits = config_service.list_locrits()
        if new_name in existing_locrits:
            return jsonify({
                'success': False,
                'error': f'Un Locrit avec le nom "{new_name}" existe déjà'
            }), 400

        # Récupérer les settings actuels
        current_settings = config_service.get_locrit_settings(locrit_name)
        if not current_settings:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé'
            }), 404

        # Créer le nouveau Locrit avec le nouveau nom
        config_service.update_locrit_settings(new_name, current_settings)

        # Supprimer l'ancien Locrit
        success = config_service.delete_locrit(locrit_name)
        if not success:
            # Rollback: supprimer le nouveau si l'ancien n'a pas pu être supprimé
            config_service.delete_locrit(new_name)
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la suppression de l\'ancien Locrit'
            }), 500

        # Sauvegarder la configuration
        config_saved = config_service.save_config()

        if config_saved:
            logger.info(f"Locrit renommé via API: {locrit_name} -> {new_name}")
            return jsonify({
                'success': True,
                'message': f'Locrit "{locrit_name}" renommé en "{new_name}" avec succès !',
                'old_name': locrit_name,
                'new_name': new_name
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde de la configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Erreur lors du renommage du Locrit {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du renommage du Locrit.',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/toggle', methods=['POST'])
def toggle_locrit_api(locrit_name):
    """API pour activer/désactiver un Locrit"""
    try:
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé'
            }), 404

        # Inverser le statut
        settings['active'] = not settings.get('active', False)
        settings['updated_at'] = datetime.now().isoformat()

        # Sauvegarder
        config_service.update_locrit_settings(locrit_name, settings)
        success = config_service.save_config()

        if success:
            status = "activé" if settings['active'] else "désactivé"
            logger.info(f"Locrit {status} via API: {locrit_name}")
            return jsonify({
                'success': True,
                'active': settings['active'],
                'message': f'Locrit "{locrit_name}" {status} !'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde de la configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Erreur lors du toggle du Locrit {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du changement de statut du Locrit.',
            'details': str(e)
        }), 500


@config_bp.route('/api/locrits/<locrit_name>/delete', methods=['POST'])
def delete_locrit_api(locrit_name):
    """API pour supprimer un Locrit"""
    try:
        logger.info(f"Suppression du Locrit via API: {locrit_name}")

        success = config_service.delete_locrit(locrit_name)
        if success:
            config_service.save_config()
            logger.info(f"Locrit supprimé via API: {locrit_name}")
            return jsonify({
                'success': True,
                'message': f'Locrit "{locrit_name}" supprimé avec succès !'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Locrit "{locrit_name}" non trouvé.'
            }), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du Locrit {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la suppression du Locrit.',
            'details': str(e)
        }), 500