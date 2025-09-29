"""
Chat routes for Locrit Web UI
"""

import asyncio
import json
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify, Response
from backend.middleware.auth import login_required
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service
from src.services.comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler

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
async def api_chat_with_locrit(locrit_name):
    """API pour envoyer un message à un Locrit"""
    try:
        # Start operation tracking
        operation_id = comprehensive_logger.start_operation(f"api_chat_{locrit_name}")

        # Vérifier que le Locrit existe et est actif
        settings = config_service.get_locrit_settings(locrit_name)
        if not settings:
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                status_code=404,
                error="Locrit not found"
            )
            return jsonify({'error': 'Locrit non trouvé'}), 404

        if not settings.get('active', False):
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                status_code=400,
                error="Locrit inactive"
            )
            return jsonify({'error': 'Locrit inactif'}), 400

        # Récupérer le message
        data = request.get_json()
        if not data or 'message' not in data:
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                status_code=400,
                error="Message required"
            )
            return jsonify({'error': 'Message requis'}), 400

        message = data['message'].strip()
        if not message:
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                status_code=400,
                error="Empty message"
            )
            return jsonify({'error': 'Message vide'}), 400

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Utiliser LangChain avec ChatOllama
        from src.services.ollama_service import get_ollama_service
        from src.services.memory_manager_service import memory_manager
        ollama_service = get_ollama_service()

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Sauvegarder le message utilisateur dans la mémoire du Locrit
        user_id = session.get('user_name', 'web_user') if 'user_name' in session else 'anonymous_user'
        session_id = f"web_{user_id}_{locrit_name}"

        try:
            # Sauvegarder le message utilisateur
            asyncio.run(memory_manager.save_message(
                locrit_name=locrit_name,
                role="user",
                content=message,
                session_id=session_id,
                user_id=user_id
            ))
        except Exception as e:
            logger.warning(f"Erreur sauvegarde message utilisateur: {e}")

        # Préparer le prompt système basé sur la description du Locrit
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

        try:
            # Récupérer l'historique de conversation depuis la mémoire Kuzu
            conversation_history = []
            try:
                # Récupérer les derniers messages de cette session (limite à 20 pour éviter de surcharger le contexte)
                history_messages = asyncio.run(memory_manager.get_conversation_history(
                    locrit_name=locrit_name,
                    session_id=session_id,
                    limit=20
                ))

                # Convertir l'historique en messages LangChain
                for msg in history_messages:
                    if msg.get('role') == 'user':
                        conversation_history.append(HumanMessage(content=msg.get('content', '')))
                    elif msg.get('role') == 'assistant':
                        conversation_history.append(AIMessage(content=msg.get('content', '')))

            except Exception as e:
                logger.warning(f"Erreur récupération historique conversation: {e}")
                # Continuer sans historique si la récupération échoue

            # Use the Ollama service directly with proper Locrit context
            response = await ollama_service.chat(
                message=message,
                system_prompt=system_prompt,
                locrit_name=locrit_name
            )

            # Sauvegarder la réponse dans la mémoire du Locrit
            try:
                asyncio.run(memory_manager.save_message(
                    locrit_name=locrit_name,
                    role="assistant",
                    content=response.content,
                    session_id=session_id,
                    user_id=user_id
                ))
            except Exception as e:
                logger.warning(f"Erreur sauvegarde réponse: {e}")

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log successful API request
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                duration_ms=duration_ms,
                status_code=200,
                data={
                    "model": model,
                    "message_length": len(message),
                    "response_length": len(response.content)
                }
            )

            return jsonify({
                'success': True,
                'response': response.content,
                'locrit_name': locrit_name,
                'model': model
            })

        except Exception as e:
            # End operation tracking for failed request
            duration_ms = comprehensive_logger.end_operation(operation_id)

            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")

            # Log failed API request
            comprehensive_logger.log_api_request(
                endpoint=f"/api/locrits/{locrit_name}/chat",
                method="POST",
                locrit_name=locrit_name,
                duration_ms=duration_ms,
                status_code=500,
                error=str(e)
            )

            return jsonify({'error': f'Erreur de génération: {str(e)}'}), 500

    except Exception as e:
        # End operation tracking for failed request
        if 'operation_id' in locals():
            duration_ms = comprehensive_logger.end_operation(operation_id)

        logger.error(f"Erreur dans l'API chat: {str(e)}")

        # Log failed API request
        comprehensive_logger.log_api_request(
            endpoint=f"/api/locrits/{locrit_name}/chat",
            method="POST",
            locrit_name=locrit_name,
            status_code=500,
            error=str(e)
        )

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

        # Configurer le modèle du Locrit
        model = settings.get('ollama_model')
        if not model:
            return jsonify({'error': 'Aucun modèle configuré pour ce Locrit'}), 400

        # Utiliser LangChain avec ChatOllama
        from src.services.ollama_service import get_ollama_service
        ollama_service = get_ollama_service()

        # Test de connexion
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({'error': 'Service Ollama non disponible'}), 500

        # Préparer le prompt système
        system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

        def generate_stream():
            """Générateur pour le streaming avec LangChain"""
            try:
                # Classe de callback personnalisée pour le streaming
                class StreamingCallback:
                    def __init__(self):
                        self.tokens = []

                    def on_llm_new_token(self, token: str, **kwargs) -> None:
                        self.tokens.append(token)

                # Initialiser ChatOllama avec LangChain
                chat_model = ChatOllama(
                    model=model,
                    base_url=ollama_service.base_url,
                    temperature=0.7
                )

                # Préparer les messages
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message)
                ]

                # Streamer avec LangChain
                for chunk in chat_model.stream(messages):
                    if chunk.content:
                        yield f"data: {json.dumps({'chunk': chunk.content, 'done': False})}\\n\\n"

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