"""
Memory Service Factory - creates appropriate memory service based on configuration
Allows easy switching between different memory backend implementations
"""

from typing import Dict, Any, Optional
from enum import Enum

from .interfaces import BaseMemoryService
from .kuzu_adapter import KuzuMemoryAdapter
from .plaintext_memory_service import PlainTextMemoryService
from .basic_memory_adapter import BasicMemoryAdapter
from .lancedb_langchain_adapter import LanceDBLangChainAdapter
from .lancedb_mcp_adapter import LanceDBMCPAdapter


class MemoryServiceType(Enum):
    """Available memory service implementations."""
    KUZU_GRAPH = "kuzu_graph"          # Kuzu graph database (sophisticated, may have compatibility issues)
    PLAINTEXT_FILE = "plaintext_file"  # Simple text file storage (stable, easy to debug)
    BASIC_MEMORY = "basic_memory"      # Basic Memory via MCP (Markdown-based knowledge graph)
    LANCEDB_LANGCHAIN = "lancedb_langchain"  # LanceDB with LangChain (vector search, Python integration)
    LANCEDB_MCP = "lancedb_mcp"        # LanceDB via MCP (vector search, MCP protocol)
    DISABLED = "disabled"              # No memory persistence


class MemoryServiceFactory:
    """Factory for creating memory service instances."""

    @staticmethod
    def create_memory_service(
        locrit_name: str,
        service_type: str,
        config: Dict[str, Any]
    ) -> Optional[BaseMemoryService]:
        """
        Create a memory service instance based on the specified type.

        Args:
            locrit_name: Name of the Locrit
            service_type: Type of memory service (kuzu_graph, plaintext_file, disabled)
            config: Configuration dictionary for the memory service

        Returns:
            BaseMemoryService instance or None if disabled

        Raises:
            ValueError: If service_type is not recognized
        """

        try:
            service_enum = MemoryServiceType(service_type)
        except ValueError:
            raise ValueError(
                f"Unknown memory service type: {service_type}. "
                f"Available types: {[t.value for t in MemoryServiceType]}"
            )

        if service_enum == MemoryServiceType.DISABLED:
            print(f"📝 Memory service disabled for {locrit_name}")
            return None

        elif service_enum == MemoryServiceType.KUZU_GRAPH:
            print(f"🗄️  Creating Kuzu graph memory service for {locrit_name}")
            return KuzuMemoryAdapter(locrit_name, config)

        elif service_enum == MemoryServiceType.PLAINTEXT_FILE:
            print(f"📄 Creating plaintext file memory service for {locrit_name}")
            return PlainTextMemoryService(locrit_name, config)

        elif service_enum == MemoryServiceType.BASIC_MEMORY:
            print(f"📚 Creating Basic Memory (MCP) service for {locrit_name}")
            return BasicMemoryAdapter(locrit_name, config)

        elif service_enum == MemoryServiceType.LANCEDB_LANGCHAIN:
            print(f"🚀 Creating LanceDB LangChain service for {locrit_name}")
            return LanceDBLangChainAdapter(locrit_name, config)

        elif service_enum == MemoryServiceType.LANCEDB_MCP:
            print(f"🔌 Creating LanceDB MCP service for {locrit_name}")
            return LanceDBMCPAdapter(locrit_name, config)

        else:
            raise ValueError(f"Unsupported memory service type: {service_type}")

    @staticmethod
    def get_available_services() -> Dict[str, Dict[str, str]]:
        """
        Get information about available memory service types.

        Returns:
            Dictionary with service type as key and info dict as value
        """
        return {
            MemoryServiceType.KUZU_GRAPH.value: {
                "name": "Kuzu Graph Database",
                "description": "Advanced graph-based memory with relationships and vector search",
                "pros": "Sophisticated queries, relationships, semantic search",
                "cons": "May have compatibility issues with Python 3.13, higher complexity",
                "stability": "experimental"
            },
            MemoryServiceType.PLAINTEXT_FILE.value: {
                "name": "Plain Text Files",
                "description": "Simple file-based storage using JSON and text files",
                "pros": "Stable, easy to debug, human-readable, no dependencies",
                "cons": "Limited query capabilities, slower for large datasets",
                "stability": "stable"
            },
            MemoryServiceType.BASIC_MEMORY.value: {
                "name": "Basic Memory (MCP)",
                "description": "Markdown-based knowledge graph with semantic search via MCP",
                "pros": "Rich semantic markup, bi-directional read/write, knowledge graph, integrates with Obsidian",
                "cons": "Requires MCP, newer/experimental, external dependency",
                "stability": "experimental"
            },
            MemoryServiceType.LANCEDB_LANGCHAIN.value: {
                "name": "LanceDB (LangChain)",
                "description": "Vector database with LangChain integration for semantic search",
                "pros": "Fast vector search, persistent storage, multimodal support, Python native",
                "cons": "Requires embeddings model, higher memory usage",
                "stability": "stable"
            },
            MemoryServiceType.LANCEDB_MCP.value: {
                "name": "LanceDB (MCP)",
                "description": "Vector database via MCP for remote-capable semantic search",
                "pros": "Standardized protocol, remote-capable, efficient vector ops",
                "cons": "Requires MCP setup, newer integration, external dependency",
                "stability": "experimental"
            },
            MemoryServiceType.DISABLED.value: {
                "name": "Disabled",
                "description": "No memory persistence",
                "pros": "No overhead, no crashes",
                "cons": "Locrit won't remember conversations",
                "stability": "stable"
            }
        }

    @staticmethod
    def recommend_service(python_version: str = None) -> str:
        """
        Recommend a memory service based on environment.

        Args:
            python_version: Python version string (e.g., "3.13")

        Returns:
            Recommended service type
        """
        # If Python 3.13+, recommend plaintext to avoid Kuzu compatibility issues
        if python_version and python_version >= "3.13":
            return MemoryServiceType.PLAINTEXT_FILE.value

        # Otherwise, Kuzu is safe to use
        return MemoryServiceType.KUZU_GRAPH.value


class MemoryServiceManager:
    """Manages memory service instances for multiple Locrits."""

    def __init__(self):
        self.services: Dict[str, BaseMemoryService] = {}

    async def get_or_create_service(
        self,
        locrit_name: str,
        service_type: str,
        config: Dict[str, Any]
    ) -> Optional[BaseMemoryService]:
        """
        Get existing service or create new one for a Locrit.

        Args:
            locrit_name: Name of the Locrit
            service_type: Type of memory service
            config: Configuration dictionary

        Returns:
            BaseMemoryService instance or None
        """

        # Check if service already exists
        if locrit_name in self.services:
            return self.services[locrit_name]

        # Create new service
        service = MemoryServiceFactory.create_memory_service(
            locrit_name, service_type, config
        )

        if service:
            # Initialize the service
            initialized = await service.initialize()
            if initialized:
                self.services[locrit_name] = service
                return service
            else:
                print(f"❌ Failed to initialize memory service for {locrit_name}")
                return None

        return None

    async def close_service(self, locrit_name: str) -> None:
        """Close and remove a memory service."""
        if locrit_name in self.services:
            await self.services[locrit_name].close()
            del self.services[locrit_name]

    async def close_all_services(self) -> None:
        """Close all memory services."""
        for service in self.services.values():
            await service.close()
        self.services.clear()

    def get_service(self, locrit_name: str) -> Optional[BaseMemoryService]:
        """Get existing service without creating new one."""
        return self.services.get(locrit_name)


# Global instance for managing memory services
memory_service_manager = MemoryServiceManager()
