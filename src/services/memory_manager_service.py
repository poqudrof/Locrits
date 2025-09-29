"""
Memory Manager Service - Manages per-Locrit Kuzu memory instances.
This service handles the creation and routing of memory requests to individual Locrit databases.
"""

from typing import Dict, Optional, Any, List
from .kuzu_memory_service import KuzuMemoryService
from .config_service import config_service
from .comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory


class MemoryManagerService:
    """Manages memory services for multiple Locrits."""

    def __init__(self, base_path: str = "data/memory"):
        """
        Initialize the memory manager.

        Args:
            base_path: Base directory for memory databases
        """
        self.base_path = base_path
        self.memory_services: Dict[str, KuzuMemoryService] = {}
        self.is_initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the memory manager.

        Returns:
            True if initialization succeeds
        """
        try:
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Error initializing memory manager: {e}")
            return False

    async def get_memory_service(self, locrit_name: str) -> Optional[KuzuMemoryService]:
        """
        Get or create a memory service for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit

        Returns:
            KuzuMemoryService instance or None if error
        """
        if not self.is_initialized:
            await self.initialize()

        # Return existing service if already created
        if locrit_name in self.memory_services:
            return self.memory_services[locrit_name]

        # Verify the Locrit exists in config
        locrit_settings = config_service.get_locrit_settings(locrit_name)
        if not locrit_settings:
            print(f"Locrit {locrit_name} not found in configuration")
            return None

        try:
            # Create new memory service for this Locrit
            memory_service = KuzuMemoryService(locrit_name, self.base_path)

            # Initialize the service
            success = await memory_service.initialize()
            if not success:
                print(f"Failed to initialize memory service for {locrit_name}")
                return None

            # Store and return the service
            self.memory_services[locrit_name] = memory_service
            print(f"Created memory service for Locrit: {locrit_name}")
            return memory_service

        except Exception as e:
            print(f"Error creating memory service for {locrit_name}: {e}")
            return None

    async def save_message(self, locrit_name: str, role: str, content: str,
                          session_id: str = None, user_id: str = "default",
                          metadata: Dict = None) -> Optional[str]:
        """
        Save a message to a specific Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            role: Message role
            content: Message content
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            Message ID or None if error
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return None

        try:
            # Start operation tracking
            operation_id = comprehensive_logger.start_operation(f"memory_save_{locrit_name}")

            result = await memory_service.save_message(
                role=role,
                content=content,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log the memory save operation
            comprehensive_logger.log_memory_save(
                content=content,
                locrit_name=locrit_name,
                memory_type="message",
                session_id=session_id,
                user_id=user_id,
                metadata=metadata,
                success=result is not None,
                error=None if result else "Save returned None"
            )

            return result
        except Exception as e:
            # End operation tracking for failed operation
            duration_ms = comprehensive_logger.end_operation(operation_id)

            print(f"Error saving message for {locrit_name}: {e}")

            # Log the failed memory save operation
            comprehensive_logger.log_memory_save(
                content=content,
                locrit_name=locrit_name,
                memory_type="message",
                session_id=session_id,
                user_id=user_id,
                metadata=metadata,
                success=False,
                error=str(e)
            )

            return None

    async def get_conversation_history(self, locrit_name: str, session_id: str,
                                     limit: int = 50) -> List[Dict]:
        """
        Get conversation history for a specific Locrit and session.

        Args:
            locrit_name: Name of the Locrit
            session_id: Session identifier
            limit: Maximum number of messages

        Returns:
            List of message dictionaries
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return []

        try:
            # Start operation tracking
            operation_id = comprehensive_logger.start_operation(f"memory_recall_{locrit_name}")

            result = await memory_service.get_conversation_history(session_id, limit)

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log the memory recall operation
            comprehensive_logger.log_memory_recall(
                query=f"session:{session_id}",
                locrit_name=locrit_name,
                results_count=len(result),
                session_id=session_id,
                duration_ms=duration_ms,
                search_type="conversation_history"
            )

            return result
        except Exception as e:
            # End operation tracking for failed operation
            duration_ms = comprehensive_logger.end_operation(operation_id)

            print(f"Error getting conversation history for {locrit_name}: {e}")

            # Log the failed memory recall operation
            comprehensive_logger.log_memory_recall(
                query=f"session:{session_id}",
                locrit_name=locrit_name,
                results_count=0,
                session_id=session_id,
                duration_ms=duration_ms,
                search_type="conversation_history"
            )

            return []

    async def search_memories(self, locrit_name: str, query: str,
                            limit: int = 10) -> List[Dict]:
        """
        Search memories for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return []

        try:
            # Start operation tracking
            operation_id = comprehensive_logger.start_operation(f"memory_search_{locrit_name}")

            result = await memory_service.search_memories(query, limit)

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log the memory search operation
            comprehensive_logger.log_memory_search(
                query=query,
                locrit_name=locrit_name,
                results_count=len(result),
                search_strategy="auto",
                duration_ms=duration_ms
            )

            return result
        except Exception as e:
            # End operation tracking for failed operation
            duration_ms = comprehensive_logger.end_operation(operation_id)

            print(f"Error searching memories for {locrit_name}: {e}")

            # Log the failed memory search operation
            comprehensive_logger.log_memory_search(
                query=query,
                locrit_name=locrit_name,
                results_count=0,
                search_strategy="auto",
                duration_ms=duration_ms
            )

            return []

    async def get_full_memory_summary(self, locrit_name: str) -> Dict[str, Any]:
        """
        Get complete memory summary for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit

        Returns:
            Dictionary with memory summary
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return {"error": f"Memory service not available for {locrit_name}"}

        try:
            return await memory_service.get_full_memory_summary()
        except Exception as e:
            print(f"Error getting memory summary for {locrit_name}: {e}")
            return {"error": str(e)}

    async def get_concept_details(self, locrit_name: str, concept_name: str,
                                 concept_type: str = None) -> Optional[Dict]:
        """
        Get detailed information about a specific concept for a Locrit.

        Args:
            locrit_name: Name of the Locrit
            concept_name: Name of the concept
            concept_type: Type of the concept (optional filter)

        Returns:
            Dictionary with concept details or None if not found
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return None

        try:
            return await memory_service.get_concept_details(concept_name, concept_type)
        except Exception as e:
            print(f"Error getting concept details for {locrit_name}: {e}")
            return None

    async def get_related_concepts(self, locrit_name: str, concept_name: str,
                                  depth: int = 2) -> List[Dict]:
        """
        Get related concepts for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit
            concept_name: Name of the concept
            depth: Maximum traversal depth

        Returns:
            List of related concepts
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return []

        try:
            return await memory_service.get_related_concepts(concept_name, depth)
        except Exception as e:
            print(f"Error getting related concepts for {locrit_name}: {e}")
            return []

    async def list_available_locrits(self) -> List[str]:
        """
        List all Locrits that have memory services available.

        Returns:
            List of Locrit names
        """
        # Get all configured Locrits
        configured_locrits = config_service.list_locrits()

        # Return only active ones
        active_locrits = []
        for locrit_name in configured_locrits:
            settings = config_service.get_locrit_settings(locrit_name)
            if settings and settings.get('active', False):
                active_locrits.append(locrit_name)

        return active_locrits

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get overall memory statistics across all Locrits.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_locrits": len(self.memory_services),
            "active_locrits": list(self.memory_services.keys()),
            "base_path": self.base_path,
            "per_locrit_stats": {}
        }

        # Get stats for each Locrit
        for locrit_name, memory_service in self.memory_services.items():
            try:
                locrit_summary = await memory_service.get_full_memory_summary()
                if "statistics" in locrit_summary:
                    stats["per_locrit_stats"][locrit_name] = locrit_summary["statistics"]
            except Exception as e:
                stats["per_locrit_stats"][locrit_name] = {"error": str(e)}

        return stats

    async def close_all(self) -> None:
        """Close all memory services."""
        for locrit_name, memory_service in self.memory_services.items():
            try:
                await memory_service.close()
                print(f"Closed memory service for {locrit_name}")
            except Exception as e:
                print(f"Error closing memory service for {locrit_name}: {e}")

        self.memory_services.clear()
        self.is_initialized = False

    async def close_locrit_memory(self, locrit_name: str) -> bool:
        """
        Close memory service for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit

        Returns:
            True if successfully closed
        """
        if locrit_name in self.memory_services:
            try:
                await self.memory_services[locrit_name].close()
                del self.memory_services[locrit_name]
                print(f"Closed memory service for {locrit_name}")
                return True
            except Exception as e:
                print(f"Error closing memory service for {locrit_name}: {e}")
                return False

        return True  # Already closed

    # Memory editing methods

    async def delete_message(self, locrit_name: str, message_id: str) -> bool:
        """
        Delete a message from a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            message_id: ID of the message to delete

        Returns:
            True if deletion succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            # Log the memory edit operation
            comprehensive_logger.log_memory_edit(
                operation="delete_message",
                target_id=message_id,
                locrit_name=locrit_name,
                success=True,
                user_id=None,
                details={"message_id": message_id}
            )

            result = await memory_service.delete_message(message_id)

            if not result:
                # Log failed deletion
                comprehensive_logger.log_memory_edit(
                    operation="delete_message",
                    target_id=message_id,
                    locrit_name=locrit_name,
                    success=False,
                    error="Delete returned False",
                    details={"message_id": message_id}
                )

            return result
        except Exception as e:
            print(f"Error deleting message for {locrit_name}: {e}")

            # Log the failed memory edit operation
            comprehensive_logger.log_memory_edit(
                operation="delete_message",
                target_id=message_id,
                locrit_name=locrit_name,
                success=False,
                error=str(e),
                details={"message_id": message_id}
            )

            return False

    async def edit_message(self, locrit_name: str, message_id: str, new_content: str) -> bool:
        """
        Edit a message in a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            message_id: ID of the message to edit
            new_content: New message content

        Returns:
            True if edit succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.edit_message(message_id, new_content)
        except Exception as e:
            print(f"Error editing message for {locrit_name}: {e}")
            return False

    async def add_memory(self, locrit_name: str, content: str, importance: float = 0.5,
                        metadata: Dict = None) -> Optional[str]:
        """
        Add a standalone memory to a Locrit.

        Args:
            locrit_name: Name of the Locrit
            content: Memory content
            importance: Memory importance (0.0 to 1.0)
            metadata: Additional metadata

        Returns:
            Memory ID or None if error
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return None

        try:
            return await memory_service.add_memory(content, importance, metadata)
        except Exception as e:
            print(f"Error adding memory for {locrit_name}: {e}")
            return None

    async def delete_memory(self, locrit_name: str, memory_id: str) -> bool:
        """
        Delete a memory from a Locrit.

        Args:
            locrit_name: Name of the Locrit
            memory_id: ID of the memory to delete

        Returns:
            True if deletion succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.delete_memory(memory_id)
        except Exception as e:
            print(f"Error deleting memory for {locrit_name}: {e}")
            return False

    async def edit_concept(self, locrit_name: str, concept_id: str, name: str = None,
                          description: str = None, confidence: float = None) -> bool:
        """
        Edit a concept in a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            concept_id: ID of the concept to edit
            name: New concept name (optional)
            description: New concept description (optional)
            confidence: New confidence score (optional)

        Returns:
            True if edit succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.edit_concept(concept_id, name, description, confidence)
        except Exception as e:
            print(f"Error editing concept for {locrit_name}: {e}")
            return False

    async def delete_concept(self, locrit_name: str, concept_id: str) -> bool:
        """
        Delete a concept from a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            concept_id: ID of the concept to delete

        Returns:
            True if deletion succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.delete_concept(concept_id)
        except Exception as e:
            print(f"Error deleting concept for {locrit_name}: {e}")
            return False

    async def delete_session(self, locrit_name: str, session_id: str) -> bool:
        """
        Delete a session and all its messages from a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            session_id: ID of the session to delete

        Returns:
            True if deletion succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.delete_session(session_id)
        except Exception as e:
            print(f"Error deleting session for {locrit_name}: {e}")
            return False

    async def clear_all_memory(self, locrit_name: str) -> bool:
        """
        Clear all memory data for a Locrit.

        Args:
            locrit_name: Name of the Locrit

        Returns:
            True if clearing succeeds
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return False

        try:
            return await memory_service.clear_all_memory()
        except Exception as e:
            print(f"Error clearing all memory for {locrit_name}: {e}")
            return False

    async def get_message_by_id(self, locrit_name: str, message_id: str) -> Optional[Dict]:
        """
        Get a specific message by ID from a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            message_id: ID of the message

        Returns:
            Message data or None if not found
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return None

        try:
            return await memory_service.get_message_by_id(message_id)
        except Exception as e:
            print(f"Error getting message for {locrit_name}: {e}")
            return None

    async def get_session_by_id(self, locrit_name: str, session_id: str) -> Optional[Dict]:
        """
        Get a specific session by ID from a Locrit's memory.

        Args:
            locrit_name: Name of the Locrit
            session_id: ID of the session

        Returns:
            Session data or None if not found
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return None

        try:
            return await memory_service.get_session_by_id(session_id)
        except Exception as e:
            print(f"Error getting session for {locrit_name}: {e}")
            return None

    async def get_all_memories(self, locrit_name: str) -> List[Dict]:
        """
        Get all standalone memory entries for a Locrit.

        Args:
            locrit_name: Name of the Locrit

        Returns:
            List of memory entries
        """
        memory_service = await self.get_memory_service(locrit_name)
        if not memory_service:
            return []

        try:
            return await memory_service.get_all_memories()
        except Exception as e:
            print(f"Error getting all memories for {locrit_name}: {e}")
            return []


# Global instance
memory_manager = MemoryManagerService()