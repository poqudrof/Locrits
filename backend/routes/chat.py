"""
Chat routes for Locrit Web UI
"""

import asyncio
import json
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify, Response
from backend.middleware.auth import login_required
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

chat_bp = Blueprint('chat', __name__)

# Logger pour l'application web
logger = ui_logging_service.logger


@chat_bp.route('/locrits/<locrit_name>/chat')
@login_required
def chat_with_locrit(locrit_name):
    """Interface de chat avec un Locrit"""
    try:
        # Vérifier que le Locrit existe
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            flash(f'Locrit "{locrit_name}" non trouvé.', 'error')
            return redirect(url_for('dashboard.locrits_list'))

        return render_template('chat.html',
                             locrit_name=locrit_name,
                             locrit_settings=settings,
                             user_name=session.get('user_name'))

    except Exception as e:
        logger.error(f"Erreur lors du chargement du chat: {str(e)}")
        flash('Erreur lors du chargement du chat.', 'error')
        return redirect(url_for('dashboard.locrits_list'))


@chat_bp.route('/api/locrits/<locrit_name>/chat', methods=['POST'])
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


@chat_bp.route('/api/locrits/<locrit_name>/chat/stream', methods=['POST'])
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
                            yield f"data: {json.dumps({'chunk': content, 'done': False})}\\n\\n"

                yield f"data: {json.dumps({'done': True})}\\n\\n"

            except Exception as e:
                logger.error(f"Erreur lors du streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\\n\\n"

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