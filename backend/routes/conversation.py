"""
Conversation routes for Locrit - Server-side conversation management
These routes allow clients to interact with Locrits using only conversation IDs.
All context is managed server-side.
"""

import asyncio
import nest_asyncio
from flask import Blueprint, request, jsonify
from src.services.conversation_service import conversation_service
from src.services.ui_logging_service import ui_logging_service

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

conversation_bp = Blueprint('conversation', __name__)

# Logger
logger = ui_logging_service.logger


@conversation_bp.route('/api/conversations/create', methods=['POST'])
def create_conversation():
    """
    Create a new conversation with a Locrit.

    Request body:
    {
        "locrit_name": "LocritName",
        "user_id": "user123",  // optional, defaults to "anonymous"
        "metadata": {}  // optional additional metadata
    }

    Response:
    {
        "success": true,
        "conversation_id": "uuid",
        "locrit_name": "LocritName",
        "created_at": "2025-10-03T...",
        "session_id": "uuid"
    }
    """
    try:
        data = request.get_json()
        if not data or 'locrit_name' not in data:
            return jsonify({'error': 'locrit_name is required'}), 400

        locrit_name = data['locrit_name']
        user_id = data.get('user_id', 'anonymous')
        metadata = data.get('metadata', {})

        # Create conversation (wrap async call)
        conversation = asyncio.run(conversation_service.create_conversation(
            locrit_name=locrit_name,
            user_id=user_id,
            metadata=metadata
        ))

        if not conversation:
            return jsonify({'error': 'Locrit not found or inactive'}), 404

        logger.info(f"Created conversation {conversation['conversation_id']} with {locrit_name}")

        return jsonify({
            'success': True,
            'conversation_id': conversation['conversation_id'],
            'locrit_name': conversation['locrit_name'],
            'created_at': conversation['created_at'],
            'session_id': conversation['session_id']
        })

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@conversation_bp.route('/api/conversations/<conversation_id>/message', methods=['POST'])
def send_message(conversation_id):
    """
    Send a message in a conversation. Context is managed server-side.

    Request body:
    {
        "message": "Hello, Locrit!"
    }

    Response:
    {
        "success": true,
        "response": "Locrit's response",
        "conversation_id": "uuid",
        "locrit_name": "LocritName",
        "timestamp": "2025-10-03T...",
        "message_count": 2
    }
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'message is required'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'message cannot be empty'}), 400

        # Send message and get response (wrap async call)
        result = asyncio.run(conversation_service.send_message(
            conversation_id=conversation_id,
            message=message,
            save_to_memory=True
        ))

        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            status_code = 404 if 'not found' in error_msg.lower() else 500
            return jsonify(result), status_code

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500


@conversation_bp.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """
    Get conversation details and history.

    Query params:
    - limit: Maximum number of messages to return (default: 50)

    Response:
    {
        "conversation_id": "uuid",
        "locrit_name": "LocritName",
        "user_id": "user123",
        "created_at": "2025-10-03T...",
        "last_activity": "2025-10-03T...",
        "message_count": 10,
        "messages": [...]
    }
    """
    try:
        limit = int(request.args.get('limit', 50))

        conversation = asyncio.run(conversation_service.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit
        ))

        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404

        return jsonify(conversation)

    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@conversation_bp.route('/api/conversations', methods=['GET'])
def list_conversations():
    """
    List conversations for a user.

    Query params:
    - user_id: User identifier (required)
    - locrit_name: Optional filter by Locrit name

    Response:
    {
        "success": true,
        "conversations": [
            {
                "conversation_id": "uuid",
                "locrit_name": "LocritName",
                "created_at": "2025-10-03T...",
                "last_activity": "2025-10-03T...",
                "message_count": 10
            },
            ...
        ]
    }
    """
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400

        locrit_name = request.args.get('locrit_name')

        conversations = asyncio.run(conversation_service.list_user_conversations(
            user_id=user_id,
            locrit_name=locrit_name
        ))

        return jsonify({
            'success': True,
            'conversations': conversations,
            'count': len(conversations)
        })

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500


@conversation_bp.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    Delete a conversation.

    Response:
    {
        "success": true,
        "message": "Conversation deleted"
    }
    """
    try:
        success = asyncio.run(conversation_service.delete_conversation(conversation_id))

        if not success:
            return jsonify({'error': 'Conversation not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Conversation deleted'
        })

    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@conversation_bp.route('/api/conversations/<conversation_id>/info', methods=['GET'])
def get_conversation_info(conversation_id):
    """
    Get conversation info without message history.

    Response:
    {
        "conversation_id": "uuid",
        "locrit_name": "LocritName",
        "user_id": "user123",
        "created_at": "2025-10-03T...",
        "last_activity": "2025-10-03T...",
        "message_count": 10
    }
    """
    try:
        conversation = asyncio.run(conversation_service.get_conversation(conversation_id))

        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404

        # Return conversation info without messages
        return jsonify({
            'conversation_id': conversation['conversation_id'],
            'locrit_name': conversation['locrit_name'],
            'user_id': conversation['user_id'],
            'created_at': conversation['created_at'],
            'last_activity': conversation['last_activity'],
            'message_count': conversation['message_count'],
            'metadata': conversation.get('metadata', {})
        })

    except Exception as e:
        logger.error(f"Error getting conversation info: {str(e)}")
        return jsonify({'error': str(e)}), 500
