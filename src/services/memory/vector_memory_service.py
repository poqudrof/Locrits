"""
Vector-based memory service for fuzzy, semantic memories.

Handles experiences, impressions, themes, and contextual similarities using
vector embeddings and similarity search. This service is optimized for:
- Experiential memories and impressions
- Emotional associations and feelings
- Thematic content analysis
- Contextual and semantic similarities
- "Souvenir" type memories
"""

import kuzu
import os
import json
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

def safe_json_dumps(obj: Any) -> str:
    """Safely serialize objects to JSON, handling datetime objects."""
    def json_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=json_serializer)

from .interfaces import VectorMemoryService as BaseVectorService, MemoryItem, MemorySearchResult, MemoryType
from .config import MemoryConfig, VectorMemoryConfig

try:
    from nomic import embed
    NOMIC_AVAILABLE = True
except ImportError:
    NOMIC_AVAILABLE = False
    print("Warning: nomic package not available. Vector embeddings will be disabled.")


class KuzuVectorMemoryService(BaseVectorService):
    """Kuzu-based vector memory service for semantic, fuzzy memories."""

    def __init__(self, locrit_name: str, config: MemoryConfig):
        super().__init__(locrit_name, config.vector.__dict__)
        self.full_config = config
        self.vector_config = config.vector

        self.base_path = Path(config.base_path)
        self.db_dir = self.base_path / "vector" / self._sanitize_name(locrit_name)
        self.db_path = self.db_dir / "kuzu.db"

        self.db = None
        self.conn = None
        # Enable embeddings if vector service is enabled and we have either nomic or ollama
        self.embeddings_enabled = self.vector_config.enabled and (
            NOMIC_AVAILABLE or
            getattr(self.vector_config, 'inference_mode', None) == "ollama"
        )

        # Vector index names
        self.souvenir_vector_index = f"{self._sanitize_name(locrit_name)}_souvenir_embeddings"
        self.impression_vector_index = f"{self._sanitize_name(locrit_name)}_impression_embeddings"
        self.theme_vector_index = f"{self._sanitize_name(locrit_name)}_theme_embeddings"

        # Create directory if it doesn't exist
        self.db_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize Locrit name for use as directory name."""
        import re
        return re.sub(r'[^\w\-_]', '_', name.lower())

    async def initialize(self) -> bool:
        """Initialize the Kuzu database and create vector schema."""
        if not self.vector_config.enabled or not self.embeddings_enabled:
            return False

        try:
            # Create database and connection
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)

            # Install and load VECTOR extension
            try:
                await asyncio.to_thread(self.conn.execute, "INSTALL VECTOR;")
                await asyncio.to_thread(self.conn.execute, "LOAD EXTENSION VECTOR;")
                print(f"Vector extension loaded for {self.locrit_name}")
            except Exception as e:
                print(f"Warning: Vector extension installation failed for {self.locrit_name}: {e}")

            # Create schema
            await self._create_vector_schema()

            # Create vector indices
            await self._create_vector_indices()

            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Error initializing vector memory for {self.locrit_name}: {e}")
            return False

    async def _create_vector_schema(self) -> None:
        """Create the vector schema for fuzzy memory storage."""
        try:
            # Souvenir memories - experiential, impressionistic
            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Souvenir(
                    id STRING,
                    content STRING,
                    experience_type STRING,
                    emotional_tone STRING,
                    vividness DOUBLE,
                    importance DOUBLE,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    tags STRING,
                    context STRING,
                    content_embedding FLOAT[{self.vector_config.dimension}],
                    PRIMARY KEY(id)
                )
            """)

            # Impression memories - feelings and reactions
            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Impression(
                    id STRING,
                    content STRING,
                    subject STRING,
                    sentiment DOUBLE,
                    confidence DOUBLE,
                    importance DOUBLE,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    metadata STRING,
                    content_embedding FLOAT[{self.vector_config.dimension}],
                    PRIMARY KEY(id)
                )
            """)

            # Theme memories - abstract concepts and patterns
            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Theme(
                    id STRING,
                    name STRING,
                    description STRING,
                    theme_type STRING,
                    strength DOUBLE,
                    occurrence_count INT64,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP,
                    examples STRING,
                    theme_embedding FLOAT[{self.vector_config.dimension}],
                    PRIMARY KEY(id)
                )
            """)

            # Association relationships for fuzzy connections
            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS REMINDS_OF(
                    FROM Souvenir TO Souvenir,
                    similarity DOUBLE,
                    association_type STRING
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS EVOKES(
                    FROM Souvenir TO Impression,
                    emotional_strength DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS EMBODIES(
                    FROM Souvenir TO Theme,
                    relevance DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS RELATES_TO_THEME(
                    FROM Impression TO Theme,
                    strength DOUBLE
                )
            """)

        except Exception as e:
            print(f"Error creating vector schema for {self.locrit_name}: {e}")
            raise

    async def _create_vector_indices(self) -> None:
        """Create vector indices for similarity search."""
        try:
            # Create vector index for souvenir content embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Souvenir',
                    '{self.souvenir_vector_index}',
                    'content_embedding'
                )
            """)

            # Create vector index for impression content embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Impression',
                    '{self.impression_vector_index}',
                    'content_embedding'
                )
            """)

            # Create vector index for theme embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Theme',
                    '{self.theme_vector_index}',
                    'theme_embedding'
                )
            """)

        except Exception as e:
            print(f"Note: Vector indices may already exist or vector extension not available: {e}")

    async def _generate_embedding(self, text: str, task_type: str = "search_document") -> Optional[List[float]]:
        """Generate embedding for text using nomic-embed-text."""
        if not self.embeddings_enabled:
            return None

        try:
            # Use Ollama for embeddings
            if getattr(self.vector_config, 'inference_mode', None) == "ollama":
                import ollama

                # Get base URL from config or use default
                ollama_base_url = getattr(self.vector_config, 'ollama_base_url', 'http://localhost:11434')
                client = ollama.Client(host=ollama_base_url)

                # Generate embedding using Ollama
                result = await asyncio.to_thread(
                    client.embeddings,
                    model=self.vector_config.model,
                    prompt=text
                )

                if result and 'embedding' in result:
                    return result['embedding']
                else:
                    print(f"Failed to generate embedding for text: {text[:50]}...")
                    return None
            else:
                # Fallback to nomic (original implementation)
                prefixed_text = f"{task_type}: {text}"
                result = await asyncio.to_thread(
                    embed.text,
                    texts=[prefixed_text],
                    model=self.vector_config.model,
                    task_type=task_type,
                    dimensionality=self.vector_config.dimension,
                    inference_mode=self.vector_config.inference_mode
                )
                if result and 'embeddings' in result and len(result['embeddings']) > 0:
                    return result['embeddings'][0]
                else:
                    print(f"Failed to generate embedding for text: {text[:50]}...")
                    return None

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item in vector storage."""
        if not self.is_initialized:
            raise Exception(f"Vector memory service not initialized for {self.locrit_name}")

        try:
            # Determine vector storage type based on content characteristics
            vector_type = item.metadata.get('vector_type', self._classify_memory_type(item))

            if vector_type == 'souvenir':
                return await self._store_souvenir(item)
            elif vector_type == 'impression':
                return await self._store_impression(item)
            elif vector_type == 'theme':
                return await self._store_theme(item)
            else:
                # Default to souvenir for general experiences
                return await self._store_souvenir(item)

        except Exception as e:
            print(f"Error storing vector memory: {e}")
            raise

    def _classify_memory_type(self, item: MemoryItem) -> str:
        """Classify what type of vector memory this should be."""
        content = item.content.lower()

        # Check for emotional/experiential indicators
        experience_keywords = ['felt', 'experienced', 'remember', 'impression', 'seemed', 'atmosphere', 'vibe']
        impression_keywords = ['think', 'believe', 'opinion', 'feel about', 'reaction', 'response']
        theme_keywords = ['pattern', 'theme', 'concept', 'principle', 'idea', 'notion']

        experience_score = sum(1 for word in experience_keywords if word in content)
        impression_score = sum(1 for word in impression_keywords if word in content)
        theme_score = sum(1 for word in theme_keywords if word in content)

        if theme_score >= max(experience_score, impression_score):
            return 'theme'
        elif impression_score > experience_score:
            return 'impression'
        else:
            return 'souvenir'

    async def _store_souvenir(self, item: MemoryItem) -> str:
        """Store a souvenir (experiential) memory."""
        souvenir_id = item.id or f"souvenir_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Generate embedding
        content_embedding = await self._generate_embedding(item.content, "search_document")

        # Extract metadata
        metadata = item.metadata
        experience_type = metadata.get('experience_type', 'general')
        emotional_tone = metadata.get('emotional_tone', 'neutral')
        vividness = metadata.get('vividness', item.importance)
        context = metadata.get('context', '')

        # Store with or without embedding
        if content_embedding:
            await asyncio.to_thread(self.conn.execute, """
                CREATE (s:Souvenir {
                    id: $souvenir_id,
                    content: $content,
                    experience_type: $experience_type,
                    emotional_tone: $emotional_tone,
                    vividness: $vividness,
                    importance: $importance,
                    created_at: $created_at,
                    last_accessed: $last_accessed,
                    tags: $tags,
                    context: $context,
                    content_embedding: $content_embedding
                })
            """, {
                "souvenir_id": souvenir_id,
                "content": item.content,
                "experience_type": experience_type,
                "emotional_tone": emotional_tone,
                "vividness": vividness,
                "importance": item.importance,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "tags": safe_json_dumps(item.tags),
                "context": context,
                "content_embedding": content_embedding
            })
        else:
            # Fallback without embedding
            await asyncio.to_thread(self.conn.execute, """
                CREATE (s:Souvenir {
                    id: $souvenir_id,
                    content: $content,
                    experience_type: $experience_type,
                    emotional_tone: $emotional_tone,
                    vividness: $vividness,
                    importance: $importance,
                    created_at: $created_at,
                    last_accessed: $last_accessed,
                    tags: $tags,
                    context: $context
                })
            """, {
                "souvenir_id": souvenir_id,
                "content": item.content,
                "experience_type": experience_type,
                "emotional_tone": emotional_tone,
                "vividness": vividness,
                "importance": item.importance,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "tags": safe_json_dumps(item.tags),
                "context": context
            })

        return souvenir_id

    async def _store_impression(self, item: MemoryItem) -> str:
        """Store an impression (opinion/feeling) memory."""
        impression_id = item.id or f"impression_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Generate embedding
        content_embedding = await self._generate_embedding(item.content, "classification")

        # Extract metadata
        metadata = item.metadata
        subject = metadata.get('subject', '')
        sentiment = metadata.get('sentiment', 0.0)  # -1 to 1
        confidence = metadata.get('confidence', item.importance)

        # Store with or without embedding
        if content_embedding:
            await asyncio.to_thread(self.conn.execute, """
                CREATE (i:Impression {
                    id: $impression_id,
                    content: $content,
                    subject: $subject,
                    sentiment: $sentiment,
                    confidence: $confidence,
                    importance: $importance,
                    created_at: $created_at,
                    last_accessed: $last_accessed,
                    metadata: $metadata,
                    content_embedding: $content_embedding
                })
            """, {
                "impression_id": impression_id,
                "content": item.content,
                "subject": subject,
                "sentiment": sentiment,
                "confidence": confidence,
                "importance": item.importance,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "metadata": safe_json_dumps(item.metadata),
                "content_embedding": content_embedding
            })
        else:
            # Fallback without embedding
            await asyncio.to_thread(self.conn.execute, """
                CREATE (i:Impression {
                    id: $impression_id,
                    content: $content,
                    subject: $subject,
                    sentiment: $sentiment,
                    confidence: $confidence,
                    importance: $importance,
                    created_at: $created_at,
                    last_accessed: $last_accessed,
                    metadata: $metadata
                })
            """, {
                "impression_id": impression_id,
                "content": item.content,
                "subject": subject,
                "sentiment": sentiment,
                "confidence": confidence,
                "importance": item.importance,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "metadata": json.dumps(item.metadata)
            })

        return impression_id

    async def _store_theme(self, item: MemoryItem) -> str:
        """Store a theme (abstract concept) memory."""
        theme_id = item.id or f"theme_{item.content.lower().replace(' ', '_')[:20]}"

        # Generate embedding
        theme_embedding = await self._generate_embedding(item.content, "clustering")

        # Extract metadata
        metadata = item.metadata
        name = metadata.get('name', item.content[:50])
        theme_type = metadata.get('theme_type', 'concept')
        examples = metadata.get('examples', [])

        # Store or update theme
        if theme_embedding:
            await asyncio.to_thread(self.conn.execute, """
                MERGE (t:Theme {id: $theme_id})
                ON CREATE SET t.name = $name, t.description = $content, t.theme_type = $theme_type,
                             t.strength = $importance, t.occurrence_count = 1,
                             t.first_seen = $created_at, t.last_updated = $created_at,
                             t.examples = $examples, t.theme_embedding = $theme_embedding
                ON MATCH SET t.description = $content, t.strength = t.strength + $importance,
                            t.occurrence_count = t.occurrence_count + 1,
                            t.last_updated = $created_at, t.examples = $examples
            """, {
                "theme_id": theme_id,
                "name": name,
                "content": item.content,
                "theme_type": theme_type,
                "importance": item.importance,
                "created_at": item.created_at,
                "examples": safe_json_dumps(examples),
                "theme_embedding": theme_embedding
            })
        else:
            # Fallback without embedding
            await asyncio.to_thread(self.conn.execute, """
                MERGE (t:Theme {id: $theme_id})
                ON CREATE SET t.name = $name, t.description = $content, t.theme_type = $theme_type,
                             t.strength = $importance, t.occurrence_count = 1,
                             t.first_seen = $created_at, t.last_updated = $created_at,
                             t.examples = $examples
                ON MATCH SET t.description = $content, t.strength = t.strength + $importance,
                            t.occurrence_count = t.occurrence_count + 1,
                            t.last_updated = $created_at, t.examples = $examples
            """, {
                "theme_id": theme_id,
                "name": name,
                "content": item.content,
                "theme_type": theme_type,
                "importance": item.importance,
                "created_at": item.created_at,
                "examples": json.dumps(examples)
            })

        return theme_id

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID."""
        if not self.is_initialized:
            return None

        try:
            # Try different node types
            for node_type in ['Souvenir', 'Impression', 'Theme']:
                result = await asyncio.to_thread(self._get_vector_node_by_id, node_type, memory_id)
                if result:
                    return self._convert_to_memory_item(result, node_type.lower())

            return None

        except Exception as e:
            print(f"Error retrieving vector memory {memory_id}: {e}")
            return None

    def _get_vector_node_by_id(self, node_type: str, node_id: str) -> Optional[Dict]:
        """Get a vector node by ID and type."""
        try:
            if node_type == 'Souvenir':
                result = self.conn.execute("""
                    MATCH (n:Souvenir {id: $id})
                    RETURN n.id, n.content, n.experience_type, n.emotional_tone, n.vividness,
                           n.importance, n.created_at, n.last_accessed, n.tags, n.context
                """, {"id": node_id})
            elif node_type == 'Impression':
                result = self.conn.execute("""
                    MATCH (n:Impression {id: $id})
                    RETURN n.id, n.content, n.subject, n.sentiment, n.confidence,
                           n.importance, n.created_at, n.last_accessed, n.metadata
                """, {"id": node_id})
            elif node_type == 'Theme':
                result = self.conn.execute("""
                    MATCH (n:Theme {id: $id})
                    RETURN n.id, n.name, n.description, n.theme_type, n.strength,
                           n.occurrence_count, n.first_seen, n.last_updated, n.examples
                """, {"id": node_id})
            else:
                return None

            if result.has_next():
                row = result.get_next()
                if row:
                    return {"type": node_type.lower(), "data": row}

            return None

        except Exception:
            return None

    def _convert_to_memory_item(self, result: Dict, memory_type: str) -> MemoryItem:
        """Convert database result to MemoryItem."""
        data = result["data"]

        if memory_type == 'souvenir':
            return MemoryItem(
                id=data[0],
                content=data[1],
                memory_type=MemoryType.VECTOR,
                importance=data[5],
                created_at=data[6],
                last_accessed=data[7],
                metadata={
                    "vector_type": "souvenir",
                    "experience_type": data[2],
                    "emotional_tone": data[3],
                    "vividness": data[4],
                    "context": data[9]
                },
                tags=json.loads(data[8]) if data[8] else []
            )
        elif memory_type == 'impression':
            return MemoryItem(
                id=data[0],
                content=data[1],
                memory_type=MemoryType.VECTOR,
                importance=data[5],
                created_at=data[6],
                last_accessed=data[7],
                metadata={
                    "vector_type": "impression",
                    "subject": data[2],
                    "sentiment": data[3],
                    "confidence": data[4],
                    **(json.loads(data[8]) if data[8] else {})
                },
                tags=["impression"]
            )
        elif memory_type == 'theme':
            return MemoryItem(
                id=data[0],
                content=data[2],  # description
                memory_type=MemoryType.VECTOR,
                importance=data[4],  # strength
                created_at=data[6],  # first_seen
                last_accessed=data[7],  # last_updated
                metadata={
                    "vector_type": "theme",
                    "name": data[1],
                    "theme_type": data[3],
                    "occurrence_count": data[5],
                    "examples": json.loads(data[8]) if data[8] else []
                },
                tags=["theme"]
            )

    async def search_memories(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories using vector similarity."""
        if not self.is_initialized or not self.embeddings_enabled:
            return []

        try:
            # Search across all vector types
            results = []

            # Search souvenirs
            souvenir_results = await self._vector_search_souvenirs(query, limit // 3)
            results.extend(souvenir_results)

            # Search impressions
            impression_results = await self._vector_search_impressions(query, limit // 3)
            results.extend(impression_results)

            # Search themes
            theme_results = await self._vector_search_themes(query, limit // 3)
            results.extend(theme_results)

            # Apply filters if provided
            if filters:
                results = self._apply_vector_filters(results, filters)

            # Sort by relevance and limit
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"Error searching vector memories: {e}")
            return []

    async def find_similar_memories(self, query: str, threshold: float = 0.7, limit: int = 10) -> List[MemorySearchResult]:
        """Find memories similar to the query using vector similarity."""
        return await self.search_memories(query, limit, {"similarity_threshold": threshold})

    async def _vector_search_souvenirs(self, query: str, limit: int) -> List[MemorySearchResult]:
        """Search souvenirs using vector similarity."""
        if not self.embeddings_enabled:
            return []

        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            def execute_search():
                result = self.conn.execute(f"""
                    CALL QUERY_VECTOR_INDEX(
                        '{self.souvenir_vector_index}',
                        $query_embedding,
                        $limit
                    ) YIELD node, score
                    RETURN node.id, node.content, node.experience_type, node.emotional_tone,
                           node.vividness, node.importance, node.created_at, node.last_accessed,
                           node.tags, node.context, score
                    ORDER BY score DESC
                """, {"query_embedding": query_embedding, "limit": limit})

                results = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memory_item = MemoryItem(
                            id=row[0],
                            content=row[1],
                            memory_type=MemoryType.VECTOR,
                            importance=row[5],
                            created_at=row[6],
                            last_accessed=row[7],
                            metadata={
                                "vector_type": "souvenir",
                                "experience_type": row[2],
                                "emotional_tone": row[3],
                                "vividness": row[4],
                                "context": row[9]
                            },
                            tags=json.loads(row[8]) if row[8] else []
                        )

                        results.append(MemorySearchResult(
                            item=memory_item,
                            relevance_score=float(row[10]),  # similarity score
                            similarity_score=float(row[10]),
                            reasoning=f"Souvenir similarity match for '{query}'"
                        ))
                return results

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in souvenir vector search: {e}")
            return []

    async def _vector_search_impressions(self, query: str, limit: int) -> List[MemorySearchResult]:
        """Search impressions using vector similarity."""
        if not self.embeddings_enabled:
            return []

        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            def execute_search():
                result = self.conn.execute(f"""
                    CALL QUERY_VECTOR_INDEX(
                        '{self.impression_vector_index}',
                        $query_embedding,
                        $limit
                    ) YIELD node, score
                    RETURN node.id, node.content, node.subject, node.sentiment, node.confidence,
                           node.importance, node.created_at, node.last_accessed, node.metadata, score
                    ORDER BY score DESC
                """, {"query_embedding": query_embedding, "limit": limit})

                results = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memory_item = MemoryItem(
                            id=row[0],
                            content=row[1],
                            memory_type=MemoryType.VECTOR,
                            importance=row[5],
                            created_at=row[6],
                            last_accessed=row[7],
                            metadata={
                                "vector_type": "impression",
                                "subject": row[2],
                                "sentiment": row[3],
                                "confidence": row[4],
                                **(json.loads(row[8]) if row[8] else {})
                            },
                            tags=["impression"]
                        )

                        results.append(MemorySearchResult(
                            item=memory_item,
                            relevance_score=float(row[9]),
                            similarity_score=float(row[9]),
                            reasoning=f"Impression similarity match for '{query}'"
                        ))
                return results

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in impression vector search: {e}")
            return []

    async def _vector_search_themes(self, query: str, limit: int) -> List[MemorySearchResult]:
        """Search themes using vector similarity."""
        if not self.embeddings_enabled:
            return []

        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            def execute_search():
                result = self.conn.execute(f"""
                    CALL QUERY_VECTOR_INDEX(
                        '{self.theme_vector_index}',
                        $query_embedding,
                        $limit
                    ) YIELD node, score
                    RETURN node.id, node.name, node.description, node.theme_type, node.strength,
                           node.occurrence_count, node.first_seen, node.last_updated, node.examples, score
                    ORDER BY score DESC
                """, {"query_embedding": query_embedding, "limit": limit})

                results = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memory_item = MemoryItem(
                            id=row[0],
                            content=row[2],  # description
                            memory_type=MemoryType.VECTOR,
                            importance=row[4],  # strength
                            created_at=row[6],  # first_seen
                            last_accessed=row[7],  # last_updated
                            metadata={
                                "vector_type": "theme",
                                "name": row[1],
                                "theme_type": row[3],
                                "occurrence_count": row[5],
                                "examples": json.loads(row[8]) if row[8] else []
                            },
                            tags=["theme"]
                        )

                        results.append(MemorySearchResult(
                            item=memory_item,
                            relevance_score=float(row[9]),
                            similarity_score=float(row[9]),
                            reasoning=f"Theme similarity match for '{query}'"
                        ))
                return results

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in theme vector search: {e}")
            return []

    def _apply_vector_filters(self, results: List[MemorySearchResult], filters: Dict[str, Any]) -> List[MemorySearchResult]:
        """Apply filters to vector search results."""
        filtered = results

        if 'similarity_threshold' in filters:
            threshold = filters['similarity_threshold']
            filtered = [r for r in filtered if r.similarity_score and r.similarity_score >= threshold]

        if 'vector_type' in filters:
            vector_type = filters['vector_type']
            filtered = [r for r in filtered if r.item.metadata.get('vector_type') == vector_type]

        if 'emotional_tone' in filters:
            tone = filters['emotional_tone']
            filtered = [r for r in filtered if r.item.metadata.get('emotional_tone') == tone]

        if 'min_importance' in filters:
            min_imp = filters['min_importance']
            filtered = [r for r in filtered if r.item.importance >= min_imp]

        return filtered

    async def get_memory_clusters(self, num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Group memories into semantic clusters."""
        if not self.is_initialized:
            return []

        try:
            # This is a simplified clustering - in practice you'd use proper clustering algorithms
            # Get recent souvenirs for clustering
            def get_souvenirs():
                result = self.conn.execute("""
                    MATCH (s:Souvenir)
                    RETURN s.id, s.content, s.experience_type, s.emotional_tone, s.importance
                    ORDER BY s.created_at DESC
                    LIMIT 50
                """)

                souvenirs = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        souvenirs.append({
                            "id": row[0],
                            "content": row[1],
                            "experience_type": row[2],
                            "emotional_tone": row[3],
                            "importance": row[4]
                        })
                return souvenirs

            souvenirs = await asyncio.to_thread(get_souvenirs)

            # Group by experience type and emotional tone
            clusters = {}
            for souvenir in souvenirs:
                cluster_key = f"{souvenir['experience_type']}_{souvenir['emotional_tone']}"
                if cluster_key not in clusters:
                    clusters[cluster_key] = {
                        "id": cluster_key,
                        "experience_type": souvenir['experience_type'],
                        "emotional_tone": souvenir['emotional_tone'],
                        "memories": [],
                        "average_importance": 0.0,
                        "count": 0
                    }

                clusters[cluster_key]["memories"].append(souvenir)
                clusters[cluster_key]["count"] += 1

            # Calculate average importance
            for cluster in clusters.values():
                if cluster["count"] > 0:
                    cluster["average_importance"] = sum(m["importance"] for m in cluster["memories"]) / cluster["count"]

            # Return top clusters by count
            return sorted(clusters.values(), key=lambda x: x["count"], reverse=True)[:num_clusters]

        except Exception as e:
            print(f"Error getting memory clusters: {e}")
            return []

    async def get_memory_themes(self, timeframe_days: int = 30) -> List[Dict[str, Any]]:
        """Extract common themes from recent memories."""
        if not self.is_initialized:
            return []

        try:
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)

            def get_recent_themes():
                result = self.conn.execute("""
                    MATCH (t:Theme)
                    WHERE t.last_updated >= $cutoff_date
                    RETURN t.id, t.name, t.description, t.theme_type, t.strength,
                           t.occurrence_count, t.last_updated
                    ORDER BY t.strength DESC, t.occurrence_count DESC
                    LIMIT 20
                """, {"cutoff_date": cutoff_date})

                themes = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        themes.append({
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "theme_type": row[3],
                            "strength": row[4],
                            "occurrence_count": row[5],
                            "last_updated": str(row[6])
                        })
                return themes

            return await asyncio.to_thread(get_recent_themes)

        except Exception as e:
            print(f"Error getting memory themes: {e}")
            return []

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory."""
        if not self.is_initialized:
            return False

        try:
            # Update common fields
            if 'content' in updates:
                await asyncio.to_thread(self.conn.execute, """
                    MATCH (n {id: $memory_id})
                    SET n.content = $content
                """, {"memory_id": memory_id, "content": updates['content']})

            if 'importance' in updates:
                await asyncio.to_thread(self.conn.execute, """
                    MATCH (n {id: $memory_id})
                    SET n.importance = $importance
                """, {"memory_id": memory_id, "importance": updates['importance']})

            # Update last_accessed
            await asyncio.to_thread(self.conn.execute, """
                MATCH (n {id: $memory_id})
                SET n.last_accessed = $timestamp
            """, {"memory_id": memory_id, "timestamp": datetime.now()})

            return True

        except Exception as e:
            print(f"Error updating vector memory {memory_id}: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory and its relationships."""
        if not self.is_initialized:
            return False

        try:
            await asyncio.to_thread(self.conn.execute, """
                MATCH (n {id: $memory_id})
                DETACH DELETE n
            """, {"memory_id": memory_id})
            return True

        except Exception as e:
            print(f"Error deleting vector memory {memory_id}: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if not self.is_initialized:
            return {"error": "Not initialized"}

        try:
            def get_stats():
                stats = {}

                # Count nodes by type
                for node_type in ['Souvenir', 'Impression', 'Theme']:
                    result = self.conn.execute(f"MATCH (n:{node_type}) RETURN COUNT(n)")
                    if result.has_next():
                        row = result.get_next()
                        stats[f"{node_type.lower()}_count"] = row[0] if row else 0

                # Count relationships
                result = self.conn.execute("MATCH ()-[r]->() RETURN COUNT(r)")
                if result.has_next():
                    row = result.get_next()
                    stats["relationship_count"] = row[0] if row else 0

                # Average importance by type
                for node_type in ['Souvenir', 'Impression']:
                    result = self.conn.execute(f"MATCH (n:{node_type}) RETURN AVG(n.importance)")
                    if result.has_next():
                        row = result.get_next()
                        stats[f"avg_{node_type.lower()}_importance"] = row[0] if row else 0.0

                return stats

            return await asyncio.to_thread(get_stats)

        except Exception as e:
            print(f"Error getting vector memory stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories."""
        if not self.is_initialized:
            return 0

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # Delete low-importance souvenirs older than retention period
            result = await asyncio.to_thread(self.conn.execute, """
                MATCH (s:Souvenir)
                WHERE s.created_at < $cutoff_date AND s.importance < $threshold
                DETACH DELETE s
                RETURN COUNT(s)
            """, {"cutoff_date": cutoff_date, "threshold": self.vector_config.cleanup_threshold})

            deleted_count = 0
            if result.has_next():
                row = result.get_next()
                deleted_count += row[0] if row else 0

            # Delete low-confidence impressions
            result = await asyncio.to_thread(self.conn.execute, """
                MATCH (i:Impression)
                WHERE i.created_at < $cutoff_date AND i.confidence < $threshold
                DETACH DELETE i
                RETURN COUNT(i)
            """, {"cutoff_date": cutoff_date, "threshold": self.vector_config.cleanup_threshold})

            if result.has_next():
                row = result.get_next()
                deleted_count += row[0] if row else 0

            return deleted_count

        except Exception as e:
            print(f"Error cleaning up vector memories: {e}")
            return 0

    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
            if self.db:
                del self.db
            self.is_initialized = False
        except Exception as e:
            print(f"Error closing vector connection for {self.locrit_name}: {e}")