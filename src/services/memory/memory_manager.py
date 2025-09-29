"""
Memory Manager - Main orchestrator for the modular memory system.

Coordinates between graph and vector memory services, provides intelligent
memory storage decisions, and manages memory update scheduling.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict

from .interfaces import (
    MemoryOrchestrator, MemoryDecisionEngine, MemoryItem, MemorySearchResult,
    MemoryType, MemoryImportance, MemoryDecision
)
from .config import MemoryConfig, MemoryConfigManager
from .graph_memory_service import KuzuGraphMemoryService
from .vector_memory_service import KuzuVectorMemoryService


class IntelligentMemoryManager(MemoryOrchestrator, MemoryDecisionEngine):
    """Main memory manager that orchestrates between graph and vector services."""

    def __init__(self, locrit_name: str, config_path: Optional[str] = None):
        """Initialize the memory manager."""
        self.locrit_name = locrit_name

        # Load configuration
        self.config_manager = MemoryConfigManager(config_path)
        self.config = self.config_manager.load_config()

        super().__init__(locrit_name, self.config)

        # Initialize services
        self.graph_service: Optional[KuzuGraphMemoryService] = None
        self.vector_service: Optional[KuzuVectorMemoryService] = None

        # Memory update tracking
        self.message_count = 0
        self.last_update_time = datetime.now()
        self.pending_memories: List[Dict[str, Any]] = []

        # Performance metrics
        self.stats = {
            "total_memories_stored": 0,
            "graph_memories_stored": 0,
            "vector_memories_stored": 0,
            "hybrid_memories_stored": 0,
            "searches_performed": 0,
            "last_cleanup_time": None
        }

    async def initialize(self) -> bool:
        """Initialize all memory services."""
        try:
            success = True

            # Initialize graph service if enabled
            if self.config.graph.enabled:
                self.graph_service = KuzuGraphMemoryService(self.locrit_name, self.config)
                graph_success = await self.graph_service.initialize()
                if not graph_success:
                    print(f"Warning: Graph memory service failed to initialize for {self.locrit_name}")
                    success = False

            # Initialize vector service if enabled
            if self.config.vector.enabled:
                self.vector_service = KuzuVectorMemoryService(self.locrit_name, self.config)
                vector_success = await self.vector_service.initialize()
                if not vector_success:
                    print(f"Warning: Vector memory service failed to initialize for {self.locrit_name}")
                    success = False

            # At least one service must be working
            if not self.graph_service and not self.vector_service:
                print(f"Error: No memory services available for {self.locrit_name}")
                return False

            print(f"Memory manager initialized for {self.locrit_name}")
            print(f"  - Graph service: {'✓' if self.graph_service and self.graph_service.is_initialized else '✗'}")
            print(f"  - Vector service: {'✓' if self.vector_service and self.vector_service.is_initialized else '✗'}")

            return success

        except Exception as e:
            print(f"Error initializing memory manager for {self.locrit_name}: {e}")
            return False

    async def decide_memory_storage(self, content: str, context: Dict[str, Any]) -> MemoryType:
        """Decide how to store content based on its characteristics."""
        try:
            decision = await self.analyze_content_for_storage(content, context)
            return decision.memory_type
        except Exception as e:
            print(f"Error deciding memory storage: {e}")
            # Default to hybrid if both services available, otherwise use what's available
            if self.graph_service and self.vector_service:
                return MemoryType.HYBRID
            elif self.graph_service:
                return MemoryType.GRAPH
            elif self.vector_service:
                return MemoryType.VECTOR
            else:
                return MemoryType.GRAPH  # fallback

    async def analyze_content_for_storage(self, content: str, context: Dict[str, Any]) -> MemoryDecision:
        """Analyze content and decide how it should be stored."""
        content_lower = content.lower()

        # Analyze content characteristics
        factual_indicators = ['fact', 'data', 'statistic', 'number', 'date', 'name', 'address', 'phone']
        experiential_indicators = ['felt', 'experienced', 'remember', 'seemed', 'atmosphere', 'vibe', 'impression']
        emotional_indicators = ['happy', 'sad', 'angry', 'excited', 'worried', 'love', 'hate', 'feel']
        conceptual_indicators = ['concept', 'idea', 'principle', 'theory', 'pattern', 'theme']
        temporal_indicators = ['then', 'next', 'after', 'before', 'sequence', 'order']

        # Score different aspects
        factual_score = sum(1 for indicator in factual_indicators if indicator in content_lower)
        experiential_score = sum(1 for indicator in experiential_indicators if indicator in content_lower)
        emotional_score = sum(1 for indicator in emotional_indicators if indicator in content_lower)
        conceptual_score = sum(1 for indicator in conceptual_indicators if indicator in content_lower)
        temporal_score = sum(1 for indicator in temporal_indicators if indicator in content_lower)

        # Context-based scoring
        role = context.get('role', 'user')
        content_type = context.get('content_type', 'message')

        # Boost scores based on context
        if role == 'system':
            factual_score += 2
        if content_type == 'fact':
            factual_score += 3
        if content_type == 'experience':
            experiential_score += 3
        if content_type == 'opinion':
            emotional_score += 2

        # Check content length and complexity
        word_count = len(content.split())
        has_structure = any(char in content for char in ['.', ':', ';', '-', '•'])

        # Decision logic
        total_indicators = factual_score + experiential_score + emotional_score + conceptual_score

        # Determine memory type
        if factual_score >= 2 or temporal_score >= 2 or (word_count < 20 and has_structure):
            memory_type = MemoryType.GRAPH
            reasoning = "Content appears factual, structured, or temporal - suitable for graph storage"
            tags = ['fact', 'structured']
        elif experiential_score >= 2 or emotional_score >= 2:
            memory_type = MemoryType.VECTOR
            reasoning = "Content appears experiential or emotional - suitable for vector storage"
            tags = ['experience', 'emotional']
        elif conceptual_score >= 2:
            memory_type = MemoryType.VECTOR
            reasoning = "Content appears conceptual - suitable for vector storage"
            tags = ['concept', 'abstract']
        elif word_count > 50 or total_indicators == 0:
            memory_type = MemoryType.VECTOR
            reasoning = "Long content with unclear structure - defaulting to vector storage"
            tags = ['long_content', 'fuzzy']
        else:
            # When in doubt, use hybrid if available
            if self.graph_service and self.vector_service:
                memory_type = MemoryType.HYBRID
                reasoning = "Ambiguous content - storing in both systems"
                tags = ['hybrid', 'ambiguous']
            elif self.graph_service:
                memory_type = MemoryType.GRAPH
                reasoning = "Defaulting to graph storage"
                tags = ['default', 'graph']
            else:
                memory_type = MemoryType.VECTOR
                reasoning = "Defaulting to vector storage"
                tags = ['default', 'vector']

        # Determine importance
        importance_indicators = ['important', 'critical', 'remember', 'key', 'vital', 'essential']
        importance_score = sum(1 for indicator in importance_indicators if indicator in content_lower)

        if importance_score >= 2:
            importance = 0.9
        elif context.get('user_marked_important', False):
            importance = 0.8
        elif factual_score >= 3:
            importance = 0.7
        elif experiential_score >= 2:
            importance = 0.6
        else:
            importance = 0.5

        return MemoryDecision(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags,
            reasoning=reasoning
        )

    async def store_memory_intelligently(self, content: str, context: Dict[str, Any],
                                        importance: float = 0.5) -> List[str]:
        """Store memory using the most appropriate storage strategy."""
        try:
            # Analyze and decide storage strategy
            decision = await self.analyze_content_for_storage(content, context)

            # Override importance if provided
            if importance != 0.5:
                decision.importance = importance

            # Create memory item
            memory_item = MemoryItem(
                id=context.get('id'),
                content=content,
                memory_type=decision.memory_type,
                importance=decision.importance,
                created_at=context.get('timestamp', datetime.now()),
                last_accessed=datetime.now(),
                metadata=context,
                tags=decision.tags
            )

            # Store based on decision
            stored_ids = []

            if decision.memory_type == MemoryType.GRAPH and self.graph_service:
                graph_id = await self.graph_service.store_memory(memory_item)
                stored_ids.append(graph_id)
                self.stats["graph_memories_stored"] += 1

            elif decision.memory_type == MemoryType.VECTOR and self.vector_service:
                vector_id = await self.vector_service.store_memory(memory_item)
                stored_ids.append(vector_id)
                self.stats["vector_memories_stored"] += 1

            elif decision.memory_type == MemoryType.HYBRID:
                # Store in both systems
                if self.graph_service:
                    graph_item = memory_item
                    graph_item.metadata['storage_type'] = 'graph'
                    graph_id = await self.graph_service.store_memory(graph_item)
                    stored_ids.append(graph_id)

                if self.vector_service:
                    vector_item = memory_item
                    vector_item.metadata['storage_type'] = 'vector'
                    vector_id = await self.vector_service.store_memory(vector_item)
                    stored_ids.append(vector_id)

                self.stats["hybrid_memories_stored"] += 1

            self.stats["total_memories_stored"] += 1

            # Log the decision for debugging
            if self.config.debug:
                print(f"Memory stored: {decision.reasoning}")
                print(f"  Type: {decision.memory_type.value}")
                print(f"  IDs: {stored_ids}")
                print(f"  Tags: {decision.tags}")

            return stored_ids

        except Exception as e:
            print(f"Error storing memory intelligently: {e}")
            return []

    async def comprehensive_search(self, query: str, search_strategy: str = "auto",
                                  limit: int = 10) -> List[MemorySearchResult]:
        """Search across all memory types with intelligent strategy selection."""
        try:
            self.stats["searches_performed"] += 1

            # Determine search strategy
            if search_strategy == "auto":
                search_strategy = await self._determine_search_strategy(query)

            all_results = []

            # Search based on strategy
            if search_strategy == "graph_first" and self.graph_service:
                # Search graph first, then vector if needed
                graph_results = await self.graph_service.search_memories(query, limit)
                all_results.extend(graph_results)

                if len(graph_results) < limit and self.vector_service:
                    remaining = limit - len(graph_results)
                    vector_results = await self.vector_service.search_memories(query, remaining)
                    all_results.extend(vector_results)

            elif search_strategy == "vector_first" and self.vector_service:
                # Search vector first, then graph if needed
                vector_results = await self.vector_service.search_memories(query, limit)
                all_results.extend(vector_results)

                if len(vector_results) < limit and self.graph_service:
                    remaining = limit - len(vector_results)
                    graph_results = await self.graph_service.search_memories(query, remaining)
                    all_results.extend(graph_results)

            elif search_strategy == "parallel":
                # Search both simultaneously and merge
                tasks = []
                if self.graph_service:
                    tasks.append(self.graph_service.search_memories(query, limit // 2))
                if self.vector_service:
                    tasks.append(self.vector_service.search_memories(query, limit // 2))

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if not isinstance(result, Exception):
                            all_results.extend(result)

            else:
                # Fallback: search available services
                if self.graph_service:
                    graph_results = await self.graph_service.search_memories(query, limit)
                    all_results.extend(graph_results)

                if self.vector_service:
                    vector_results = await self.vector_service.search_memories(query, limit)
                    all_results.extend(vector_results)

            # Remove duplicates and sort by relevance
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

            return unique_results[:limit]

        except Exception as e:
            print(f"Error in comprehensive search: {e}")
            return []

    async def _determine_search_strategy(self, query: str) -> str:
        """Determine the best search strategy for a query."""
        query_lower = query.lower()

        # Check for factual query indicators
        factual_words = ['what', 'when', 'where', 'who', 'how many', 'list', 'name', 'date']
        experiential_words = ['feel', 'experience', 'remember', 'impression', 'like', 'similar']

        factual_score = sum(1 for word in factual_words if word in query_lower)
        experiential_score = sum(1 for word in experiential_words if word in query_lower)

        if factual_score > experiential_score:
            return "graph_first"
        elif experiential_score > factual_score:
            return "vector_first"
        else:
            return "parallel"

    def _deduplicate_results(self, results: List[MemorySearchResult]) -> List[MemorySearchResult]:
        """Remove duplicate results based on content similarity."""
        unique_results = []
        seen_content = set()

        for result in results:
            # Simple deduplication based on content
            content_key = result.item.content[:100].lower().strip()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        return unique_results

    async def update_memories_from_conversation(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a conversation and update memories accordingly."""
        try:
            self.message_count += len(messages)
            update_results = {
                "messages_processed": len(messages),
                "memories_created": 0,
                "memories_updated": 0,
                "should_force_update": False
            }

            # Add messages to pending memories
            for message in messages:
                self.pending_memories.append({
                    "content": message.get("content", ""),
                    "context": message,
                    "timestamp": datetime.now()
                })

            # Check if we should update memories
            should_update = await self.should_update_memories({
                "message_count": self.message_count,
                "pending_count": len(self.pending_memories),
                "last_update": self.last_update_time
            })

            if should_update:
                update_results.update(await self._process_pending_memories())
                self.last_update_time = datetime.now()
                self.pending_memories.clear()

            return update_results

        except Exception as e:
            print(f"Error updating memories from conversation: {e}")
            return {"error": str(e)}

    async def should_update_memories(self, conversation_context: Dict[str, Any]) -> bool:
        """Decide whether memories should be updated based on conversation state."""
        try:
            message_count = conversation_context.get("message_count", 0)
            pending_count = conversation_context.get("pending_count", 0)
            last_update = conversation_context.get("last_update", datetime.now())

            # Check auto-update interval
            if self.config.updates.auto_update:
                if message_count >= self.config.updates.update_interval:
                    return True

            # Check time-based update
            time_since_update = datetime.now() - last_update
            if time_since_update > timedelta(hours=1):  # Update at least hourly
                return True

            # Check pending memory threshold
            if pending_count >= self.config.updates.max_batch_size:
                return True

            # Check for user request
            if conversation_context.get("user_requested_update", False):
                return True

            return False

        except Exception as e:
            print(f"Error checking if should update memories: {e}")
            return False

    async def _process_pending_memories(self) -> Dict[str, Any]:
        """Process all pending memories and store them."""
        try:
            results = {"memories_created": 0, "memories_updated": 0, "errors": 0}

            if self.config.updates.batch_update:
                # Process in batches
                batch_size = self.config.updates.max_batch_size
                for i in range(0, len(self.pending_memories), batch_size):
                    batch = self.pending_memories[i:i + batch_size]
                    batch_results = await self._process_memory_batch(batch)
                    results["memories_created"] += batch_results["created"]
                    results["errors"] += batch_results["errors"]
            else:
                # Process individually
                for memory_data in self.pending_memories:
                    try:
                        stored_ids = await self.store_memory_intelligently(
                            memory_data["content"],
                            memory_data["context"]
                        )
                        if stored_ids:
                            results["memories_created"] += len(stored_ids)
                    except Exception as e:
                        print(f"Error processing individual memory: {e}")
                        results["errors"] += 1

            return results

        except Exception as e:
            print(f"Error processing pending memories: {e}")
            return {"error": str(e)}

    async def _process_memory_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of memories."""
        results = {"created": 0, "errors": 0}

        # Group by predicted storage type for efficiency
        graph_memories = []
        vector_memories = []
        hybrid_memories = []

        for memory_data in batch:
            try:
                decision = await self.analyze_content_for_storage(
                    memory_data["content"],
                    memory_data["context"]
                )

                memory_item = MemoryItem(
                    id=memory_data["context"].get("id"),
                    content=memory_data["content"],
                    memory_type=decision.memory_type,
                    importance=decision.importance,
                    created_at=memory_data["timestamp"],
                    last_accessed=datetime.now(),
                    metadata=memory_data["context"],
                    tags=decision.tags
                )

                if decision.memory_type == MemoryType.GRAPH:
                    graph_memories.append(memory_item)
                elif decision.memory_type == MemoryType.VECTOR:
                    vector_memories.append(memory_item)
                else:
                    hybrid_memories.append(memory_item)

            except Exception as e:
                print(f"Error preparing memory for batch: {e}")
                results["errors"] += 1

        # Store batches
        tasks = []
        if graph_memories and self.graph_service:
            tasks.append(self._store_batch(self.graph_service, graph_memories))
        if vector_memories and self.vector_service:
            tasks.append(self._store_batch(self.vector_service, vector_memories))
        if hybrid_memories:
            tasks.append(self._store_hybrid_batch(hybrid_memories))

        if tasks:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in batch_results:
                if not isinstance(result, Exception):
                    results["created"] += result

        return results

    async def _store_batch(self, service, memories: List[MemoryItem]) -> int:
        """Store a batch of memories in a single service."""
        stored_count = 0
        for memory in memories:
            try:
                stored_id = await service.store_memory(memory)
                if stored_id:
                    stored_count += 1
            except Exception as e:
                print(f"Error storing memory in batch: {e}")
        return stored_count

    async def _store_hybrid_batch(self, memories: List[MemoryItem]) -> int:
        """Store a batch of hybrid memories in both services."""
        stored_count = 0
        for memory in memories:
            try:
                stored_ids = []
                if self.graph_service:
                    graph_id = await self.graph_service.store_memory(memory)
                    if graph_id:
                        stored_ids.append(graph_id)

                if self.vector_service:
                    vector_id = await self.vector_service.store_memory(memory)
                    if vector_id:
                        stored_ids.append(vector_id)

                if stored_ids:
                    stored_count += len(stored_ids)

            except Exception as e:
                print(f"Error storing hybrid memory in batch: {e}")

        return stored_count

    async def prioritize_memories_for_cleanup(self, memories: List[MemoryItem]) -> List[str]:
        """Prioritize which memories should be cleaned up when storage is full."""
        try:
            # Score memories for cleanup priority (higher score = more likely to be cleaned)
            scored_memories = []

            for memory in memories:
                cleanup_score = 0.0

                # Age factor (older = higher cleanup score)
                age_days = (datetime.now() - memory.created_at).days
                cleanup_score += min(age_days / 365.0, 1.0) * 0.3

                # Importance factor (lower importance = higher cleanup score)
                cleanup_score += (1.0 - memory.importance) * 0.4

                # Access frequency (less accessed = higher cleanup score)
                days_since_access = (datetime.now() - memory.last_accessed).days
                cleanup_score += min(days_since_access / 30.0, 1.0) * 0.3

                scored_memories.append((memory.id, cleanup_score))

            # Sort by cleanup score (highest first) and return IDs
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            return [memory_id for memory_id, _ in scored_memories]

        except Exception as e:
            print(f"Error prioritizing memories for cleanup: {e}")
            return []

    async def get_memory_overview(self) -> Dict[str, Any]:
        """Get comprehensive overview of memory status."""
        try:
            overview = {
                "locrit_name": self.locrit_name,
                "services_status": {
                    "graph": self.graph_service.is_initialized if self.graph_service else False,
                    "vector": self.vector_service.is_initialized if self.vector_service else False
                },
                "statistics": self.stats.copy(),
                "configuration": {
                    "auto_update": self.config.updates.auto_update,
                    "update_interval": self.config.updates.update_interval,
                    "graph_enabled": self.config.graph.enabled,
                    "vector_enabled": self.config.vector.enabled
                },
                "pending_memories": len(self.pending_memories),
                "last_update": str(self.last_update_time)
            }

            # Get service-specific stats
            if self.graph_service and self.graph_service.is_initialized:
                graph_stats = await self.graph_service.get_memory_stats()
                overview["graph_stats"] = graph_stats

            if self.vector_service and self.vector_service.is_initialized:
                vector_stats = await self.vector_service.get_memory_stats()
                overview["vector_stats"] = vector_stats

            return overview

        except Exception as e:
            print(f"Error getting memory overview: {e}")
            return {"error": str(e)}

    async def cleanup_old_memories(self, retention_days: int = None) -> Dict[str, int]:
        """Clean up old memories from both services."""
        if retention_days is None:
            retention_days = self.config.retention.default_retention_days

        cleanup_results = {"graph_cleaned": 0, "vector_cleaned": 0, "total_cleaned": 0}

        try:
            tasks = []
            if self.graph_service and self.graph_service.is_initialized:
                tasks.append(self.graph_service.cleanup_old_memories(retention_days))

            if self.vector_service and self.vector_service.is_initialized:
                tasks.append(self.vector_service.cleanup_old_memories(retention_days))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                if len(results) >= 1 and not isinstance(results[0], Exception):
                    cleanup_results["graph_cleaned"] = results[0]

                if len(results) >= 2 and not isinstance(results[1], Exception):
                    cleanup_results["vector_cleaned"] = results[1]

            cleanup_results["total_cleaned"] = cleanup_results["graph_cleaned"] + cleanup_results["vector_cleaned"]
            self.stats["last_cleanup_time"] = datetime.now()

            return cleanup_results

        except Exception as e:
            print(f"Error cleaning up memories: {e}")
            return {"error": str(e)}

    async def force_memory_update(self) -> Dict[str, Any]:
        """Force an immediate memory update regardless of schedule."""
        try:
            if not self.pending_memories:
                return {"message": "No pending memories to process"}

            results = await self._process_pending_memories()
            self.last_update_time = datetime.now()
            self.pending_memories.clear()
            self.message_count = 0  # Reset counter

            return {
                "status": "completed",
                "results": results,
                "update_time": str(self.last_update_time)
            }

        except Exception as e:
            print(f"Error forcing memory update: {e}")
            return {"error": str(e)}

    async def close(self) -> None:
        """Close all memory services."""
        try:
            tasks = []
            if self.graph_service:
                tasks.append(self.graph_service.close())
            if self.vector_service:
                tasks.append(self.vector_service.close())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            print(f"Memory manager closed for {self.locrit_name}")

        except Exception as e:
            print(f"Error closing memory manager: {e}")