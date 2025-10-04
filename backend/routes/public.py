"""
Routes publiques pour les pages personnelles des Locrits
Permet aux visiteurs d'interagir avec un Locrit si celui-ci est ouvert à Internet
"""

import json
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

public_bp = Blueprint('public', __name__)
logger = ui_logging_service.logger


@public_bp.route('/public/<locrit_name>', methods=['GET'])
def get_locrit_public_page(locrit_name):
    """
    Affiche la page publique d'un Locrit
    Accessible uniquement si le Locrit a open_to.internet = True
    """
    try:
        # Récupérer les paramètres du Locrit
        settings = config_service.get_locrit_settings(locrit_name)

        if not settings:
            return jsonify({
                'success': False,
                'error': 'Locrit introuvable'
            }), 404

        # Vérifier si le Locrit est actif
        if not settings.get('active', False):
            return jsonify({
                'success': False,
                'error': 'Ce Locrit n\'est pas actif pour le moment'
            }), 403

        # Vérifier si le Locrit est ouvert à Internet
        open_to_internet = settings.get('open_to', {}).get('internet', False)

        if not open_to_internet:
            return jsonify({
                'success': False,
                'error': 'Ce Locrit n\'est pas accessible publiquement'
            }), 403

        # Récupérer la configuration de la page personnelle (si elle existe)
        page_config = settings.get('public_page', {
            'title': f'Parlez avec {locrit_name}',
            'description': settings.get('description', 'Un Locrit intelligent'),
            'welcome_message': f'Bonjour ! Je suis {locrit_name}. Comment puis-je vous aider ?',
            'theme': 'default',
            'avatar': '🤖'
        })

        # Retourner les informations publiques du Locrit
        return jsonify({
            'success': True,
            'locrit': {
                'name': locrit_name,
                'description': settings.get('description', ''),
                'model': settings.get('ollama_model', ''),
                'public_address': settings.get('public_address'),
                'page_config': page_config,
                'active': settings.get('active', False)
            }
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la page publique de {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@public_bp.route('/public/<locrit_name>/chat', methods=['POST'])
async def chat_with_locrit_public(locrit_name):
    """
    Permet de discuter avec un Locrit via son interface publique.
    Supporte deux modes:
    1. Avec conversation_id: utilise le service de conversation (contexte géré côté serveur)
    2. Sans conversation_id: mode legacy (pas de contexte entre messages)
    """
    try:
        # Récupérer les données de la requête
        data = request.get_json()
        visitor_name = data.get('visitor_name', 'Visiteur')
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')

        if not message:
            return jsonify({
                'success': False,
                'error': 'Le message ne peut pas être vide'
            }), 400

        # Si conversation_id est fourni, utiliser le service de conversation
        if conversation_id:
            from src.services.conversation_service import conversation_service

            result = await conversation_service.send_message(
                conversation_id=conversation_id,
                message=message,
                save_to_memory=True
            )

            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                status_code = 404 if 'not found' in error_msg.lower() else 500
                return jsonify(result), status_code

            logger.info(f"Public conversation: {conversation_id} -> {locrit_name} by {visitor_name}")
            return jsonify(result)

        # Mode legacy - sans contexte

        # Récupérer les paramètres du Locrit
        settings = config_service.get_locrit_settings(locrit_name)

        if not settings:
            return jsonify({
                'success': False,
                'error': 'Locrit introuvable'
            }), 404

        # Vérifier si le Locrit est actif
        if not settings.get('active', False):
            return jsonify({
                'success': False,
                'error': 'Ce Locrit n\'est pas actif pour le moment'
            }), 403

        # Vérifier si le Locrit est ouvert à Internet
        open_to_internet = settings.get('open_to', {}).get('internet', False)

        if not open_to_internet:
            return jsonify({
                'success': False,
                'error': 'Ce Locrit n\'est pas accessible publiquement'
            }), 403

        # Logger la tentative de conversation publique
        logger.info(f"Conversation publique avec {locrit_name} - Visiteur: {visitor_name}")

        # Construire le contexte du message pour indiquer que c'est une conversation publique
        context_message = f"[Conversation publique avec {visitor_name} via l'interface web]\n{message}"

        # Utiliser le service Ollama directement
        from src.services.ollama_service import get_ollama_service_for_locrit
        import nest_asyncio

        try:
            ollama_service = get_ollama_service_for_locrit(locrit_name)
        except (ValueError, Exception) as e:
            logger.error(f"Failed to get Ollama service for {locrit_name}: {e}")
            return jsonify({
                'success': False,
                'error': f'Service Ollama non disponible: {str(e)}'
            }), 503

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({
                'success': False,
                'error': 'Aucun modèle configuré pour ce Locrit'
            }), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({
                'success': False,
                'error': 'Service Ollama non disponible - connexion échouée'
            }), 503

        # Préparer le prompt système
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"
        system_prompt += f"\n\nTu es en train de communiquer avec {visitor_name}, un visiteur humain sur ton interface web publique."

        try:
            ollama_service.current_model = model
            ollama_service.is_connected = True
            ollama_service.available_models = connection_test.get('models', [])

            # Utiliser nest_asyncio pour permettre asyncio.run dans Flask
            nest_asyncio.apply()
            response = asyncio.run(ollama_service.chat(context_message, system_prompt, locrit_name))

            logger.info(f"Réponse générée pour {visitor_name} par {locrit_name}")

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Erreur de génération: {str(e)}'
            }), 500

        return jsonify({
            'success': True,
            'response': response,
            'locrit_name': locrit_name,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Erreur lors du chat public avec {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'envoi du message'
        }), 500


@public_bp.route('/public/<locrit_name>/settings', methods=['PUT'])
def update_locrit_public_page(locrit_name):
    """
    Permet au propriétaire du Locrit de personnaliser sa page publique
    Nécessite une authentification (à implémenter)
    """
    try:
        # TODO: Ajouter une vérification d'authentification
        # Pour l'instant, accessible sans authentification (à sécuriser)

        data = request.get_json()
        page_config = data.get('page_config', {})

        # Récupérer les paramètres actuels du Locrit
        settings = config_service.get_locrit_settings(locrit_name)

        if not settings:
            return jsonify({
                'success': False,
                'error': 'Locrit introuvable'
            }), 404

        # Mettre à jour la configuration de la page publique
        settings['public_page'] = {
            'title': page_config.get('title', f'Parlez avec {locrit_name}'),
            'description': page_config.get('description', settings.get('description', '')),
            'welcome_message': page_config.get('welcome_message', f'Bonjour ! Je suis {locrit_name}.'),
            'theme': page_config.get('theme', 'default'),
            'avatar': page_config.get('avatar', '🤖'),
            'custom_css': page_config.get('custom_css', ''),
            'show_model_info': page_config.get('show_model_info', False)
        }

        # Sauvegarder la configuration
        config_service.update_locrit_settings(locrit_name, settings)

        logger.info(f"Page publique de {locrit_name} mise à jour")

        return jsonify({
            'success': True,
            'message': 'Page publique mise à jour',
            'page_config': settings['public_page']
        })

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la page publique de {locrit_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la mise à jour'
        }), 500


@public_bp.route('/public/list', methods=['GET'])
def list_public_locrits():
    """
    Liste tous les Locrits accessibles publiquement
    """
    try:
        locrits = config_service.list_locrits()
        public_locrits = []

        for locrit_name in locrits:
            settings = config_service.get_locrit_settings(locrit_name)

            if settings and settings.get('active', False):
                # Vérifier si le Locrit est ouvert à Internet
                open_to_internet = settings.get('open_to', {}).get('internet', False)

                if open_to_internet:
                    page_config = settings.get('public_page', {
                        'title': f'Parlez avec {locrit_name}',
                        'description': settings.get('description', ''),
                        'avatar': '🤖'
                    })

                    public_locrits.append({
                        'name': locrit_name,
                        'description': settings.get('description', ''),
                        'public_address': settings.get('public_address'),
                        'avatar': page_config.get('avatar', '🤖'),
                        'title': page_config.get('title', f'Parlez avec {locrit_name}')
                    })

        return jsonify({
            'success': True,
            'locrits': public_locrits,
            'count': len(public_locrits)
        })

    except Exception as e:
        logger.error(f"Erreur lors de la liste des Locrits publics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500
