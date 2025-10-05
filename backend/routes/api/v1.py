"""
Public API v1 routes for inter-Locrit communication
"""

import asyncio
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

api_v1_bp = Blueprint('api_v1', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@api_v1_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Locrit API',
        'timestamp': datetime.now().isoformat()
    })


@api_v1_bp.route('/api/v1/ping', methods=['GET'])
def api_ping():
    """Endpoint de test pour vérifier que l'API est disponible"""
    return jsonify({
        'success': True,
        'message': 'Locrit API v1 is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@api_v1_bp.route('/api/v1/locrits', methods=['GET'])
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


@api_v1_bp.route('/api/v1/locrits/<locrit_name>/info', methods=['GET'])
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


@api_v1_bp.route('/api/v1/locrits/<locrit_name>/chat', methods=['POST'])
async def api_v1_chat_with_locrit(locrit_name):
    """
    API publique pour chat avec un Locrit (pour communication inter-Locrits et API externe).
    Supporte deux modes:
    1. Avec conversation_id: utilise le service de conversation (contexte géré côté serveur)
    2. Sans conversation_id: mode legacy (pour compatibilité descendante)
    """
    try:
        # Récupérer le message et les métadonnées
        data = request.get_json(force=True)
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message vide'}), 400

        conversation_id = data.get('conversation_id')

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

            # Log de la communication inter-Locrits
            logger.info(f"API v1 conversation: {conversation_id} -> {locrit_name}")

            return jsonify(result)

        # Mode legacy - sans conversation_id (pour compatibilité descendante)
        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            return jsonify({'error': 'Locrit inactif'}), 400

        # Vérifier si le Locrit est ouvert aux humains (pour le chat web)
        open_to_humans = settings.get('open_to', {}).get('humans', False)
        if not open_to_humans:
            logger.warning(f"Accès non autorisé pour {locrit_name} (ouvert aux humains: {open_to_humans})")
            return jsonify({'error': 'Locrit non accessible depuis le web'}), 403

        # Métadonnées optionnelles pour le contexte
        sender_name = data.get('sender_name', 'Locrit externe')
        sender_type = data.get('sender_type', 'locrit')
        context = data.get('context', '')

        # Utiliser le service Ollama pour générer la réponse
        from src.services.ollama_service import get_ollama_service_for_locrit

        try:
            ollama_service = get_ollama_service_for_locrit(locrit_name)
        except (ValueError, Exception) as e:
            logger.error(f"Failed to get Ollama service for {locrit_name}: {e}")
            return jsonify({'error': f'Service Ollama non disponible: {str(e)}'}), 503

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible - connexion échouée'}), 503

        # Préparer le prompt système enrichi avec le contexte
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"
        if sender_name and sender_type == 'locrit':
            system_prompt += f"\\n\\nTu es en train de communiquer avec {sender_name}, un autre Locrit."
        if context:
            system_prompt += f"\\n\\nContexte de la conversation: {context}"

        try:
            ollama_service.current_model = model
            ollama_service.is_connected = True
            ollama_service.available_models = connection_test.get('models', [])

            # Utiliser nest_asyncio pour permettre asyncio.run dans Flask
            import nest_asyncio
            nest_asyncio.apply()

            response = asyncio.run(ollama_service.chat(message, system_prompt))

            # Log de la communication inter-Locrits
            logger.info(f"Communication inter-Locrits: {sender_name} -> {locrit_name}")

            return jsonify({
                'success': True,
                'response': response,
                'locrit_name': locrit_name,
                'model': model,
                'timestamp': datetime.now().isoformat(),
                'sender_acknowledged': sender_name,
                'mode': 'legacy'
            })

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return jsonify({'error': f'Erreur de génération: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Erreur dans l'API v1 chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

