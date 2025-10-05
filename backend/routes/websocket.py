"""
WebSocket routes for real-time chat communication
"""

import json
import asyncio
from datetime import datetime
from flask import session
from flask_socketio import Namespace, emit, join_room, leave_room
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service
from src.services.memory_manager_service import memory_manager
from src.services.comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory

# Logger pour l'application web
logger = ui_logging_service.logger


class ChatNamespace(Namespace):
    """Namespace for chat WebSocket events"""

    def on_connect(self):
        """Handle client connection"""
        logger.debug(f"Client connected to chat namespace")

        # Log WebSocket connection (reduced verbosity)
        # comprehensive_logger.log_websocket_event(
        #     event_type="connect",
        #     data={"namespace": "chat"}
        # )

        emit('connected', {'status': 'connected'})

    def on_disconnect(self):
        """Handle client disconnection"""
        logger.debug(f"Client disconnected from chat namespace")

        # Log WebSocket disconnection (reduced verbosity)
        # comprehensive_logger.log_websocket_event(
        #     event_type="disconnect",
        #     data={"namespace": "chat"}
        # )

    def on_join_chat(self, data):
        """Handle joining a chat room for a specific Locrit and session"""
        locrit_name = data.get('locrit_name')
        session_id = data.get('session_id')

        if locrit_name and session_id:
            # Create unique room for this conversation session
            room = f"chat_{locrit_name}_{session_id}"
            join_room(room)
            logger.debug(f"Client joined chat room: {room}")

            # Log WebSocket join chat event (reduced verbosity)
            # comprehensive_logger.log_websocket_event(
            #     event_type="join_chat",
            #     locrit_name=locrit_name,
            #     session_id=session_id,
            #     data={"room": room}
            # )

            emit('joined_chat', {
                'locrit_name': locrit_name,
                'session_id': session_id,
                'room': room
            })
        else:
            # Log failed join chat attempt
            comprehensive_logger.log_websocket_event(
                event_type="join_chat_failed",
                data={"reason": "Missing locrit_name or session_id"}
            )

            emit('error', {'message': 'Locrit name and session ID required'})

    def on_leave_chat(self, data):
        """Handle leaving a chat room"""
        locrit_name = data.get('locrit_name')
        session_id = data.get('session_id')
        if locrit_name and session_id:
            room = f"chat_{locrit_name}_{session_id}"
            leave_room(room)
            logger.info(f"Client left chat room: {room}")

            # Log WebSocket leave chat event
            comprehensive_logger.log_websocket_event(
                event_type="leave_chat",
                locrit_name=locrit_name,
                session_id=session_id,
                data={"room": room}
            )

            emit('left_chat', {'locrit_name': locrit_name, 'session_id': session_id})

    def on_chat_message(self, data):
        """
        Handle sending a message to a Locrit.
        Supporte deux modes:
        1. Avec conversation_id: utilise le service de conversation (contexte géré côté serveur)
        2. Sans conversation_id mais avec session_id: mode legacy (pour compatibilité descendante)
        """
        try:
            locrit_name = data.get('locrit_name')
            session_id = data.get('session_id')
            conversation_id = data.get('conversation_id')
            message = data.get('message', '').strip()
            stream = data.get('stream', False)

            if not locrit_name or not message:
                emit('error', {'message': 'Locrit name and message required'})
                return

            if not conversation_id and not session_id:
                emit('error', {'message': 'Either conversation_id or session_id is required'})
                return

            # Si conversation_id est fourni, utiliser le service de conversation
            if conversation_id:
                from src.services.conversation_service import conversation_service

                # Use conversation service (no streaming support yet in conversation service)
                async def send_with_conversation():
                    result = await conversation_service.send_message(
                        conversation_id=conversation_id,
                        message=message,
                        save_to_memory=True
                    )
                    return result

                result = asyncio.run(send_with_conversation())

                if not result.get('success'):
                    emit('error', {
                        'locrit_name': locrit_name,
                        'conversation_id': conversation_id,
                        'message': result.get('error', 'Unknown error')
                    })
                    return

                # Send the complete response (no streaming with conversation service)
                emit('chat_response', {
                    'locrit_name': locrit_name,
                    'conversation_id': conversation_id,
                    'response': result.get('response', ''),
                    'timestamp': result.get('timestamp', datetime.now().isoformat()),
                    'message_count': result.get('message_count', 0)
                })

                logger.info(f"WebSocket conversation message: {conversation_id} -> {locrit_name}")
                return

            # Mode legacy - utiliser session_id
            # Verify Locrit exists and is active
            settings = config_service.get_locrit_settings(locrit_name)
            if not settings:
                emit('error', {'message': 'Locrit not found'})
                return


            # Check if Locrit is open to humans (for web UI)
            open_to_humans = settings.get('open_to', {}).get('humans', False)
            if not open_to_humans:
                emit('error', {'message': 'Locrit not accessible for humans'})
                return

            # Get Ollama service
            from src.services.ollama_service import get_ollama_service_for_locrit

            try:
                ollama_service = get_ollama_service_for_locrit(locrit_name)
            except (ValueError, Exception) as e:
                logger.error(f"Failed to get Ollama service for {locrit_name}: {e}")
                emit('error', {'message': f'Ollama service unavailable: {str(e)}'})
                return

            # Configure model
            model = settings.get('ollama_model')
            if not model:
                emit('error', {'message': 'No model configured for this Locrit'})
                return

            # Test connection
            connection_test = ollama_service.test_connection()
            if not connection_test.get('success'):
                emit('error', {'message': 'Ollama service unavailable - connection failed'})
                return

            # Set up user ID for memory (use session_id from frontend)
            user_id = session.get('user_name', 'web_user') if 'user_name' in session else 'websocket_user'
            # Use the session_id provided by the frontend to maintain conversation context

            # Save user message to memory
            try:
                # Use asyncio.create_task in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(memory_manager.save_message(
                    locrit_name=locrit_name,
                    role="user",
                    content=message,
                    session_id=session_id,
                    user_id=user_id
                ))
                loop.close()
            except Exception as e:
                logger.warning(f"Error saving user message to memory: {e}")

            # Prepare system prompt
            system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

            logger.info(f"Processing chat message for {locrit_name} using model {model}")

            # Retrieve conversation history from memory
            conversation_history = []
            try:
                # Get last 20 messages for context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                history_messages = loop.run_until_complete(memory_manager.get_conversation_history(
                    locrit_name=locrit_name,
                    session_id=session_id,
                    limit=20
                ))
                loop.close()

                # Convert to Ollama format
                for msg in history_messages:
                    if msg.get('role') == 'user':
                        conversation_history.append({"role": "user", "content": msg.get('content', '')})
                    elif msg.get('role') == 'assistant':
                        conversation_history.append({"role": "assistant", "content": msg.get('content', '')})

            except Exception as e:
                logger.warning(f"Error retrieving conversation history: {e}")

            # Stream the response
            try:
                import ollama

                client = ollama.Client(host=ollama_service.base_url)

                # Build messages with conversation context
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                # Add conversation history
                messages.extend(conversation_history)

                # Add current user message
                messages.append({"role": "user", "content": message})

                stream = client.chat(
                    model=model,
                    messages=messages,
                    stream=True
                )

                # Send chunks to the client and collect full response
                full_response = ""
                if stream:
                    for chunk in stream:
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            if content:
                                full_response += content
                                emit('chat_chunk', {
                                    'locrit_name': locrit_name,
                                    'session_id': session_id,
                                    'content': content,
                                    'timestamp': datetime.now().isoformat()
                                })

                    # Save assistant response to memory
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(memory_manager.save_message(
                            locrit_name=locrit_name,
                            role="assistant",
                            content=full_response,
                            session_id=session_id,
                            user_id=user_id
                        ))
                        loop.close()
                    except Exception as e:
                        logger.warning(f"Error saving assistant response to memory: {e}")

                    # Send completion signal
                    emit('chat_complete', {
                        'locrit_name': locrit_name,
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Handle non-streaming response
                    full_response = "".join(
                        chunk['message']['content'] for chunk in stream if 'message' in chunk and 'content' in chunk['message']
                    )

                    # Save assistant response to memory
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(memory_manager.save_message(
                            locrit_name=locrit_name,
                            role="assistant",
                            content=full_response,
                            session_id=session_id,
                            user_id=user_id
                        ))
                        loop.close()
                    except Exception as e:
                        logger.warning(f"Error saving assistant response to memory: {e}")

                    emit('chat_response', {
                        'locrit_name': locrit_name,
                        'session_id': session_id,
                        'response': full_response,
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error streaming chat response: {str(e)}")
                emit('error', {
                    'locrit_name': locrit_name,
                    'session_id': session_id,
                    'message': f'Error generating response: {str(e)}'
                })

        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            emit('error', {'message': str(e)})


# Create the chat namespace instance
chat_namespace = ChatNamespace('/')