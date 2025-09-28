"""
Memory Manager Service - Manages per-Locrit Kuzu memory instances.
This service handles the creation and routing of memory requests to individual Locrit databases.
"""

from typing import Dict, Optional, Any, List
from .kuzu_memory_service import KuzuMemoryService
from .config_service import config_service


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
            return await memory_service.save_message(
                role=role,
                content=content,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )
        except Exception as e:
            print(f"Error saving message for {locrit_name}: {e}")
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
            return await memory_service.get_conversation_history(session_id, limit)
        except Exception as e:
            print(f"Error getting conversation history for {locrit_name}: {e}")
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
            return await memory_service.search_memories(query, limit)
        except Exception as e:
            print(f"Error searching memories for {locrit_name}: {e}")
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


# Global instance
memory_manager = MemoryManagerService()