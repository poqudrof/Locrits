"""
Basic Memory Adapter - implements BaseMemoryService interface via MCP
Provides persistent, structured knowledge storage using local Markdown files
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

from .interfaces import (
    BaseMemoryService, MemoryItem, MemorySearchResult,
    MemoryType, MemoryImportance
)

# Import MCP client tools
try:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters, stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  MCP not available - BasicMemoryAdapter will not work")


class BasicMemoryAdapter(BaseMemoryService):
    """
    Adapter for Basic Memory system via MCP (Model Context Protocol).

    Stores memories as structured Markdown files with semantic markup,
    enabling persistent AI conversations with rich context.
    """

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        super().__init__(locrit_name, config)

        if not MCP_AVAILABLE:
            raise RuntimeError("MCP package not available. Install with: pip install mcp")

        # Configuration
        self.memory_path = Path(config.get('database_path', 'data/memory')) / self._sanitize_name(locrit_name) / 'basic-memory'
        self.mcp_client = None
        self.session = None

        # Create directory
        self.memory_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize Locrit name for directory use."""
        import re
        return re.sub(r'[^\w\-_]', '_', name.lower())

    async def initialize(self) -> bool:
        """Initialize Basic Memory via MCP server."""
        try:
            # Set up MCP server parameters for basic-memory
            server_params = StdioServerParameters(
                command="uvx",
                args=["basic-memory"],
                env={
                    "BASIC_MEMORY_PATH": str(self.memory_path)
                }
            )

            # Initialize MCP client
            async with stdio_client(server_params) as (read, write):
                async with Client(read, write) as client:
                    self.mcp_client = client

                    # Initialize the session
                    await client.initialize()

                    self.is_initialized = True
                    print(f"📚 Basic Memory initialized for {self.locrit_name} at {self.memory_path}")
                    return True

        except Exception as e:
            print(f"❌ Failed to initialize Basic Memory: {e}")
            self.is_initialized = False
            return False

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        try:
            result = await self.mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            print(f"❌ MCP tool call failed ({tool_name}): {e}")
            raise

    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item as a Markdown note via Basic Memory."""
        if not self.is_initialized:
            raise RuntimeError("Memory service not initialized")

        try:
            # Convert MemoryItem to Basic Memory note format
            note_content = self._memory_to_markdown(item)

            # Use write_note MCP tool
            result = await self._call_mcp_tool("write_note", {
                "title": f"memory_{item.id}",
                "content": note_content,
                "type": item.memory_type.value,
                "tags": item.tags,
                "metadata": item.metadata
            })

            return item.id

        except Exception as e:
            print(f"❌ Failed to store memory in Basic Memory: {e}")
            raise

    def _memory_to_markdown(self, item: MemoryItem) -> str:
        """Convert MemoryItem to Markdown format."""
        md = f"""# {item.id}

## Content
{item.content}

## Metadata
- **Created:** {item.created_at.isoformat()}
- **Last Accessed:** {item.last_accessed.isoformat()}
- **Importance:** {item.importance}
- **Type:** {item.memory_type.value}
- **Tags:** {', '.join(item.tags)}

## Observations
{json.dumps(item.metadata, indent=2)}
"""
        return md

    def _markdown_to_memory(self, note_data: Dict[str, Any]) -> MemoryItem:
        """Convert Basic Memory note to MemoryItem."""
        # Parse the note structure
        content = note_data.get('content', '')
        title = note_data.get('title', str(uuid.uuid4()))

        # Extract metadata from frontmatter or content
        metadata = note_data.get('metadata', {})
        tags = note_data.get('tags', [])

        return MemoryItem(
            id=title.replace('memory_', ''),
            content=content,
            memory_type=MemoryType.GRAPH,
            importance=metadata.get('importance', 0.5),
            created_at=datetime.fromisoformat(metadata.get('created_at', datetime.now().isoformat())),
            last_accessed=datetime.now(),
            metadata=metadata,
            tags=tags
        )

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID from Basic Memory."""
        if not self.is_initialized:
            return None

        try:
            # Use read_note MCP tool
            result = await self._call_mcp_tool("read_note", {
                "title": f"memory_{memory_id}"
            })

            if not result:
                return None

            return self._markdown_to_memory(result)

        except Exception as e:
            print(f"❌ Failed to retrieve memory from Basic Memory: {e}")
            return None

    async def search_memories(self, query: str, limit: int = 10,
                            filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories using Basic Memory's semantic search."""
        if not self.is_initialized:
            return []

        try:
            # Use search MCP tool
            result = await self._call_mcp_tool("search", {
                "query": query,
                "limit": limit
            })

            search_results = []
            for note_data in result.get('results', []):
                memory_item = self._markdown_to_memory(note_data)

                search_results.append(MemorySearchResult(
                    item=memory_item,
                    relevance_score=note_data.get('score', 0.0),
                    similarity_score=note_data.get('similarity', None),
                    reasoning=note_data.get('reasoning', None)
                ))

            return search_results

        except Exception as e:
            print(f"❌ Failed to search memories in Basic Memory: {e}")
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory in Basic Memory."""
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

            # Store updated memory
            await self.store_memory(existing)
            return True

        except Exception as e:
            print(f"❌ Failed to update memory in Basic Memory: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Basic Memory."""
        if not self.is_initialized:
            return False

        try:
            # Basic Memory doesn't have direct delete in MCP tools
            # We could implement this by marking as deleted or archiving
            # For now, return False as not directly supported
            print(f"⚠️  Delete not directly supported in Basic Memory MCP")
            return False

        except Exception as e:
            print(f"❌ Failed to delete memory from Basic Memory: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories in Basic Memory."""
        if not self.is_initialized:
            return {}

        try:
            # Count files in memory directory
            memory_files = list(self.memory_path.glob("**/*.md"))
            total_size = sum(f.stat().st_size for f in memory_files)

            return {
                'total_memories': len(memory_files),
                'database_size_mb': total_size / (1024 * 1024),
                'service_type': 'basic_memory_mcp',
                'memory_directory': str(self.memory_path)
            }

        except Exception as e:
            print(f"❌ Failed to get memory stats from Basic Memory: {e}")
            return {}

    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories."""
        if not self.is_initialized:
            return 0

        # Basic Memory manages its own cleanup through SQLite index
        # We don't need to manually clean up
        return 0

    async def close(self) -> None:
        """Close Basic Memory MCP connection."""
        try:
            if self.mcp_client:
                # MCP client cleanup happens automatically with context manager
                self.mcp_client = None
            self.is_initialized = False
        except Exception as e:
            print(f"❌ Failed to close Basic Memory service: {e}")

    async def build_context(self, query: str, max_tokens: int = 1000) -> str:
        """
        Build context for LLM from relevant memories using Basic Memory.

        This is a special feature of Basic Memory - it can assemble
        relevant context from the knowledge graph.
        """
        if not self.is_initialized:
            return ""

        try:
            result = await self._call_mcp_tool("build_context", {
                "query": query,
                "max_tokens": max_tokens
            })

            return result.get('context', '')

        except Exception as e:
            print(f"❌ Failed to build context from Basic Memory: {e}")
            return ""
