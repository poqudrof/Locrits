"""
Kuzu Graph Database Adapter - implements BaseMemoryService interface
Wraps the existing KuzuMemoryService to conform to the standard interface
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .interfaces import (
    BaseMemoryService, GraphMemoryService, MemoryItem, MemorySearchResult,
    MemoryType, MemoryImportance
)
from ..kuzu_memory_service import KuzuMemoryService


class KuzuMemoryAdapter(GraphMemoryService):
    """Adapter that wraps KuzuMemoryService to implement BaseMemoryService interface."""

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        super().__init__(locrit_name, config)

        # Extract configuration
        base_path = config.get('database_path', 'data/memory')
        embedding_model = config.get('embedding_model', 'nomic-embed-text')
        embedding_dimension = config.get('embedding_dimension', 768)
        inference_mode = config.get('inference_mode', 'ollama')

        # Create wrapped Kuzu service
        self.kuzu_service = KuzuMemoryService(
            locrit_name=locrit_name,
            base_path=base_path,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            inference_mode=inference_mode
        )

    async def initialize(self) -> bool:
        """Initialize the Kuzu memory service."""
        try:
            result = await self.kuzu_service.initialize()
            self.is_initialized = result
            return result
        except Exception as e:
            print(f"❌ Failed to initialize Kuzu memory service: {e}")
            return False

    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item in Kuzu graph database."""
        if not self.is_initialized:
            raise RuntimeError("Memory service not initialized")

        # Convert MemoryItem to Kuzu format
        memory_data = {
            'content': item.content,
            'importance': item.importance,
            'created_at': item.created_at.isoformat(),
            'metadata': item.metadata,
            'tags': item.tags
        }

        # Store as concept or message depending on type
        try:
            await self.kuzu_service.store_concept(
                name=f"memory_{item.id}",
                description=item.content,
                importance=item.importance,
                metadata=memory_data
            )
            return item.id
        except Exception as e:
            print(f"❌ Failed to store memory in Kuzu: {e}")
            raise

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID from Kuzu."""
        if not self.is_initialized:
            return None

        try:
            # Query Kuzu for the concept
            result = await self.kuzu_service.get_concept(f"memory_{memory_id}")

            if not result:
                return None

            # Convert Kuzu format back to MemoryItem
            return MemoryItem(
                id=memory_id,
                content=result.get('description', ''),
                memory_type=MemoryType.GRAPH,
                importance=result.get('importance', 0.5),
                created_at=datetime.fromisoformat(result.get('created_at', datetime.now().isoformat())),
                last_accessed=datetime.now(),
                metadata=result.get('metadata', {}),
                tags=result.get('tags', [])
            )
        except Exception as e:
            print(f"❌ Failed to retrieve memory from Kuzu: {e}")
            return None

    async def search_memories(self, query: str, limit: int = 10,
                            filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories in Kuzu using vector similarity."""
        if not self.is_initialized:
            return []

        try:
            # Use Kuzu's vector search
            results = await self.kuzu_service.search_similar_concepts(
                query=query,
                top_k=limit
            )

            search_results = []
            for result in results:
                memory_item = MemoryItem(
                    id=result.get('id', str(uuid.uuid4())),
                    content=result.get('description', ''),
                    memory_type=MemoryType.GRAPH,
                    importance=result.get('importance', 0.5),
                    created_at=datetime.fromisoformat(result.get('created_at', datetime.now().isoformat())),
                    last_accessed=datetime.now(),
                    metadata=result.get('metadata', {}),
                    tags=result.get('tags', [])
                )

                search_results.append(MemorySearchResult(
                    item=memory_item,
                    relevance_score=result.get('score', 0.0),
                    similarity_score=result.get('similarity', None)
                ))

            return search_results
        except Exception as e:
            print(f"❌ Failed to search memories in Kuzu: {e}")
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory in Kuzu."""
        if not self.is_initialized:
            return False

        try:
            # Retrieve existing memory
            existing = await self.retrieve_memory(memory_id)
            if not existing:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)

            # Store updated version
            await self.store_memory(existing)
            return True
        except Exception as e:
            print(f"❌ Failed to update memory in Kuzu: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Kuzu."""
        if not self.is_initialized:
            return False

        try:
            # Delete concept from Kuzu
            await self.kuzu_service.delete_concept(f"memory_{memory_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete memory from Kuzu: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories in Kuzu."""
        if not self.is_initialized:
            return {}

        try:
            stats = await self.kuzu_service.get_database_stats()
            return {
                'total_memories': stats.get('total_concepts', 0),
                'total_relationships': stats.get('total_relationships', 0),
                'database_size_mb': stats.get('database_size_mb', 0),
                'service_type': 'kuzu_graph'
            }
        except Exception as e:
            print(f"❌ Failed to get memory stats from Kuzu: {e}")
            return {}

    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories from Kuzu."""
        if not self.is_initialized:
            return 0

        try:
            # This would require querying old concepts and deleting them
            # For now, return 0 as placeholder
            return 0
        except Exception as e:
            print(f"❌ Failed to cleanup memories in Kuzu: {e}")
            return 0

    async def close(self) -> None:
        """Close Kuzu connection and clean up resources."""
        try:
            await self.kuzu_service.close()
            self.is_initialized = False
        except Exception as e:
            print(f"❌ Failed to close Kuzu service: {e}")

    # GraphMemoryService-specific methods

    async def create_relationship(self, from_id: str, to_id: str,
                                 relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two memories in Kuzu graph."""
        if not self.is_initialized:
            return False

        try:
            await self.kuzu_service.create_relationship(
                from_concept=f"memory_{from_id}",
                to_concept=f"memory_{to_id}",
                relationship_type=relationship_type,
                properties=properties or {}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to create relationship in Kuzu: {e}")
            return False

    async def get_related_memories(self, memory_id: str, relationship_types: List[str] = None,
                                  max_depth: int = 2) -> List[MemorySearchResult]:
        """Get memories related through graph relationships in Kuzu."""
        if not self.is_initialized:
            return []

        try:
            related = await self.kuzu_service.get_related_concepts(
                concept_name=f"memory_{memory_id}",
                relationship_types=relationship_types,
                max_depth=max_depth
            )

            results = []
            for item in related:
                memory_item = MemoryItem(
                    id=item.get('id', str(uuid.uuid4())),
                    content=item.get('description', ''),
                    memory_type=MemoryType.GRAPH,
                    importance=item.get('importance', 0.5),
                    created_at=datetime.fromisoformat(item.get('created_at', datetime.now().isoformat())),
                    last_accessed=datetime.now(),
                    metadata=item.get('metadata', {}),
                    tags=item.get('tags', [])
                )

                results.append(MemorySearchResult(
                    item=memory_item,
                    relevance_score=item.get('relevance', 0.5)
                ))

            return results
        except Exception as e:
            print(f"❌ Failed to get related memories from Kuzu: {e}")
            return []

    async def get_memory_network(self, center_id: str, radius: int = 2) -> Dict[str, Any]:
        """Get the network of memories around a central memory in Kuzu graph."""
        if not self.is_initialized:
            return {}

        try:
            network = await self.kuzu_service.get_concept_network(
                concept_name=f"memory_{center_id}",
                radius=radius
            )
            return network
        except Exception as e:
            print(f"❌ Failed to get memory network from Kuzu: {e}")
            return {}
