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

# Logger pour l'application web
logger = ui_logging_service.logger


class ChatNamespace(Namespace):
    """Namespace for chat WebSocket events"""

    def on_connect(self):
        """Handle client connection"""
        logger.info(f"Client connected to chat namespace")
        emit('connected', {'status': 'connected'})

    def on_disconnect(self):
        """Handle client disconnection"""
        logger.info(f"Client disconnected from chat namespace")

    def on_join_chat(self, data):
        """Handle joining a chat room for a specific Locrit"""
        locrit_name = data.get('locrit_name')
        if locrit_name:
            room = f"chat_{locrit_name}"
            join_room(room)
            logger.info(f"Client joined chat room: {room}")
            emit('joined_chat', {'locrit_name': locrit_name})
        else:
            emit('error', {'message': 'Locrit name required'})

    def on_leave_chat(self, data):
        """Handle leaving a chat room"""
        locrit_name = data.get('locrit_name')
        if locrit_name:
            room = f"chat_{locrit_name}"
            leave_room(room)
            logger.info(f"Client left chat room: {room}")
            emit('left_chat', {'locrit_name': locrit_name})

    def on_chat_message(self, data):
        """Handle sending a message to a Locrit"""
        try:
            locrit_name = data.get('locrit_name')
            message = data.get('message', '').strip()
            stream = data.get('stream', False)

            if not locrit_name or not message:
                emit('error', {'message': 'Locrit name and message required'})
                return

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
            from src.services.ollama_service import get_ollama_service
            ollama_service = get_ollama_service()

            # Configure model
            model = settings.get('ollama_model')
            if not model:
                emit('error', {'message': 'No model configured for this Locrit'})
                return

            # Test connection
            connection_test = ollama_service.test_connection()
            if not connection_test.get('success'):
                emit('error', {'message': 'Ollama service unavailable'})
                return

            # Set up session and user ID for memory
            user_id = session.get('user_name', 'web_user') if 'user_name' in session else 'websocket_user'
            session_id = f"websocket_{user_id}_{locrit_name}"

            # Save user message to memory
            try:
                asyncio.run(memory_manager.save_message(
                    locrit_name=locrit_name,
                    role="user",
                    content=message,
                    session_id=session_id,
                    user_id=user_id
                ))
            except Exception as e:
                logger.warning(f"Error saving user message to memory: {e}")

            # Prepare system prompt
            system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

            logger.info(f"Processing chat message for {locrit_name} using model {model}")

            # Retrieve conversation history from memory
            conversation_history = []
            try:
                # Get last 20 messages for context
                history_messages = asyncio.run(memory_manager.get_conversation_history(
                    locrit_name=locrit_name,
                    session_id=session_id,
                    limit=20
                ))

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
                                    'content': content,
                                    'timestamp': datetime.now().isoformat()
                                })

                    # Save assistant response to memory
                    try:
                        asyncio.run(memory_manager.save_message(
                            locrit_name=locrit_name,
                            role="assistant",
                            content=full_response,
                            session_id=session_id,
                            user_id=user_id
                        ))
                    except Exception as e:
                        logger.warning(f"Error saving assistant response to memory: {e}")

                    # Send completion signal
                    emit('chat_complete', {
                        'locrit_name': locrit_name,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Handle non-streaming response
                    full_response = "".join(
                        chunk['message']['content'] for chunk in stream if 'message' in chunk and 'content' in chunk['message']
                    )

                    # Save assistant response to memory
                    try:
                        asyncio.run(memory_manager.save_message(
                            locrit_name=locrit_name,
                            role="assistant",
                            content=full_response,
                            session_id=session_id,
                            user_id=user_id
                        ))
                    except Exception as e:
                        logger.warning(f"Error saving assistant response to memory: {e}")

                    emit('chat_response', {
                        'locrit_name': locrit_name,
                        'response': full_response,
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error streaming chat response: {str(e)}")
                emit('error', {'message': f'Error generating response: {str(e)}'})

        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            emit('error', {'message': str(e)})


# Create the chat namespace instance
chat_namespace = ChatNamespace('/')