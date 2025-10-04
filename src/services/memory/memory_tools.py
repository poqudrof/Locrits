"""
LLM Tools for Memory Management

This module provides tool functions that allow LLMs to interact with and make decisions
about the memory system. These tools give the LLM agency over its own memory management.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .memory_manager import IntelligentMemoryManager
from .interfaces import MemoryType, MemoryImportance


class MemoryTools:
    """Tool functions for LLM memory management."""

    def __init__(self, memory_manager: IntelligentMemoryManager):
        self.memory_manager = memory_manager
        self.locrit_name = memory_manager.locrit_name

    # Core Memory Storage Tools

    async def store_graph_memory(self, content: str, memory_type: str = "message",
                                importance: float = 0.5, relationships: List[Dict] = None,
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a memory as structured graph data.

        Use this for:
        - Facts, events, and precise information
        - Data with clear relationships
        - Temporal sequences
        - Structured knowledge

        Args:
            content: The content to remember
            memory_type: Type of memory ('message', 'fact', 'event', 'concept')
            importance: Importance score (0.0 to 1.0)
            relationships: List of relationships to create
            metadata: Additional metadata

        Returns:
            Dictionary with storage results
        """
        try:
            context = metadata or {}
            context.update({
                "graph_type": memory_type,
                "storage_decision": "llm_directed_graph",
                "timestamp": datetime.now(),
                "relationships": relationships or []
            })

            # Force graph storage
            if self.memory_manager.graph_service:
                from .interfaces import MemoryItem
                memory_item = MemoryItem(
                    id=context.get('id'),
                    content=content,
                    memory_type=MemoryType.GRAPH,
                    importance=importance,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    metadata=context,
                    tags=["llm_stored", "graph", memory_type]
                )

                stored_id = await self.memory_manager.graph_service.store_memory(memory_item)

                # Create relationships if specified
                if relationships and stored_id:
                    for rel in relationships:
                        await self.memory_manager.graph_service.create_relationship(
                            from_id=rel.get("from_id", stored_id),
                            to_id=rel.get("to_id"),
                            relationship_type=rel.get("type", "RELATES_TO"),
                            properties=rel.get("properties", {})
                        )

                return {
                    "success": True,
                    "memory_id": stored_id,
                    "storage_type": "graph",
                    "memory_type": memory_type,
                    "relationships_created": len(relationships) if relationships else 0
                }
            else:
                return {
                    "success": False,
                    "error": "Graph memory service not available",
                    "fallback": "Use store_vector_memory instead"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_preview": content[:100]
            }

    async def store_vector_memory(self, content: str, vector_type: str = "souvenir",
                                 importance: float = 0.5, emotional_tone: str = "neutral",
                                 tags: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a memory as semantic vector data.

        Use this for:
        - Experiences, impressions, and feelings
        - Fuzzy or ambiguous content
        - Thematic information
        - Content for similarity search

        Args:
            content: The content to remember
            vector_type: Type of vector memory ('souvenir', 'impression', 'theme')
            importance: Importance score (0.0 to 1.0)
            emotional_tone: Emotional tone of the memory
            tags: List of tags for categorization
            metadata: Additional metadata

        Returns:
            Dictionary with storage results
        """
        try:
            context = metadata or {}
            context.update({
                "vector_type": vector_type,
                "emotional_tone": emotional_tone,
                "storage_decision": "llm_directed_vector",
                "timestamp": datetime.now()
            })

            # Force vector storage
            if self.memory_manager.vector_service:
                from .interfaces import MemoryItem
                memory_item = MemoryItem(
                    id=context.get('id'),
                    content=content,
                    memory_type=MemoryType.VECTOR,
                    importance=importance,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    metadata=context,
                    tags=(tags or []) + ["llm_stored", "vector", vector_type]
                )

                stored_id = await self.memory_manager.vector_service.store_memory(memory_item)

                return {
                    "success": True,
                    "memory_id": stored_id,
                    "storage_type": "vector",
                    "vector_type": vector_type,
                    "emotional_tone": emotional_tone
                }
            else:
                return {
                    "success": False,
                    "error": "Vector memory service not available",
                    "fallback": "Use store_graph_memory instead"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_preview": content[:100]
            }

    async def store_hybrid_memory(self, content: str, importance: float = 0.5,
                                 graph_metadata: Dict[str, Any] = None,
                                 vector_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a memory in both graph and vector systems.

        Use this for:
        - Important content that benefits from both precise and fuzzy retrieval
        - Content with both factual and experiential aspects
        - Memories you want maximum accessibility for

        Args:
            content: The content to remember
            importance: Importance score (0.0 to 1.0)
            graph_metadata: Metadata specific to graph storage
            vector_metadata: Metadata specific to vector storage

        Returns:
            Dictionary with storage results
        """
        try:
            context = {
                "storage_decision": "llm_directed_hybrid",
                "timestamp": datetime.now()
            }

            stored_ids = await self.memory_manager.store_memory_intelligently(
                content=content,
                context=context,
                importance=importance
            )

            # Override the automatic decision to force hybrid storage
            additional_results = []

            # Store in graph if not already there
            if self.memory_manager.graph_service:
                graph_context = context.copy()
                graph_context.update(graph_metadata or {})
                graph_result = await self.store_graph_memory(
                    content, importance=importance, metadata=graph_context
                )
                if graph_result["success"]:
                    additional_results.append(graph_result["memory_id"])

            # Store in vector if not already there
            if self.memory_manager.vector_service:
                vector_context = context.copy()
                vector_context.update(vector_metadata or {})
                vector_result = await self.store_vector_memory(
                    content, importance=importance, metadata=vector_context
                )
                if vector_result["success"]:
                    additional_results.append(vector_result["memory_id"])

            all_ids = stored_ids + additional_results

            return {
                "success": True,
                "memory_ids": all_ids,
                "storage_type": "hybrid",
                "total_stored": len(all_ids),
                "graph_available": self.memory_manager.graph_service is not None,
                "vector_available": self.memory_manager.vector_service is not None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_preview": content[:100]
            }

    # Memory Retrieval Tools

    async def search_graph_memory(self, query: str, limit: int = 10,
                                 filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search through graph (structured) memories.

        Use this for:
        - Finding specific facts or events
        - Searching by relationships
        - Precise, structured queries

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Search filters (e.g., memory_type, date_range)

        Returns:
            Dictionary with search results
        """
        try:
            if not self.memory_manager.graph_service:
                return {
                    "success": False,
                    "error": "Graph memory service not available",
                    "results": []
                }

            results = await self.memory_manager.graph_service.search_memories(
                query, limit, filters
            )

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "results": [
                    {
                        "memory_id": r.item.id,
                        "content": r.item.content,
                        "relevance_score": r.relevance_score,
                        "memory_type": r.item.metadata.get("graph_type", "unknown"),
                        "importance": r.item.importance,
                        "created_at": str(r.item.created_at),
                        "tags": r.item.tags,
                        "reasoning": r.reasoning
                    }
                    for r in results
                ]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

    async def search_vector_memory(self, query: str, limit: int = 10,
                                  similarity_threshold: float = 0.7,
                                  vector_type: str = None) -> Dict[str, Any]:
        """
        Search through vector (semantic) memories.

        Use this for:
        - Finding similar experiences or impressions
        - Semantic similarity search
        - Fuzzy or thematic queries

        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            vector_type: Filter by vector type ('souvenir', 'impression', 'theme')

        Returns:
            Dictionary with search results
        """
        try:
            if not self.memory_manager.vector_service:
                return {
                    "success": False,
                    "error": "Vector memory service not available",
                    "results": []
                }

            filters = {"similarity_threshold": similarity_threshold}
            if vector_type:
                filters["vector_type"] = vector_type

            results = await self.memory_manager.vector_service.search_memories(
                query, limit, filters
            )

            return {
                "success": True,
                "query": query,
                "similarity_threshold": similarity_threshold,
                "total_results": len(results),
                "results": [
                    {
                        "memory_id": r.item.id,
                        "content": r.item.content,
                        "similarity_score": r.similarity_score,
                        "vector_type": r.item.metadata.get("vector_type", "unknown"),
                        "emotional_tone": r.item.metadata.get("emotional_tone", "neutral"),
                        "importance": r.item.importance,
                        "created_at": str(r.item.created_at),
                        "tags": r.item.tags
                    }
                    for r in results
                ]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

    async def search_all_memory(self, query: str, limit: int = 10,
                               strategy: str = "auto") -> Dict[str, Any]:
        """
        Search across all memory types with intelligent strategy.

        Use this for:
        - Comprehensive searches
        - When unsure which memory type to search
        - Finding the most relevant memories regardless of storage type

        Args:
            query: Search query
            limit: Maximum number of results
            strategy: Search strategy ('auto', 'graph_first', 'vector_first', 'parallel')

        Returns:
            Dictionary with search results
        """
        try:
            results = await self.memory_manager.comprehensive_search(
                query, strategy, limit
            )

            return {
                "success": True,
                "query": query,
                "strategy": strategy,
                "total_results": len(results),
                "results": [
                    {
                        "memory_id": r.item.id,
                        "content": r.item.content,
                        "relevance_score": r.relevance_score,
                        "similarity_score": r.similarity_score,
                        "storage_type": r.item.memory_type.value,
                        "importance": r.item.importance,
                        "created_at": str(r.item.created_at),
                        "tags": r.item.tags,
                        "reasoning": r.reasoning
                    }
                    for r in results
                ]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

    # Memory Management Tools

    async def analyze_memory_decision(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze content and get AI recommendation for memory storage.

        Use this to:
        - Understand how the AI would classify content
        - Get storage recommendations before committing
        - Learn about memory classification logic

        Args:
            content: Content to analyze
            context: Additional context information

        Returns:
            Dictionary with analysis and recommendation
        """
        try:
            decision = await self.memory_manager.analyze_content_for_storage(
                content, context or {}
            )

            return {
                "success": True,
                "content_preview": content[:100],
                "recommendation": {
                    "memory_type": decision.memory_type.value,
                    "importance": decision.importance,
                    "tags": decision.tags,
                    "reasoning": decision.reasoning
                },
                "available_services": {
                    "graph": self.memory_manager.graph_service is not None,
                    "vector": self.memory_manager.vector_service is not None
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_preview": content[:100]
            }

    async def update_memory_now(self, force: bool = False) -> Dict[str, Any]:
        """
        Trigger immediate memory update processing.

        Use this to:
        - Process pending memories immediately
        - Force memory consolidation after important conversations
        - Manually trigger memory updates

        Args:
            force: Whether to force update regardless of schedule

        Returns:
            Dictionary with update results
        """
        try:
            if force:
                results = await self.memory_manager.force_memory_update()
            else:
                # Check if update is needed
                should_update = await self.memory_manager.should_update_memories({
                    "message_count": self.memory_manager.message_count,
                    "pending_count": len(self.memory_manager.pending_memories),
                    "last_update": self.memory_manager.last_update_time
                })

                if should_update:
                    results = await self.memory_manager.force_memory_update()
                else:
                    results = {
                        "status": "not_needed",
                        "message": "Memory update not needed at this time",
                        "pending_memories": len(self.memory_manager.pending_memories)
                    }

            return {
                "success": True,
                "update_results": results,
                "timestamp": str(datetime.now())
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_memory_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of memory systems.

        Use this to:
        - Check memory system health
        - See memory statistics
        - Monitor pending updates

        Returns:
            Dictionary with memory status
        """
        try:
            overview = await self.memory_manager.get_memory_overview()

            return {
                "success": True,
                "locrit_name": self.locrit_name,
                "status": overview,
                "recommendations": self._generate_status_recommendations(overview)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_status_recommendations(self, overview: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on memory status."""
        recommendations = []

        # Check service availability
        services = overview.get("services_status", {})
        if not services.get("graph") and not services.get("vector"):
            recommendations.append("⚠️ No memory services are available - check configuration")
        elif not services.get("graph"):
            recommendations.append("ℹ️ Graph memory disabled - only vector storage available")
        elif not services.get("vector"):
            recommendations.append("ℹ️ Vector memory disabled - only graph storage available")

        # Check pending memories
        pending = overview.get("pending_memories", 0)
        if pending > 20:
            recommendations.append(f"🔄 {pending} memories pending - consider running update_memory_now()")
        elif pending > 0:
            recommendations.append(f"📝 {pending} memories pending for next update")

        # Check memory counts
        stats = overview.get("statistics", {})
        total_memories = stats.get("total_memories_stored", 0)
        if total_memories == 0:
            recommendations.append("🆕 No memories stored yet - start conversations to build memory")
        elif total_memories > 1000:
            recommendations.append("📚 Large memory collection - consider periodic cleanup")

        # Check last update time
        last_update = overview.get("last_update")
        if last_update:
            try:
                last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                hours_since_update = (datetime.now() - last_update_time).total_seconds() / 3600
                if hours_since_update > 24:
                    recommendations.append("⏰ Memory not updated in 24+ hours")
            except:
                pass

        return recommendations

    async def cleanup_old_memories(self, retention_days: int = None) -> Dict[str, Any]:
        """
        Clean up old, low-importance memories.

        Use this to:
        - Free up storage space
        - Remove outdated memories
        - Maintain memory system performance

        Args:
            retention_days: Number of days to retain memories (uses config default if None)

        Returns:
            Dictionary with cleanup results
        """
        try:
            results = await self.memory_manager.cleanup_old_memories(retention_days)

            return {
                "success": True,
                "cleanup_results": results,
                "retention_days": retention_days or self.memory_manager.config.retention.default_retention_days,
                "timestamp": str(datetime.now())
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # Relationship and Network Tools

    async def create_memory_relationship(self, from_memory_id: str, to_memory_id: str,
                                       relationship_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a relationship between two memories.

        Use this to:
        - Link related facts or events
        - Create knowledge networks
        - Establish causal or temporal relationships

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship ('RELATES_TO', 'CAUSES', 'FOLLOWS', etc.)
            properties: Additional relationship properties

        Returns:
            Dictionary with relationship creation results
        """
        try:
            if not self.memory_manager.graph_service:
                return {
                    "success": False,
                    "error": "Graph memory service required for relationships"
                }

            success = await self.memory_manager.graph_service.create_relationship(
                from_memory_id, to_memory_id, relationship_type, properties
            )

            return {
                "success": success,
                "from_memory_id": from_memory_id,
                "to_memory_id": to_memory_id,
                "relationship_type": relationship_type,
                "properties": properties or {}
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "from_memory_id": from_memory_id,
                "to_memory_id": to_memory_id
            }

    async def get_memory_network(self, memory_id: str, radius: int = 2) -> Dict[str, Any]:
        """
        Get the network of memories connected to a specific memory.

        Use this to:
        - Explore memory relationships
        - Find connected information
        - Understand knowledge networks

        Args:
            memory_id: Central memory ID
            radius: How many relationship hops to include

        Returns:
            Dictionary with network information
        """
        try:
            if not self.memory_manager.graph_service:
                return {
                    "success": False,
                    "error": "Graph memory service required for networks"
                }

            network = await self.memory_manager.graph_service.get_memory_network(
                memory_id, radius
            )

            return {
                "success": True,
                "center_memory_id": memory_id,
                "network": network
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "center_memory_id": memory_id
            }


# Tool function wrappers for easy integration with LLM frameworks

def create_memory_tools(memory_manager: IntelligentMemoryManager) -> Dict[str, callable]:
    """Create a dictionary of memory tool functions for LLM use."""
    tools = MemoryTools(memory_manager)

    return {
        # Storage tools
        "store_graph_memory": tools.store_graph_memory,
        "store_vector_memory": tools.store_vector_memory,
        "store_hybrid_memory": tools.store_hybrid_memory,

        # Retrieval tools
        "search_graph_memory": tools.search_graph_memory,
        "search_vector_memory": tools.search_vector_memory,
        "search_all_memory": tools.search_all_memory,

        # Management tools
        "analyze_memory_decision": tools.analyze_memory_decision,
        "update_memory_now": tools.update_memory_now,
        "get_memory_status": tools.get_memory_status,
        "cleanup_old_memories": tools.cleanup_old_memories,

        # Relationship tools
        "create_memory_relationship": tools.create_memory_relationship,
        "get_memory_network": tools.get_memory_network,
    }