"""
Base interfaces and abstract classes for the modular memory system.

This module defines the contracts that all memory services must implement,
ensuring consistent behavior across graph and vector memory storage.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class MemoryType(Enum):
    """Types of memory storage strategies."""
    GRAPH = "graph"          # Precise, structured memories (facts, events, relationships)
    VECTOR = "vector"        # Fuzzy, semantic memories (experiences, impressions, themes)
    HYBRID = "hybrid"        # Stored in both for different access patterns


class MemoryImportance(Enum):
    """Importance levels for memory prioritization."""
    CRITICAL = 1.0      # Must never be forgotten
    HIGH = 0.8          # Very important to remember
    MEDIUM = 0.5        # Moderately important
    LOW = 0.2           # Can be forgotten if space is needed
    EPHEMERAL = 0.1     # Temporary, likely to be cleaned up


@dataclass
class MemoryItem:
    """Base memory item structure."""
    id: str
    content: str
    memory_type: MemoryType
    importance: float
    created_at: datetime
    last_accessed: datetime
    metadata: Dict[str, Any]
    tags: List[str]


@dataclass
class MemorySearchResult:
    """Result from memory search operations."""
    item: MemoryItem
    relevance_score: float
    similarity_score: Optional[float] = None
    reasoning: Optional[str] = None


class BaseMemoryService(ABC):
    """Abstract base class for all memory services."""

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        self.locrit_name = locrit_name
        self.config = config
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the memory service."""
        pass

    @abstractmethod
    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item and return its ID."""
        pass

    @abstractmethod
    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID."""
        pass

    @abstractmethod
    async def search_memories(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories matching the query."""
        pass

    @abstractmethod
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory."""
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        pass

    @abstractmethod
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        pass

    @abstractmethod
    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the memory service and clean up resources."""
        pass


class GraphMemoryService(BaseMemoryService):
    """Abstract class for graph-based memory services.

    Handles precise, structured memories like:
    - Facts and events
    - Relationships between entities
    - Structured knowledge
    - Temporal sequences
    """

    @abstractmethod
    async def create_relationship(self, from_id: str, to_id: str,
                                 relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two memory items."""
        pass

    @abstractmethod
    async def get_related_memories(self, memory_id: str, relationship_types: List[str] = None,
                                  max_depth: int = 2) -> List[MemorySearchResult]:
        """Get memories related to the given memory through graph relationships."""
        pass

    @abstractmethod
    async def get_memory_network(self, center_id: str, radius: int = 2) -> Dict[str, Any]:
        """Get the network of memories around a central memory."""
        pass


class VectorMemoryService(BaseMemoryService):
    """Abstract class for vector-based memory services.

    Handles fuzzy, semantic memories like:
    - Experiences and impressions
    - Emotional associations
    - Thematic content
    - Contextual similarities
    """

    @abstractmethod
    async def find_similar_memories(self, query: str, threshold: float = 0.7,
                                   limit: int = 10) -> List[MemorySearchResult]:
        """Find memories similar to the query using vector similarity."""
        pass

    @abstractmethod
    async def get_memory_clusters(self, num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Group memories into semantic clusters."""
        pass

    @abstractmethod
    async def get_memory_themes(self, timeframe_days: int = 30) -> List[Dict[str, Any]]:
        """Extract common themes from recent memories."""
        pass


class MemoryOrchestrator(ABC):
    """Abstract orchestrator that coordinates between different memory services."""

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        self.locrit_name = locrit_name
        self.config = config
        self.graph_service: Optional[GraphMemoryService] = None
        self.vector_service: Optional[VectorMemoryService] = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize all memory services."""
        pass

    @abstractmethod
    async def decide_memory_storage(self, content: str, context: Dict[str, Any]) -> MemoryType:
        """Decide how to store a piece of content based on its characteristics."""
        pass

    @abstractmethod
    async def store_memory_intelligently(self, content: str, context: Dict[str, Any],
                                        importance: float = 0.5) -> List[str]:
        """Store memory using the most appropriate storage strategy."""
        pass

    @abstractmethod
    async def comprehensive_search(self, query: str, search_strategy: str = "auto",
                                  limit: int = 10) -> List[MemorySearchResult]:
        """Search across all memory types with intelligent strategy selection."""
        pass

    @abstractmethod
    async def update_memories_from_conversation(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a conversation and update memories accordingly."""
        pass


@dataclass
class MemoryDecision:
    """Represents a decision made by the LLM about memory storage."""
    content: str
    memory_type: MemoryType
    importance: float
    tags: List[str]
    reasoning: str
    relationships: Optional[List[Dict[str, Any]]] = None


class MemoryDecisionEngine(ABC):
    """Abstract class for LLM-driven memory decision making."""

    @abstractmethod
    async def analyze_content_for_storage(self, content: str,
                                         context: Dict[str, Any]) -> MemoryDecision:
        """Analyze content and decide how it should be stored."""
        pass

    @abstractmethod
    async def should_update_memories(self, conversation_context: Dict[str, Any]) -> bool:
        """Decide whether memories should be updated based on conversation state."""
        pass

    @abstractmethod
    async def prioritize_memories_for_cleanup(self, memories: List[MemoryItem]) -> List[str]:
        """Prioritize which memories should be cleaned up when storage is full."""
        pass