"""
Conversation Persistence Service
Manages conversation data persistence to YAML files on disk.
Enables autonomous conversation tracking server-side.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from threading import Lock


class ConversationPersistenceService:
    """Manages conversation persistence to YAML files."""

    def __init__(self, storage_dir: str = "data/conversations"):
        """
        Initialize the conversation persistence service.

        Args:
            storage_dir: Directory to store conversation YAML files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, Lock] = {}  # Per-conversation locks for thread safety

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.storage_dir / f"{conversation_id}.yaml"

    def _get_lock(self, conversation_id: str) -> Lock:
        """Get or create a lock for a conversation."""
        if conversation_id not in self._locks:
            self._locks[conversation_id] = Lock()
        return self._locks[conversation_id]

    async def save_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """
        Save a conversation to disk.

        Args:
            conversation_id: The conversation identifier
            conversation_data: Full conversation data to save

        Returns:
            True if save succeeds
        """
        try:
            path = self._get_conversation_path(conversation_id)
            lock = self._get_lock(conversation_id)

            # Prepare data for YAML (ensure all fields are serializable)
            save_data = {
                "conversation_id": conversation_data.get("conversation_id"),
                "locrit_name": conversation_data.get("locrit_name"),
                "user_id": conversation_data.get("user_id", "anonymous"),
                "created_at": conversation_data.get("created_at"),
                "last_activity": conversation_data.get("last_activity"),
                "message_count": conversation_data.get("message_count", 0),
                "session_id": conversation_data.get("session_id"),
                "metadata": conversation_data.get("metadata", {}),
                "status": conversation_data.get("status", "active")  # active, archived, deleted
            }

            # Thread-safe write
            def write_yaml():
                with lock:
                    print(f"📝 FILE WRITE: {path} (mode: w, type: yaml)")
                    with open(path, 'w', encoding='utf-8') as f:
                        yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True)
                    print(f"✅ FILE WRITE: {path} completed")

            # Run in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, write_yaml)
            return True

        except Exception as e:
            print(f"Error saving conversation {conversation_id}: {e}")
            return False

    async def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation from disk.

        Args:
            conversation_id: The conversation identifier

        Returns:
            Conversation data or None if not found
        """
        try:
            path = self._get_conversation_path(conversation_id)

            if not path.exists():
                return None

            lock = self._get_lock(conversation_id)

            # Thread-safe read
            def read_yaml():
                with lock:
                    print(f"📖 FILE READ: {path} (mode: r, type: yaml)")
                    with open(path, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)

            # Run in executor to avoid blocking
            data = await asyncio.get_event_loop().run_in_executor(None, read_yaml)
            return data

        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {e}")
            return None

    async def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in a conversation.

        Args:
            conversation_id: The conversation identifier
            updates: Dictionary of fields to update

        Returns:
            True if update succeeds
        """
        try:
            # Load existing conversation
            conversation = await self.load_conversation(conversation_id)
            if not conversation:
                return False

            # Update fields
            conversation.update(updates)

            # Save back
            return await self.save_conversation(conversation_id, conversation)

        except Exception as e:
            print(f"Error updating conversation {conversation_id}: {e}")
            return False

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from disk (or mark as deleted).

        Args:
            conversation_id: The conversation identifier

        Returns:
            True if deletion succeeds
        """
        try:
            # Mark as deleted rather than physically deleting
            return await self.update_conversation(conversation_id, {
                "status": "deleted",
                "deleted_at": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"Error deleting conversation {conversation_id}: {e}")
            return False

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        locrit_name: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        List conversations with optional filters.

        Args:
            user_id: Filter by user ID
            locrit_name: Filter by Locrit name
            status: Filter by status (active, archived, deleted)

        Returns:
            List of conversation summaries
        """
        try:
            conversations = []

            # Read all YAML files in the storage directory
            def read_all_conversations():
                results = []
                for yaml_file in self.storage_dir.glob("*.yaml"):
                    try:
                        print(f"📖 FILE READ: {yaml_file} (mode: r, type: yaml)")
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if data:
                                results.append(data)
                    except Exception as e:
                        print(f"Error reading {yaml_file}: {e}")
                return results

            # Run in executor
            all_conversations = await asyncio.get_event_loop().run_in_executor(
                None, read_all_conversations
            )

            # Apply filters
            for conv in all_conversations:
                # Status filter
                if conv.get("status", "active") != status:
                    continue

                # User filter
                if user_id and conv.get("user_id") != user_id:
                    continue

                # Locrit filter
                if locrit_name and conv.get("locrit_name") != locrit_name:
                    continue

                conversations.append({
                    "conversation_id": conv.get("conversation_id"),
                    "locrit_name": conv.get("locrit_name"),
                    "user_id": conv.get("user_id"),
                    "created_at": conv.get("created_at"),
                    "last_activity": conv.get("last_activity"),
                    "message_count": conv.get("message_count", 0),
                    "status": conv.get("status", "active")
                })

            # Sort by last activity (most recent first)
            conversations.sort(
                key=lambda x: x.get("last_activity", ""),
                reverse=True
            )

            return conversations

        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []

    async def archive_old_conversations(self, days_inactive: int = 30) -> int:
        """
        Archive conversations that have been inactive for a specified period.

        Args:
            days_inactive: Number of days of inactivity before archiving

        Returns:
            Number of conversations archived
        """
        try:
            from datetime import timedelta

            archived_count = 0
            cutoff_date = datetime.now() - timedelta(days=days_inactive)

            # Get all active conversations
            active_conversations = await self.list_conversations(status="active")

            for conv in active_conversations:
                last_activity = conv.get("last_activity")
                if last_activity:
                    try:
                        last_activity_date = datetime.fromisoformat(last_activity)
                        if last_activity_date < cutoff_date:
                            # Archive this conversation
                            success = await self.update_conversation(
                                conv["conversation_id"],
                                {
                                    "status": "archived",
                                    "archived_at": datetime.now().isoformat()
                                }
                            )
                            if success:
                                archived_count += 1
                    except ValueError:
                        # Invalid date format, skip
                        continue

            return archived_count

        except Exception as e:
            print(f"Error archiving old conversations: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored conversations.

        Returns:
            Dictionary with statistics
        """
        try:
            active = await self.list_conversations(status="active")
            archived = await self.list_conversations(status="archived")
            deleted = await self.list_conversations(status="deleted")

            # Count by Locrit
            locrit_counts: Dict[str, int] = {}
            for conv in active:
                locrit_name = conv.get("locrit_name", "unknown")
                locrit_counts[locrit_name] = locrit_counts.get(locrit_name, 0) + 1

            return {
                "total_conversations": len(active) + len(archived) + len(deleted),
                "active_conversations": len(active),
                "archived_conversations": len(archived),
                "deleted_conversations": len(deleted),
                "conversations_by_locrit": locrit_counts,
                "storage_path": str(self.storage_dir)
            }

        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


# Global instance
conversation_persistence = ConversationPersistenceService()
