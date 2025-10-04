"""
Conversation Service - Manages conversations with Locrits using conversation IDs.
This service allows clients to interact with Locrits using only a conversation ID,
with all context management handled server-side.

AUTONOMOUS MODE: Conversations are persisted to YAML files on disk,
enabling the backend to track conversations independently of the UI.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from .memory_manager_service import memory_manager
from .config_service import config_service
from .comprehensive_logging_service import comprehensive_logger
from .conversation_persistence_service import conversation_persistence


class ConversationService:
    """Manages conversations with context stored server-side and persisted to disk."""

    def __init__(self):
        """Initialize the conversation service."""
        # In-memory cache (loaded from disk on demand)
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False

    async def create_conversation(
        self,
        locrit_name: str,
        user_id: str = "anonymous",
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new conversation with a Locrit.
        Automatically persisted to disk for autonomous tracking.

        Args:
            locrit_name: Name of the Locrit
            user_id: User identifier
            metadata: Additional metadata for the conversation

        Returns:
            Dictionary with conversation details including conversation_id
        """
        # Verify the Locrit exists
        locrit_settings = config_service.get_locrit_settings(locrit_name)
        if not locrit_settings:
            return None

        # Generate unique conversation ID
        conversation_id = str(uuid.uuid4())

        # Create conversation metadata
        conversation = {
            "conversation_id": conversation_id,
            "locrit_name": locrit_name,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "metadata": metadata or {},
            # Use conversation_id as session_id for memory storage
            "session_id": conversation_id,
            "status": "active"
        }

        # Store in memory cache
        self.conversations[conversation_id] = conversation

        # PERSIST TO DISK for autonomous tracking
        await conversation_persistence.save_conversation(conversation_id, conversation)

        # Log conversation creation (reduced verbosity)
        print(f"✓ Conversation {conversation_id[:8]}... created for {locrit_name}")

        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation details.
        Loads from disk if not in memory cache.

        Args:
            conversation_id: The conversation identifier

        Returns:
            Conversation details or None if not found
        """
        # Check memory cache first
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]

        # Load from disk if not in cache
        conversation = await conversation_persistence.load_conversation(conversation_id)
        if conversation:
            # Cache it
            self.conversations[conversation_id] = conversation

        return conversation

    async def send_message(
        self,
        conversation_id: str,
        message: str,
        save_to_memory: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message in a conversation and get the Locrit's response.
        All conversation context is managed server-side.

        Args:
            conversation_id: The conversation identifier
            message: The user's message
            save_to_memory: Whether to save messages to memory

        Returns:
            Dictionary with response and conversation info
        """
        # Get conversation
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {"error": "Conversation not found", "success": False}

        locrit_name = conversation["locrit_name"]
        user_id = conversation["user_id"]
        session_id = conversation["session_id"]

        # Verify the Locrit still exists and is active
        locrit_settings = config_service.get_locrit_settings(locrit_name)
        if not locrit_settings:
            return {"error": "Locrit not found", "success": False}

        if not locrit_settings.get('active', False):
            return {"error": "Locrit is inactive", "success": False}

        # Get Ollama model
        model = locrit_settings.get('ollama_model')
        if not model:
            return {"error": "No model configured for this Locrit", "success": False}

        # Save user message to memory
        if save_to_memory:
            await memory_manager.save_message(
                locrit_name=locrit_name,
                role="user",
                content=message,
                session_id=session_id,
                user_id=user_id
            )

        # Get conversation history from memory (last 20 messages)
        conversation_history = await memory_manager.get_conversation_history(
            locrit_name=locrit_name,
            session_id=session_id,
            limit=20
        )

        # Prepare system prompt
        system_prompt = f"Tu es {locrit_name}, un Locrit. {locrit_settings.get('description', '')}"

        # Generate response using Ollama
        from src.services.ollama_service import get_ollama_service_for_locrit

        try:
            ollama_service = get_ollama_service_for_locrit(locrit_name)
        except (ValueError, Exception) as e:
            return {"error": f"Ollama service not available: {str(e)}", "success": False}

        # Test connection
        connection_test = ollama_service.test_connection()
        if not connection_test.get('success'):
            return {"error": "Ollama service not available - connection failed", "success": False}

        try:
            # Set model
            ollama_service.current_model = model
            ollama_service.is_connected = True

            # Generate response with conversation history context
            import nest_asyncio
            import asyncio
            nest_asyncio.apply()

            # Build context from history
            context_messages = []
            for msg in conversation_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context_messages.append(f"{role}: {content}")

            # Add current message
            context_messages.append(f"user: {message}")

            # Create full prompt with context
            full_message = "\n".join(context_messages[-10:])  # Last 10 exchanges

            response = asyncio.run(ollama_service.chat(full_message, system_prompt))

            # Save assistant response to memory
            if save_to_memory:
                await memory_manager.save_message(
                    locrit_name=locrit_name,
                    role="assistant",
                    content=response,
                    session_id=session_id,
                    user_id=user_id
                )

            # Update conversation metadata
            conversation["last_activity"] = datetime.now().isoformat()
            conversation["message_count"] += 2  # User message + assistant response

            # PERSIST UPDATES TO DISK for autonomous tracking
            await conversation_persistence.update_conversation(
                conversation_id,
                {
                    "last_activity": conversation["last_activity"],
                    "message_count": conversation["message_count"]
                }
            )

            return {
                "success": True,
                "response": response,
                "conversation_id": conversation_id,
                "locrit_name": locrit_name,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "message_count": conversation["message_count"]
            }

        except Exception as e:
            print(f"Error in conversation {conversation_id}: {e}")
            return {
                "success": False,
                "error": f"Error generating response: {str(e)}"
            }

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get the full conversation history.

        Args:
            conversation_id: The conversation identifier
            limit: Maximum number of messages to return

        Returns:
            Dictionary with conversation info and message history
        """
        # Get conversation
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None

        # Get messages from memory
        messages = await memory_manager.get_conversation_history(
            locrit_name=conversation["locrit_name"],
            session_id=conversation["session_id"],
            limit=limit
        )

        return {
            "conversation_id": conversation_id,
            "locrit_name": conversation["locrit_name"],
            "user_id": conversation["user_id"],
            "created_at": conversation["created_at"],
            "last_activity": conversation["last_activity"],
            "message_count": conversation["message_count"],
            "messages": messages
        }

    async def list_user_conversations(
        self,
        user_id: str,
        locrit_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        List all conversations for a user, optionally filtered by Locrit.
        Loads from disk for complete autonomous tracking.

        Args:
            user_id: User identifier
            locrit_name: Optional Locrit name filter

        Returns:
            List of conversation summaries
        """
        # Load from disk (authoritative source)
        return await conversation_persistence.list_conversations(
            user_id=user_id,
            locrit_name=locrit_name,
            status="active"
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation (marks as deleted on disk).

        Args:
            conversation_id: The conversation identifier

        Returns:
            True if deletion succeeds
        """
        # Remove from cache
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

        # Mark as deleted on disk (preserves history)
        return await conversation_persistence.delete_conversation(conversation_id)


# Global instance
conversation_service = ConversationService()
