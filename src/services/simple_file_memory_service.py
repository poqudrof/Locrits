"""
Simple File-Based Memory Service - compatible with old memory_manager interface
Stores conversation history in JSON files for easy debugging and stability
"""

import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import re


class SimpleFileMemoryService:
    """
    Simple file-based memory service that stores conversations in JSON files.
    Compatible with the memory_manager_service interface.
    """

    def __init__(self, locrit_name: str, base_path: str = "data/memory"):
        """
        Initialize the simple file memory service.

        Args:
            locrit_name: Name of the Locrit
            base_path: Base directory for memory storage
        """
        self.locrit_name = locrit_name
        self.base_path = Path(base_path)

        # Sanitize locrit name for filesystem
        sanitized_name = re.sub(r'[^\w\-_]', '_', locrit_name.lower())
        self.memory_dir = self.base_path / sanitized_name / 'simple_file'

        # Paths for different data types
        self.messages_dir = self.memory_dir / 'messages'
        self.sessions_dir = self.memory_dir / 'sessions'
        self.index_file = self.memory_dir / 'index.json'

        self.is_initialized = False

    async def initialize(self) -> bool:
        """Initialize the file-based memory service."""
        try:
            # Create directories
            self.messages_dir.mkdir(parents=True, exist_ok=True)
            self.sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create index if it doesn't exist
            if not self.index_file.exists():
                await self._save_json(self.index_file, {
                    'total_messages': 0,
                    'total_sessions': 0,
                    'created_at': datetime.now().isoformat()
                })

            self.is_initialized = True
            print(f"📄 Simple file memory initialized for {self.locrit_name} at {self.memory_dir}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize simple file memory: {e}")
            return False

    async def _save_json(self, filepath: Path, data: Any) -> None:
        """Save data to JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")

    async def _load_json(self, filepath: Path, default: Any = None) -> Any:
        """Load data from JSON file."""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            print(f"Error loading JSON from {filepath}: {e}")
            return default

    async def save_message(self, role: str, content: str, session_id: str = None,
                          user_id: str = "default", metadata: Dict = None) -> str:
        """
        Save a message to memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            Message ID
        """
        if not self.is_initialized:
            await self.initialize()

        # Generate message ID
        message_id = str(uuid.uuid4())

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create message data
        message_data = {
            'id': message_id,
            'role': role,
            'content': content,
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # Save message file
        message_file = self.messages_dir / f"{message_id}.json"
        await self._save_json(message_file, message_data)

        # Update session index
        await self._update_session_index(session_id, message_id)

        # Update main index
        await self._increment_index('total_messages')

        return message_id

    async def _update_session_index(self, session_id: str, message_id: str) -> None:
        """Update session index with new message."""
        session_file = self.sessions_dir / f"{session_id}.json"
        session_data = await self._load_json(session_file, {
            'id': session_id,
            'message_ids': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })

        if message_id not in session_data['message_ids']:
            session_data['message_ids'].append(message_id)
            session_data['updated_at'] = datetime.now().isoformat()
            await self._save_json(session_file, session_data)

    async def _increment_index(self, key: str) -> None:
        """Increment a counter in the main index."""
        index_data = await self._load_json(self.index_file, {})
        index_data[key] = index_data.get(key, 0) + 1
        await self._save_json(self.index_file, index_data)

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages

        Returns:
            List of message dictionaries
        """
        if not self.is_initialized:
            await self.initialize()

        # Load session data
        session_file = self.sessions_dir / f"{session_id}.json"
        session_data = await self._load_json(session_file)

        if not session_data:
            return []

        # Load messages
        messages = []
        message_ids = session_data.get('message_ids', [])[-limit:]

        for message_id in message_ids:
            message_file = self.messages_dir / f"{message_id}.json"
            message_data = await self._load_json(message_file)
            if message_data:
                messages.append(message_data)

        return messages

    async def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search messages by text content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        if not self.is_initialized:
            await self.initialize()

        query_lower = query.lower()
        results = []

        # Search through all message files
        for message_file in self.messages_dir.glob('*.json'):
            message_data = await self._load_json(message_file)
            if message_data and query_lower in message_data.get('content', '').lower():
                results.append(message_data)
                if len(results) >= limit:
                    break

        return results

    async def get_full_memory_summary(self) -> Dict[str, Any]:
        """
        Get summary of memory statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.is_initialized:
            await self.initialize()

        index_data = await self._load_json(self.index_file, {})

        # Count actual files
        message_count = len(list(self.messages_dir.glob('*.json')))
        session_count = len(list(self.sessions_dir.glob('*.json')))

        # Get recent messages
        recent_messages = []
        message_files = sorted(
            self.messages_dir.glob('*.json'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for msg_file in message_files[:20]:  # Get up to 20 recent messages
            message_data = await self._load_json(msg_file)
            if message_data:
                recent_messages.append(message_data)

        # Get sessions
        sessions = []
        session_files = sorted(
            self.sessions_dir.glob('*.json'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for session_file in session_files:
            session_data = await self._load_json(session_file)
            if session_data:
                sessions.append(session_data)

        return {
            'statistics': {
                'total_messages': message_count,
                'total_sessions': session_count,
                'memory_type': 'simple_file',
                'locrit_name': self.locrit_name
            },
            'index_data': index_data,
            'recent_messages': recent_messages,
            'sessions': sessions
        }

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        try:
            message_file = self.messages_dir / f"{message_id}.json"
            if message_file.exists():
                message_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting message {message_id}: {e}")
            return False

    async def edit_message(self, message_id: str, new_content: str) -> bool:
        """Edit a message."""
        try:
            message_file = self.messages_dir / f"{message_id}.json"
            message_data = await self._load_json(message_file)
            if message_data:
                message_data['content'] = new_content
                message_data['edited_at'] = datetime.now().isoformat()
                await self._save_json(message_file, message_data)
                return True
            return False
        except Exception as e:
            print(f"Error editing message {message_id}: {e}")
            return False

    async def get_message_by_id(self, message_id: str) -> Optional[Dict]:
        """Get a specific message by ID."""
        message_file = self.messages_dir / f"{message_id}.json"
        return await self._load_json(message_file)

    async def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID."""
        session_file = self.sessions_dir / f"{session_id}.json"
        return await self._load_json(session_file)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            session_data = await self._load_json(session_file)

            if session_data:
                # Delete all messages in the session
                for message_id in session_data.get('message_ids', []):
                    await self.delete_message(message_id)

                # Delete session file
                if session_file.exists():
                    session_file.unlink()

                return True
            return False
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    async def clear_all_memory(self) -> bool:
        """Clear all memory data."""
        try:
            # Delete all message files
            for message_file in self.messages_dir.glob('*.json'):
                message_file.unlink()

            # Delete all session files
            for session_file in self.sessions_dir.glob('*.json'):
                session_file.unlink()

            # Reset index
            await self._save_json(self.index_file, {
                'total_messages': 0,
                'total_sessions': 0,
                'cleared_at': datetime.now().isoformat()
            })

            return True
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

    # Stub methods for compatibility
    async def add_memory(self, content: str, importance: float = 0.5, metadata: Dict = None) -> str:
        """Add a standalone memory (stored as a system message)."""
        return await self.save_message('system', content, metadata=metadata)

    async def get_all_memories(self) -> List[Dict]:
        """Get all messages (simplified)."""
        messages = []
        for message_file in self.messages_dir.glob('*.json'):
            message_data = await self._load_json(message_file)
            if message_data:
                messages.append(message_data)
        return messages

    async def get_concept_details(self, concept_name: str, concept_type: str = None) -> Optional[Dict]:
        """Not supported in simple file memory."""
        return None

    async def get_related_concepts(self, concept_name: str, depth: int = 2) -> List[Dict]:
        """Not supported in simple file memory."""
        return []

    async def edit_concept(self, concept_id: str, name: str = None,
                          description: str = None, confidence: float = None) -> bool:
        """Not supported in simple file memory."""
        return False

    async def delete_concept(self, concept_id: str) -> bool:
        """Not supported in simple file memory."""
        return False

    async def close(self) -> None:
        """Close the memory service."""
        self.is_initialized = False
