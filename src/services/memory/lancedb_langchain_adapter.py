"""
LanceDB LangChain Memory Adapter - Direct Python integration
Uses LanceDB with LangChain for vector-based semantic search and memory storage.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from langchain_community.vectorstores import LanceDB
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

from .interfaces import BaseMemoryService, MemoryItem, MemorySearchResult, MemoryType


class LanceDBLangChainAdapter(BaseMemoryService):
    """
    LanceDB memory service using direct Python integration via LangChain.

    Features:
    - Vector-based semantic search
    - Persistent storage with LanceDB
    - LangChain integration for easy document handling
    - Configurable embedding models (Ollama)
    """

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        super().__init__(locrit_name, config)

        # LanceDB configuration
        self.db_path = Path(config.get('database_path', 'data/memory')) / locrit_name / 'lancedb_langchain'
        self.embedding_model = config.get('embedding_model', 'nomic-embed-text')
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434')

        # LangChain components
        self.embeddings = None
        self.vectorstore = None
        self.table_name = f"{locrit_name.replace(' ', '_').lower()}_memories"

    async def initialize(self) -> bool:
        """Initialize LanceDB and LangChain components."""
        try:
            # Ensure directory exists
            self.db_path.mkdir(parents=True, exist_ok=True)

            # Initialize Ollama embeddings
            self.embeddings = OllamaEmbeddings(
                model=self.embedding_model,
                base_url=self.ollama_url
            )

            # Initialize or connect to LanceDB
            import lancedb
            db = lancedb.connect(str(self.db_path))

            # Check if table exists
            table_names = db.table_names()
            if self.table_name in table_names:
                # Load existing vectorstore
                self.vectorstore = LanceDB(
                    connection=db,
                    table_name=self.table_name,
                    embedding=self.embeddings
                )
                print(f"✅ Connected to existing LanceDB table: {self.table_name}")
            else:
                # Create new empty vectorstore
                # We'll initialize it with a dummy document to create the table
                dummy_doc = Document(
                    page_content="Initialization document",
                    metadata={"type": "system", "timestamp": datetime.now().isoformat()}
                )
                self.vectorstore = LanceDB.from_documents(
                    documents=[dummy_doc],
                    embedding=self.embeddings,
                    connection=db,
                    table_name=self.table_name
                )
                print(f"✅ Created new LanceDB table: {self.table_name}")

            return True

        except Exception as e:
            print(f"❌ Failed to initialize LanceDB LangChain adapter: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def store_memory(self, memory: MemoryItem) -> str:
        """Store a memory item in LanceDB."""
        if not self.vectorstore:
            raise RuntimeError("LanceDB not initialized")

        try:
            # Convert MemoryItem to LangChain Document
            doc = Document(
                page_content=memory.content,
                metadata={
                    "id": memory.id,
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat(),
                    "access_count": memory.access_count,
                    "tags": json.dumps(memory.tags),
                    **memory.metadata
                }
            )

            # Add to vectorstore (runs in thread pool to avoid blocking)
            await asyncio.to_thread(
                self.vectorstore.add_documents,
                documents=[doc],
                ids=[memory.id]
            )

            print(f"💾 Stored memory in LanceDB: {memory.id[:8]}...")
            return memory.id

        except Exception as e:
            print(f"❌ Failed to store memory in LanceDB: {e}")
            raise

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID."""
        if not self.vectorstore:
            raise RuntimeError("LanceDB not initialized")

        try:
            # LanceDB doesn't have direct ID lookup via LangChain interface
            # We'll search for it using metadata filter
            import lancedb
            db = lancedb.connect(str(self.db_path))
            table = db.open_table(self.table_name)

            # Query by metadata
            results = table.search().where(f"id = '{memory_id}'").limit(1).to_list()

            if not results:
                return None

            result = results[0]

            # Convert back to MemoryItem
            return MemoryItem(
                id=result['id'],
                content=result['text'],  # LanceDB stores content as 'text'
                memory_type=MemoryType(result.get('memory_type', 'GRAPH')),
                importance=result.get('importance', 0.5),
                created_at=datetime.fromisoformat(result['created_at']),
                last_accessed=datetime.fromisoformat(result['last_accessed']),
                access_count=result.get('access_count', 0),
                metadata={k: v for k, v in result.items() if k not in [
                    'id', 'text', 'vector', 'memory_type', 'importance',
                    'created_at', 'last_accessed', 'access_count', 'tags'
                ]},
                tags=json.loads(result.get('tags', '[]'))
            )

        except Exception as e:
            print(f"❌ Failed to retrieve memory from LanceDB: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Search memories using semantic similarity."""
        if not self.vectorstore:
            raise RuntimeError("LanceDB not initialized")

        try:
            # Perform similarity search
            docs_and_scores = await asyncio.to_thread(
                self.vectorstore.similarity_search_with_score,
                query=query,
                k=limit
            )

            results = []
            for doc, score in docs_and_scores:
                # Apply filters if provided
                if filters:
                    if 'min_importance' in filters:
                        if doc.metadata.get('importance', 0) < filters['min_importance']:
                            continue
                    if 'memory_type' in filters:
                        if doc.metadata.get('memory_type') != filters['memory_type']:
                            continue

                # Convert to MemoryItem
                memory_item = MemoryItem(
                    id=doc.metadata['id'],
                    content=doc.page_content,
                    memory_type=MemoryType(doc.metadata.get('memory_type', 'GRAPH')),
                    importance=doc.metadata.get('importance', 0.5),
                    created_at=datetime.fromisoformat(doc.metadata['created_at']),
                    last_accessed=datetime.fromisoformat(doc.metadata['last_accessed']),
                    access_count=doc.metadata.get('access_count', 0),
                    metadata={k: v for k, v in doc.metadata.items() if k not in [
                        'id', 'memory_type', 'importance', 'created_at',
                        'last_accessed', 'access_count', 'tags'
                    ]},
                    tags=json.loads(doc.metadata.get('tags', '[]'))
                )

                # Create search result (LanceDB returns distance, convert to similarity score)
                # Lower distance = higher similarity, normalize to 0-1 range
                relevance_score = 1.0 / (1.0 + score)

                results.append(MemorySearchResult(
                    item=memory_item,
                    relevance_score=relevance_score,
                    matched_fields=['content']  # Semantic search matches content
                ))

            return results

        except Exception as e:
            print(f"❌ Failed to search memories in LanceDB: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.

        Note: LanceDB doesn't support in-place updates easily via LangChain.
        We'll delete and re-add the memory.
        """
        try:
            # Retrieve existing memory
            existing = await self.retrieve_memory(memory_id)
            if not existing:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)

            # Delete old version
            await self.delete_memory(memory_id)

            # Re-add updated version
            await self.store_memory(existing)

            return True

        except Exception as e:
            print(f"❌ Failed to update memory in LanceDB: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from LanceDB."""
        try:
            import lancedb
            db = lancedb.connect(str(self.db_path))
            table = db.open_table(self.table_name)

            # Delete by ID filter
            table.delete(f"id = '{memory_id}'")

            print(f"🗑️  Deleted memory: {memory_id[:8]}...")
            return True

        except Exception as e:
            print(f"❌ Failed to delete memory from LanceDB: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        try:
            import lancedb
            db = lancedb.connect(str(self.db_path))
            table = db.open_table(self.table_name)

            count = table.count_rows()

            return {
                "total_memories": count,
                "storage_type": "lancedb_langchain",
                "embedding_model": self.embedding_model,
                "table_name": self.table_name,
                "db_path": str(self.db_path)
            }

        except Exception as e:
            print(f"❌ Failed to get LanceDB stats: {e}")
            return {"total_memories": 0, "error": str(e)}

    async def cleanup_old_memories(self, days_old: int = 30) -> int:
        """
        Clean up old memories that haven't been accessed recently.

        Args:
            days_old: Remove memories older than this many days

        Returns:
            Number of memories deleted
        """
        try:
            from datetime import datetime, timedelta
            import lancedb

            cutoff_date = datetime.now() - timedelta(days=days_old)

            db = lancedb.connect(str(self.db_path))
            table = db.open_table(self.table_name)

            # Get count before deletion
            initial_count = table.count_rows()

            # Delete old records
            cutoff_iso = cutoff_date.isoformat()
            table.delete(f"last_accessed < '{cutoff_iso}'")

            # Get count after deletion
            final_count = table.count_rows()
            deleted = initial_count - final_count

            print(f"🧹 Cleaned up {deleted} old memories (older than {days_old} days)")
            return deleted

        except Exception as e:
            print(f"❌ Failed to cleanup old memories: {e}")
            return 0

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics about the memory store.

        Returns:
            Dictionary with memory statistics
        """
        return await self.get_stats()

    async def close(self) -> None:
        """Close LanceDB connection."""
        # LangChain's LanceDB doesn't require explicit cleanup
        self.vectorstore = None
        self.embeddings = None
        print(f"✅ Closed LanceDB LangChain connection for {self.locrit_name}")
