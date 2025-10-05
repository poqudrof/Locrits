"""
Plain Text File Memory Service - implements BaseMemoryService interface
Simple file-based storage for memories using JSON and plain text files
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import re

from .interfaces import (
    BaseMemoryService, MemoryItem, MemorySearchResult,
    MemoryType, MemoryImportance
)


class PlainTextMemoryService(BaseMemoryService):
    """
    Simple file-based memory service that stores memories as plain text files.

    Structure:
    - memories/ directory contains individual memory files
    - index.json contains metadata and searchable index
    - Each memory is stored as {memory_id}.txt with JSON header
    """

    def __init__(self, locrit_name: str, config: Dict[str, Any]):
        super().__init__(locrit_name, config)

        # Configuration
        base_path = config.get('database_path', 'data/memory')
        self.memory_dir = Path(base_path) / self._sanitize_name(locrit_name) / 'plaintext'
        self.memories_path = self.memory_dir / 'memories'
        self.index_path = self.memory_dir / 'index.json'

        # In-memory index for fast searches
        self.index: Dict[str, Dict[str, Any]] = {}

        # Create directories
        self.memories_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize Locrit name for use as directory name."""
        return re.sub(r'[^\w\-_]', '_', name.lower())

    async def initialize(self) -> bool:
        """Initialize the plain text memory service."""
        try:
            # Load existing index if it exists
            if self.index_path.exists():
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            else:
                self.index = {}
                await self._save_index()

            self.is_initialized = True
            print(f"📄 Plain text memory service initialized for {self.locrit_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize plain text memory service: {e}")
            return False

    async def _save_index(self) -> None:
        """Save the in-memory index to disk."""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Failed to save index: {e}")

    def _memory_to_dict(self, item: MemoryItem) -> Dict[str, Any]:
        """Convert MemoryItem to dictionary for storage."""
        return {
            'id': item.id,
            'content': item.content,
            'memory_type': item.memory_type.value,
            'importance': item.importance,
            'created_at': item.created_at.isoformat(),
            'last_accessed': item.last_accessed.isoformat(),
            'metadata': item.metadata,
            'tags': item.tags
        }

    def _dict_to_memory(self, data: Dict[str, Any]) -> MemoryItem:
        """Convert dictionary to MemoryItem."""
        return MemoryItem(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data.get('memory_type', 'graph')),
            importance=data.get('importance', 0.5),
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data.get('last_accessed', data['created_at'])),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )

    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item as a text file."""
        if not self.is_initialized:
            raise RuntimeError("Memory service not initialized")

        try:
            # Generate ID if not provided
            if not item.id:
                item.id = str(uuid.uuid4())

            # Save memory to file
            memory_file = self.memories_path / f"{item.id}.txt"
            memory_data = self._memory_to_dict(item)

            with open(memory_file, 'w', encoding='utf-8') as f:
                # Write JSON header
                f.write("=== MEMORY METADATA ===\n")
                f.write(json.dumps({
                    'id': memory_data['id'],
                    'created_at': memory_data['created_at'],
                    'last_accessed': memory_data['last_accessed'],
                    'importance': memory_data['importance'],
                    'memory_type': memory_data['memory_type'],
                    'tags': memory_data['tags'],
                    'metadata': memory_data['metadata']
                }, indent=2))
                f.write("\n=== CONTENT ===\n")
                f.write(item.content)

            # Update index
            self.index[item.id] = {
                'file': str(memory_file.relative_to(self.memory_dir)),
                'created_at': memory_data['created_at'],
                'importance': memory_data['importance'],
                'tags': memory_data['tags'],
                'content_preview': item.content[:200]  # Store preview for quick search
            }

            await self._save_index()
            return item.id

        except Exception as e:
            print(f"❌ Failed to store memory: {e}")
            raise

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID."""
        if not self.is_initialized:
            return None

        try:
            # Check if memory exists in index
            if memory_id not in self.index:
                return None

            memory_file = self.memories_path / f"{memory_id}.txt"
            if not memory_file.exists():
                # Clean up orphaned index entry
                del self.index[memory_id]
                await self._save_index()
                return None

            # Read memory file
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse file
            parts = content.split("=== CONTENT ===\n", 1)
            if len(parts) != 2:
                return None

            # Extract metadata
            metadata_section = parts[0].replace("=== MEMORY METADATA ===\n", "")
            metadata = json.loads(metadata_section.strip())

            # Create MemoryItem
            memory_data = {
                **metadata,
                'content': parts[1].strip()
            }

            # Update last accessed
            memory_item = self._dict_to_memory(memory_data)
            memory_item.last_accessed = datetime.now()

            # Save updated access time
            await self.store_memory(memory_item)

            return memory_item

        except Exception as e:
            print(f"❌ Failed to retrieve memory: {e}")
            return None

    async def search_memories(self, query: str, limit: int = 10,
                            filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories using simple text matching."""
        if not self.is_initialized:
            return []

        try:
            query_lower = query.lower()
            results = []

            # Search through all memories
            for memory_id, index_entry in self.index.items():
                score = 0.0

                # Check content preview
                if query_lower in index_entry['content_preview'].lower():
                    score += 1.0

                # Check tags
                for tag in index_entry.get('tags', []):
                    if query_lower in tag.lower():
                        score += 0.5

                # Apply filters
                if filters:
                    if 'min_importance' in filters:
                        if index_entry['importance'] < filters['min_importance']:
                            continue

                if score > 0:
                    memory = await self.retrieve_memory(memory_id)
                    if memory:
                        results.append(MemorySearchResult(
                            item=memory,
                            relevance_score=score,
                            similarity_score=score
                        ))

            # Sort by relevance and limit
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"❌ Failed to search memories: {e}")
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory."""
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
            print(f"❌ Failed to update memory: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        if not self.is_initialized:
            return False

        try:
            # Remove from index
            if memory_id in self.index:
                del self.index[memory_id]
                await self._save_index()

            # Delete file
            memory_file = self.memories_path / f"{memory_id}.txt"
            if memory_file.exists():
                memory_file.unlink()

            return True

        except Exception as e:
            print(f"❌ Failed to delete memory: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if not self.is_initialized:
            return {}

        try:
            total_size = sum(
                (self.memories_path / f"{mid}.txt").stat().st_size
                for mid in self.index.keys()
                if (self.memories_path / f"{mid}.txt").exists()
            )

            return {
                'total_memories': len(self.index),
                'database_size_mb': total_size / (1024 * 1024),
                'service_type': 'plaintext_file',
                'memory_directory': str(self.memory_dir)
            }

        except Exception as e:
            print(f"❌ Failed to get memory stats: {e}")
            return {}

    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories."""
        if not self.is_initialized:
            return 0

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0

            # Find memories to delete
            to_delete = []
            for memory_id, index_entry in self.index.items():
                created_at = datetime.fromisoformat(index_entry['created_at'])
                importance = index_entry.get('importance', 0.5)

                # Delete if old and low importance
                if created_at < cutoff_date and importance < 0.3:
                    to_delete.append(memory_id)

            # Delete memories
            for memory_id in to_delete:
                if await self.delete_memory(memory_id):
                    deleted_count += 1

            return deleted_count

        except Exception as e:
            print(f"❌ Failed to cleanup memories: {e}")
            return 0

    async def close(self) -> None:
        """Close the memory service and save index."""
        try:
            await self._save_index()
            self.is_initialized = False
        except Exception as e:
            print(f"❌ Failed to close plain text memory service: {e}")
