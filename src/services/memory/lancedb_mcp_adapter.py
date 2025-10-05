"""
LanceDB MCP Memory Adapter - Integration via Model Context Protocol
Uses LanceDB MCP server for vector-based semantic search and memory storage.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .interfaces import BaseMemoryService, MemoryItem, MemorySearchResult, MemoryType


class LanceDBMCPAdapter(BaseMemoryService):
    """
    LanceDB memory service using MCP (Model Context Protocol) integration.

    Features:
    - Vector-based semantic search via MCP
    - Remote-capable architecture
    - Standardized MCP protocol
    - Efficient vector operations
    """

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        super().__init__(locrit_name, config)

        # LanceDB MCP configuration
        self.db_path = Path(config.get('database_path', 'data/memory')) / locrit_name / 'lancedb_mcp'
        self.table_name = f"{locrit_name.replace(' ', '_').lower()}_memories"
        self.embedding_dimension = config.get('embedding_dimension', 768)

        # MCP client components
        self.mcp_client: Optional[ClientSession] = None
        self._session_context = None
        self._transport_context = None

    async def initialize(self) -> bool:
        """Initialize LanceDB MCP server connection."""
        try:
            # Ensure directory exists
            self.db_path.mkdir(parents=True, exist_ok=True)

            # Configure MCP server parameters
            server_params = StdioServerParameters(
                command="uvx",
                args=["mcp-lance-db"],
                env={
                    "LANCEDB_URI": str(self.db_path),
                    "LANCEDB_TABLE": self.table_name
                }
            )

            # Connect to MCP server
            self._transport_context = stdio_client(server_params)
            read, write = await self._transport_context.__aenter__()

            from mcp import ClientSession
            self._session_context = ClientSession(read, write)
            self.mcp_client = await self._session_context.__aenter__()

            # Initialize MCP client
            await self.mcp_client.initialize()

            # Create table if it doesn't exist
            try:
                await self._create_table_if_needed()
            except Exception as e:
                print(f"⚠️  Table creation warning (may already exist): {e}")

            print(f"✅ Connected to LanceDB MCP server for {self.locrit_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize LanceDB MCP adapter: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _create_table_if_needed(self):
        """Create LanceDB table via MCP if it doesn't exist."""
        try:
            # Call MCP tool to create table
            result = await self.mcp_client.call_tool(
                "create_table",
                arguments={
                    "name": self.table_name,
                    "dimension": self.embedding_dimension
                }
            )
            print(f"✅ Created LanceDB table: {self.table_name}")
        except Exception as e:
            # Table might already exist
            pass

    async def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.

        Note: The MCP server should handle embeddings internally.
        If not, we'll need to call an external embedding service.
        """
        # Call MCP tool for embedding (if available)
        try:
            result = await self.mcp_client.call_tool(
                "embed_text",
                arguments={"text": text}
            )
            return result.get("embedding", [])
        except:
            # Fallback: use Ollama for embeddings
            import httpx
            ollama_url = self.config.get('ollama_url', 'http://localhost:11434')
            embedding_model = self.config.get('embedding_model', 'nomic-embed-text')

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ollama_url}/api/embeddings",
                    json={
                        "model": embedding_model,
                        "prompt": text
                    }
                )
                data = response.json()
                return data.get("embedding", [])

    async def store_memory(self, memory: MemoryItem) -> str:
        """Store a memory item via MCP."""
        if not self.mcp_client:
            raise RuntimeError("LanceDB MCP client not initialized")

        try:
            # Get embedding for the content
            embedding = await self._get_embedding(memory.content)

            # Prepare metadata
            metadata = {
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type.value,
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
                "tags": json.dumps(memory.tags),
                **memory.metadata
            }

            # Add vector to LanceDB via MCP
            result = await self.mcp_client.call_tool(
                "add_vector",
                arguments={
                    "table_name": self.table_name,
                    "vector": embedding,
                    "metadata": metadata
                }
            )

            print(f"💾 Stored memory in LanceDB MCP: {memory.id[:8]}...")
            return memory.id

        except Exception as e:
            print(f"❌ Failed to store memory via MCP: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID via MCP."""
        if not self.mcp_client:
            raise RuntimeError("LanceDB MCP client not initialized")

        try:
            # Search by ID metadata
            result = await self.mcp_client.call_tool(
                "query_by_metadata",
                arguments={
                    "table_name": self.table_name,
                    "filter": f"id = '{memory_id}'",
                    "limit": 1
                }
            )

            if not result or not result.get("results"):
                return None

            data = result["results"][0]

            # Convert to MemoryItem
            return MemoryItem(
                id=data['id'],
                content=data['content'],
                memory_type=MemoryType(data.get('memory_type', 'GRAPH')),
                importance=data.get('importance', 0.5),
                created_at=datetime.fromisoformat(data['created_at']),
                last_accessed=datetime.fromisoformat(data['last_accessed']),
                access_count=data.get('access_count', 0),
                metadata={k: v for k, v in data.items() if k not in [
                    'id', 'content', 'memory_type', 'importance',
                    'created_at', 'last_accessed', 'access_count', 'tags'
                ]},
                tags=json.loads(data.get('tags', '[]'))
            )

        except Exception as e:
            print(f"❌ Failed to retrieve memory via MCP: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Search memories using semantic similarity via MCP."""
        if not self.mcp_client:
            raise RuntimeError("LanceDB MCP client not initialized")

        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)

            # Perform similarity search via MCP
            result = await self.mcp_client.call_tool(
                "search_vectors",
                arguments={
                    "table_name": self.table_name,
                    "vector": query_embedding,
                    "limit": limit
                }
            )

            results = []
            for item in result.get("results", []):
                data = item.get("metadata", {})

                # Apply filters if provided
                if filters:
                    if 'min_importance' in filters:
                        if data.get('importance', 0) < filters['min_importance']:
                            continue
                    if 'memory_type' in filters:
                        if data.get('memory_type') != filters['memory_type']:
                            continue

                # Convert to MemoryItem
                memory_item = MemoryItem(
                    id=data['id'],
                    content=data['content'],
                    memory_type=MemoryType(data.get('memory_type', 'GRAPH')),
                    importance=data.get('importance', 0.5),
                    created_at=datetime.fromisoformat(data['created_at']),
                    last_accessed=datetime.fromisoformat(data['last_accessed']),
                    access_count=data.get('access_count', 0),
                    metadata={k: v for k, v in data.items() if k not in [
                        'id', 'content', 'memory_type', 'importance',
                        'created_at', 'last_accessed', 'access_count', 'tags'
                    ]},
                    tags=json.loads(data.get('tags', '[]'))
                )

                # Get relevance score from search result
                relevance_score = item.get("score", 0.5)

                results.append(MemorySearchResult(
                    item=memory_item,
                    relevance_score=relevance_score,
                    matched_fields=['content']
                ))

            return results

        except Exception as e:
            print(f"❌ Failed to search memories via MCP: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory item via MCP."""
        try:
            # Retrieve existing memory
            existing = await self.retrieve_memory(memory_id)
            if not existing:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)

            # Delete old version and re-add
            await self.delete_memory(memory_id)
            await self.store_memory(existing)

            return True

        except Exception as e:
            print(f"❌ Failed to update memory via MCP: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory via MCP."""
        if not self.mcp_client:
            raise RuntimeError("LanceDB MCP client not initialized")

        try:
            result = await self.mcp_client.call_tool(
                "delete_by_metadata",
                arguments={
                    "table_name": self.table_name,
                    "filter": f"id = '{memory_id}'"
                }
            )

            print(f"🗑️  Deleted memory via MCP: {memory_id[:8]}...")
            return True

        except Exception as e:
            print(f"❌ Failed to delete memory via MCP: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if not self.mcp_client:
            return {"total_memories": 0, "error": "MCP client not initialized"}

        try:
            result = await self.mcp_client.call_tool(
                "get_table_stats",
                arguments={"table_name": self.table_name}
            )

            return {
                "total_memories": result.get("count", 0),
                "storage_type": "lancedb_mcp",
                "table_name": self.table_name,
                "db_path": str(self.db_path),
                **result
            }

        except Exception as e:
            print(f"❌ Failed to get stats via MCP: {e}")
            return {"total_memories": 0, "error": str(e)}

    async def cleanup_old_memories(self, days_old: int = 30) -> int:
        """
        Clean up old memories that haven't been accessed recently.

        Args:
            days_old: Remove memories older than this many days

        Returns:
            Number of memories deleted
        """
        if not self.mcp_client:
            return 0

        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()

            result = await self.mcp_client.call_tool(
                "delete_by_metadata",
                arguments={
                    "table_name": self.table_name,
                    "filter": f"last_accessed < '{cutoff_iso}'"
                }
            )

            deleted = result.get("deleted_count", 0)
            print(f"🧹 Cleaned up {deleted} old memories via MCP (older than {days_old} days)")
            return deleted

        except Exception as e:
            print(f"❌ Failed to cleanup old memories via MCP: {e}")
            return 0

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics about the memory store.

        Returns:
            Dictionary with memory statistics
        """
        return await self.get_stats()

    async def close(self) -> None:
        """Close MCP connection."""
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._transport_context:
                await self._transport_context.__aexit__(None, None, None)

            self.mcp_client = None
            print(f"✅ Closed LanceDB MCP connection for {self.locrit_name}")

        except Exception as e:
            print(f"⚠️  Error closing LanceDB MCP connection: {e}")
