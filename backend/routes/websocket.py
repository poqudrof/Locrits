"""
WebSocket routes for real-time chat communication
"""

import json
from datetime import datetime
from flask_socketio import Namespace, emit, join_room, leave_room
from src.services.config_service import config_service
from src.services.ui_logging_service import ui_logging_service

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

            # Prepare system prompt
            system_prompt = f"Tu es {locrit_name}, un Locrit. {settings.get('description', '')}"

            logger.info(f"Processing chat message for {locrit_name} using model {model}")

            # Stream the response
            try:
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

                # Send chunks to the client
                # Stream the response if requested
                if stream:
                    for chunk in stream:
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            if content:
                                emit('chat_chunk', {
                                    'locrit_name': locrit_name,
                                    'content': content,
                                    'timestamp': datetime.now().isoformat()
                                })

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