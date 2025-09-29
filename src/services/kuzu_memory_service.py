"""
Kuzu-based memory service for per-Locrit memory isolation.
Each Locrit gets its own Kuzu database instance for complete memory separation.
"""

import kuzu
import os
import json
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from langchain_kuzu.graphs.kuzu_graph import KuzuGraph

try:
    from nomic import embed
    NOMIC_AVAILABLE = True
except ImportError:
    NOMIC_AVAILABLE = False
    print("Warning: nomic package not available. Vector embeddings will be disabled.")


class KuzuMemoryService:
    """Kuzu-based memory service with per-Locrit database isolation."""

    def __init__(self, locrit_name: str, base_path: str = "data/memory",
                 embedding_model: str = "nomic-embed-text",
                 embedding_dimension: int = 768,
                 inference_mode: str = "ollama"):
        """
        Initialize Kuzu memory service for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit (used for database path)
            base_path: Base directory for memory databases
            embedding_model: Model to use for generating embeddings
            embedding_dimension: Dimension of the embeddings (64-768 for nomic-v1.5)
            inference_mode: 'remote', 'local', or 'dynamic' for nomic inference
        """
        self.locrit_name = locrit_name
        self.base_path = Path(base_path)
        self.db_dir = self.base_path / self._sanitize_name(locrit_name)
        self.db_path = self.db_dir / "kuzu.db"

        self.db = None
        self.conn = None
        self.graph = None
        self.is_initialized = False

        # Vector embedding configuration
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.inference_mode = inference_mode
        # Enable embeddings if we have either nomic or using ollama mode
        self.embeddings_enabled = NOMIC_AVAILABLE or inference_mode == "ollama"

        # Vector index names
        self.message_vector_index = f"{self._sanitize_name(locrit_name)}_message_embeddings"
        self.memory_vector_index = f"{self._sanitize_name(locrit_name)}_memory_embeddings"
        self.concept_vector_index = f"{self._sanitize_name(locrit_name)}_concept_embeddings"

        # Create directory if it doesn't exist
        self.db_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize Locrit name for use as directory name."""
        # Replace spaces and special characters with underscores
        import re
        return re.sub(r'[^\w\-_]', '_', name.lower())

    async def initialize(self) -> bool:
        """
        Initialize the Kuzu database and create schema.

        Returns:
            True if initialization succeeds
        """
        try:
            # Create database and connection
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)
            self.graph = KuzuGraph(self.db, allow_dangerous_requests=True)

            # Install and load VECTOR extension if embeddings are enabled
            if self.embeddings_enabled:
                try:
                    await asyncio.to_thread(self.conn.execute, "INSTALL VECTOR;")
                    await asyncio.to_thread(self.conn.execute, "LOAD EXTENSION VECTOR;")
                    print(f"Vector extension loaded for {self.locrit_name}")
                except Exception as e:
                    print(f"Warning: Vector extension installation failed for {self.locrit_name}: {e}")

            # Create schema
            await self._create_schema()

            # Migrate existing schema if needed
            await self._migrate_schema()

            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Kuzu memory for {self.locrit_name}: {e}")
            return False

    async def _create_schema(self) -> None:
        """Create the graph schema for memory storage."""
        try:
            # Create node tables
            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS User(
                    id STRING,
                    name STRING,
                    email STRING,
                    created_at TIMESTAMP,
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Message(
                    id STRING,
                    role STRING,
                    content STRING,
                    timestamp TIMESTAMP,
                    session_id STRING,
                    metadata STRING,
                    content_embedding FLOAT[{self.embedding_dimension}],
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Session(
                    id STRING,
                    name STRING,
                    topic STRING,
                    created_at TIMESTAMP,
                    user_id STRING,
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Concept(
                    id STRING,
                    name STRING,
                    type STRING,
                    description STRING,
                    confidence DOUBLE,
                    name_embedding FLOAT[{self.embedding_dimension}],
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Topic(
                    id STRING,
                    name STRING,
                    description STRING,
                    category STRING,
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, f"""
                CREATE NODE TABLE IF NOT EXISTS Memory(
                    id STRING,
                    content STRING,
                    importance DOUBLE,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    content_embedding FLOAT[{self.embedding_dimension}],
                    PRIMARY KEY(id)
                )
            """)

            # Create relationship tables
            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS SENT(
                    FROM User TO Message,
                    weight DOUBLE DEFAULT 1.0
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS RESPONDS_TO(
                    FROM Message TO Message,
                    delay_seconds INT64
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS PART_OF(
                    FROM Message TO Session,
                    position INT64
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS MENTIONS(
                    FROM Message TO Concept,
                    confidence DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS DISCUSSES(
                    FROM Session TO Topic,
                    relevance DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS LEARNS(
                    FROM Session TO Memory,
                    strength DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                    FROM Concept TO Concept,
                    relationship_type STRING,
                    strength DOUBLE
                )
            """)

            # Create vector indices if embeddings are enabled
            if self.embeddings_enabled:
                await self._create_vector_indices()

        except Exception as e:
            print(f"Error creating schema for {self.locrit_name}: {e}")
            raise

    async def _create_vector_indices(self) -> None:
        """Create vector indices for similarity search."""
        try:
            # Create vector index for message content embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Message',
                    '{self.message_vector_index}',
                    'content_embedding'
                )
            """)

            # Create vector index for memory content embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Memory',
                    '{self.memory_vector_index}',
                    'content_embedding'
                )
            """)

            # Create vector index for concept name embeddings
            await asyncio.to_thread(self.conn.execute, f"""
                CALL CREATE_VECTOR_INDEX(
                    'Concept',
                    '{self.concept_vector_index}',
                    'name_embedding'
                )
            """)

        except Exception as e:
            print(f"Note: Vector indices may already exist or vector extension not available: {e}")

    async def _migrate_schema(self) -> None:
        """Migrate existing schema to add missing embedding columns."""
        try:
            # Check if Message table has content_embedding column
            result = await asyncio.to_thread(self.conn.execute, """
                CALL TABLE_INFO('Message') RETURN *
            """)

            columns = []
            while result.has_next():
                row = result.get_next()
                if row:
                    columns.append(row[0])  # Column name is first field

            # Add content_embedding column if it doesn't exist
            if 'content_embedding' not in columns:
                print(f"Migrating Message table schema for {self.locrit_name}...")
                await asyncio.to_thread(self.conn.execute, f"""
                    ALTER TABLE Message ADD content_embedding FLOAT[{self.embedding_dimension}]
                """)
                print(f"Added content_embedding column to Message table for {self.locrit_name}")

        except Exception as e:
            # If migration fails, it might be because the table doesn't exist yet or other reasons
            print(f"Schema migration note for {self.locrit_name}: {e}")

    async def _generate_embedding(self, text: str, task_type: str = "search_document") -> Optional[List[float]]:
        """
        Generate embedding for text using local Ollama.

        Args:
            text: Text to embed
            task_type: Task type for embedding ('search_document', 'search_query', 'classification', 'clustering')

        Returns:
            List of float values representing the embedding, or None if embedding generation fails
        """
        if not self.embeddings_enabled:
            return None

        try:
            # Use Ollama for embeddings
            if self.inference_mode == "ollama":
                import ollama

                # Create Ollama client
                client = ollama.Client(host="http://localhost:11434")

                # Generate embedding using Ollama
                result = await asyncio.to_thread(
                    client.embeddings,
                    model=self.embedding_model,
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
                    model=self.embedding_model,
                    task_type=task_type,
                    dimensionality=self.embedding_dimension,
                    inference_mode=self.inference_mode
                )

                if result and 'embeddings' in result and len(result['embeddings']) > 0:
                    return result['embeddings'][0]
                else:
                    print(f"Failed to generate embedding for text: {text[:50]}...")
                    return None

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    async def _generate_embeddings_batch(self, texts: List[str], task_type: str = "search_document") -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed
            task_type: Task type for embedding

        Returns:
            List of embeddings (or None for failed generations)
        """
        if not self.embeddings_enabled or not texts:
            return [None] * len(texts)

        try:
            # Use Ollama for embeddings
            if self.inference_mode == "ollama":
                import ollama
                client = ollama.Client(host="http://localhost:11434")

                # Generate embeddings one by one (Ollama doesn't support batch)
                embeddings = []
                for text in texts:
                    try:
                        result = await asyncio.to_thread(
                            client.embeddings,
                            model=self.embedding_model,
                            prompt=text
                        )
                        if result and 'embedding' in result:
                            embeddings.append(result['embedding'])
                        else:
                            embeddings.append(None)
                    except Exception as e:
                        print(f"Error generating embedding for text: {e}")
                        embeddings.append(None)

                return embeddings
            else:
                # Fallback to nomic (original implementation)
                prefixed_texts = [f"{task_type}: {text}" for text in texts]

                result = await asyncio.to_thread(
                    embed.text,
                    texts=prefixed_texts,
                    model=self.embedding_model,
                    task_type=task_type,
                    dimensionality=self.embedding_dimension,
                    inference_mode=self.inference_mode
                )

                if result and 'embeddings' in result:
                    return result['embeddings']
                else:
                    print(f"Failed to generate batch embeddings for {len(texts)} texts")
                    return [None] * len(texts)

        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)

    async def vector_search_messages(self, query: str, limit: int = 10, session_id: str = None) -> List[Dict]:
        """
        Search messages using vector similarity.

        Args:
            query: Search query text
            limit: Maximum number of results
            session_id: Optional session filter

        Returns:
            List of similar messages with similarity scores
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            # Build query with optional session filter
            if session_id:
                search_query = f"""
                    CALL QUERY_VECTOR_INDEX(
                        '{self.message_vector_index}',
                        $query_embedding,
                        $limit
                    ) YIELD node, score
                    MATCH (node:Message)-[:PART_OF]->(s:Session {{id: $session_id}})
                    RETURN node.id, node.role, node.content, node.timestamp, node.session_id, score
                    ORDER BY score DESC
                """
                params = {"query_embedding": query_embedding, "limit": limit, "session_id": session_id}
            else:
                search_query = f"""
                    CALL QUERY_VECTOR_INDEX(
                        '{self.message_vector_index}',
                        $query_embedding,
                        $limit
                    ) YIELD node, score
                    RETURN node.id, node.role, node.content, node.timestamp, node.session_id, score
                    ORDER BY score DESC
                """
                params = {"query_embedding": query_embedding, "limit": limit}

            def execute_search():
                result = self.conn.execute(search_query, params)
                messages = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        messages.append({
                            "id": row[0],
                            "role": row[1],
                            "content": row[2],
                            "timestamp": str(row[3]),
                            "session_id": row[4],
                            "similarity_score": float(row[5])
                        })
                return messages

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in vector search for messages: {e}")
            return []

    async def vector_search_memories(self, query: str, limit: int = 10, min_importance: float = 0.0) -> List[Dict]:
        """
        Search memories using vector similarity.

        Args:
            query: Search query text
            limit: Maximum number of results
            min_importance: Minimum importance threshold

        Returns:
            List of similar memories with similarity scores
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            search_query = f"""
                CALL QUERY_VECTOR_INDEX(
                    '{self.memory_vector_index}',
                    $query_embedding,
                    $limit
                ) YIELD node, score
                WHERE node.importance >= $min_importance
                RETURN node.id, node.content, node.importance, node.created_at, node.last_accessed, score
                ORDER BY score DESC
            """

            def execute_search():
                result = self.conn.execute(search_query, {
                    "query_embedding": query_embedding,
                    "limit": limit,
                    "min_importance": min_importance
                })
                memories = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memories.append({
                            "id": row[0],
                            "content": row[1],
                            "importance": row[2],
                            "created_at": str(row[3]),
                            "last_accessed": str(row[4]),
                            "similarity_score": float(row[5])
                        })
                return memories

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in vector search for memories: {e}")
            return []

    async def vector_search_concepts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search concepts using vector similarity.

        Args:
            query: Search query text
            limit: Maximum number of results

        Returns:
            List of similar concepts with similarity scores
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query, "search_query")
            if not query_embedding:
                return []

            search_query = f"""
                CALL QUERY_VECTOR_INDEX(
                    '{self.concept_vector_index}',
                    $query_embedding,
                    $limit
                ) YIELD node, score
                RETURN node.id, node.name, node.type, node.description, node.confidence, score
                ORDER BY score DESC
            """

            def execute_search():
                result = self.conn.execute(search_query, {
                    "query_embedding": query_embedding,
                    "limit": limit
                })
                concepts = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        concepts.append({
                            "id": row[0],
                            "name": row[1],
                            "type": row[2],
                            "description": row[3],
                            "confidence": row[4],
                            "similarity_score": float(row[5])
                        })
                return concepts

            return await asyncio.to_thread(execute_search)

        except Exception as e:
            print(f"Error in vector search for concepts: {e}")
            return []

    async def vector_search_all(self, query: str, limit_per_type: int = 5) -> Dict[str, List[Dict]]:
        """
        Search across all content types using vector similarity.

        Args:
            query: Search query text
            limit_per_type: Maximum results per content type

        Returns:
            Dictionary with results for messages, memories, and concepts
        """
        try:
            results = await asyncio.gather(
                self.vector_search_messages(query, limit_per_type),
                self.vector_search_memories(query, limit_per_type),
                self.vector_search_concepts(query, limit_per_type),
                return_exceptions=True
            )

            return {
                "messages": results[0] if not isinstance(results[0], Exception) else [],
                "memories": results[1] if not isinstance(results[1], Exception) else [],
                "concepts": results[2] if not isinstance(results[2], Exception) else []
            }

        except Exception as e:
            print(f"Error in comprehensive vector search: {e}")
            return {"messages": [], "memories": [], "concepts": []}

    async def get_contextual_memories(self, current_message: str, limit: int = 5,
                                      include_session_context: bool = True, session_id: str = None) -> List[Dict]:
        """
        Get contextually relevant memories for the current message using vector similarity.

        Args:
            current_message: The current message content
            limit: Number of relevant memories to retrieve
            include_session_context: Whether to include session-specific context
            session_id: Session ID for context filtering

        Returns:
            List of contextually relevant memories with similarity scores
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            # Search for similar messages first
            similar_messages = await self.vector_search_messages(current_message, limit * 2, session_id if include_session_context else None)

            # Search for similar standalone memories
            similar_memories = await self.vector_search_memories(current_message, limit)

            # Combine and rank results
            all_results = []

            # Add messages with context
            for msg in similar_messages:
                all_results.append({
                    **msg,
                    "type": "message",
                    "relevance": msg["similarity_score"] * (1.2 if include_session_context and msg.get("session_id") == session_id else 1.0)
                })

            # Add standalone memories
            for mem in similar_memories:
                all_results.append({
                    **mem,
                    "type": "memory",
                    "relevance": mem["similarity_score"] * mem.get("importance", 0.5)
                })

            # Sort by relevance and return top results
            all_results.sort(key=lambda x: x["relevance"], reverse=True)
            return all_results[:limit]

        except Exception as e:
            print(f"Error getting contextual memories: {e}")
            return []

    async def recommend_related_concepts(self, content: str, limit: int = 10) -> List[Dict]:
        """
        Recommend concepts related to the given content using vector similarity.

        Args:
            content: Content to find related concepts for
            limit: Maximum number of concepts to recommend

        Returns:
            List of related concepts with similarity scores and usage statistics
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            # Find similar concepts
            similar_concepts = await self.vector_search_concepts(content, limit)

            # Enhance with usage statistics
            enhanced_concepts = []
            for concept in similar_concepts:
                # Get mention count and recent usage
                concept_details = await self.get_concept_details(concept["name"])
                if concept_details:
                    enhanced_concepts.append({
                        **concept,
                        "mentions": concept_details.get("mentions", 0),
                        "first_mentioned": concept_details.get("first_mentioned"),
                        "last_mentioned": concept_details.get("last_mentioned"),
                        "context_examples": concept_details.get("context_examples", [])[:2]  # Limit context examples
                    })
                else:
                    enhanced_concepts.append(concept)

            return enhanced_concepts

        except Exception as e:
            print(f"Error recommending related concepts: {e}")
            return []

    async def get_memory_insights(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Get insights about memory patterns using vector analysis.

        Args:
            timeframe_days: Number of days to analyze

        Returns:
            Dictionary with memory insights and patterns
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return {"error": "Vector search not available"}

        try:
            # Get recent messages for analysis
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)

            def get_recent_messages():
                result = self.conn.execute("""
                    MATCH (m:Message)
                    WHERE m.timestamp >= $cutoff_date
                    RETURN m.content, m.role, m.timestamp
                    ORDER BY m.timestamp DESC
                    LIMIT 100
                """, {"cutoff_date": cutoff_date})

                messages = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        messages.append({
                            "content": row[0],
                            "role": row[1],
                            "timestamp": str(row[2])
                        })
                return messages

            recent_messages = await asyncio.to_thread(get_recent_messages)

            # Sample a few messages for concept analysis
            sample_messages = recent_messages[:10] if len(recent_messages) > 10 else recent_messages

            # Get frequently mentioned concepts
            insights = {
                "timeframe_days": timeframe_days,
                "total_messages_analyzed": len(recent_messages),
                "frequent_concepts": [],
                "content_themes": []
            }

            # Analyze themes in recent content
            if sample_messages:
                themes = []
                for msg in sample_messages:
                    if msg["content"]:
                        related_concepts = await self.recommend_related_concepts(msg["content"], 3)
                        themes.extend([c["name"] for c in related_concepts if c["similarity_score"] > 0.7])

                # Count theme frequency
                from collections import Counter
                theme_counts = Counter(themes)
                insights["content_themes"] = [{"theme": theme, "frequency": count}
                                              for theme, count in theme_counts.most_common(5)]

            return insights

        except Exception as e:
            print(f"Error getting memory insights: {e}")
            return {"error": str(e)}

    async def find_knowledge_gaps(self, query_topics: List[str], confidence_threshold: float = 0.5) -> List[Dict]:
        """
        Identify potential knowledge gaps by finding topics with low concept coverage.

        Args:
            query_topics: List of topic names to analyze
            confidence_threshold: Minimum confidence threshold for concepts

        Returns:
            List of topics with gap analysis
        """
        if not self.embeddings_enabled or not self.is_initialized:
            return []

        try:
            gap_analysis = []

            for topic in query_topics:
                # Search for related concepts
                related_concepts = await self.vector_search_concepts(topic, 10)

                # Filter by confidence
                high_confidence_concepts = [c for c in related_concepts
                                            if c.get("confidence", 0) >= confidence_threshold]

                # Get concept details for coverage analysis
                coverage_score = 0.0
                if related_concepts:
                    total_similarity = sum(c["similarity_score"] for c in related_concepts)
                    coverage_score = total_similarity / len(related_concepts)

                gap_analysis.append({
                    "topic": topic,
                    "related_concepts_found": len(related_concepts),
                    "high_confidence_concepts": len(high_confidence_concepts),
                    "coverage_score": coverage_score,
                    "gap_level": "high" if coverage_score < 0.3 else "medium" if coverage_score < 0.6 else "low",
                    "top_related_concepts": [c["name"] for c in related_concepts[:3]]
                })

            # Sort by gap level (high gaps first)
            gap_levels = {"high": 3, "medium": 2, "low": 1}
            gap_analysis.sort(key=lambda x: gap_levels.get(x["gap_level"], 0), reverse=True)

            return gap_analysis

        except Exception as e:
            print(f"Error finding knowledge gaps: {e}")
            return []

    async def save_message(self, role: str, content: str, session_id: str = None,
                          user_id: str = "default", metadata: Dict = None) -> str:
        """
        Save a message to the Locrit's memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            Message ID
        """
        if not self.is_initialized:
            raise Exception(f"Memory service not initialized for {self.locrit_name}")

        # Generate message ID
        timestamp = datetime.now()
        message_id = f"{role}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        # If no session_id provided, create one
        if not session_id:
            session_id = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        try:
            # Create or get user
            await self._ensure_user_exists(user_id)

            # Create or get session
            await self._ensure_session_exists(session_id, user_id)

            # Generate embedding for message content
            content_embedding = await self._generate_embedding(content, "search_document")

            # Insert message with embedding
            if content_embedding:
                await asyncio.to_thread(self.conn.execute, """
                    CREATE (m:Message {
                        id: $message_id,
                        role: $role,
                        content: $content,
                        timestamp: $timestamp,
                        session_id: $session_id,
                        metadata: $metadata,
                        content_embedding: $content_embedding
                    })
                """, {
                    "message_id": message_id,
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "metadata": json.dumps(metadata or {}),
                    "content_embedding": content_embedding
                })
            else:
                # Fallback to message without embedding if generation fails
                await asyncio.to_thread(self.conn.execute, """
                    CREATE (m:Message {
                        id: $message_id,
                        role: $role,
                        content: $content,
                        timestamp: $timestamp,
                        session_id: $session_id,
                        metadata: $metadata
                    })
                """, {
                    "message_id": message_id,
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "metadata": json.dumps(metadata or {})
                })

            # Create relationships
            await asyncio.to_thread(self.conn.execute, """
                MATCH (u:User {id: $user_id}), (m:Message {id: $message_id})
                CREATE (u)-[:SENT {weight: 1.0}]->(m)
            """, {"user_id": user_id, "message_id": message_id})

            await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message {id: $message_id}), (s:Session {id: $session_id})
                CREATE (m)-[:PART_OF {position: 0}]->(s)
            """, {"message_id": message_id, "session_id": session_id})

            # Extract and link concepts
            await self._extract_and_link_concepts(message_id, content)

            # Link to previous message in session if exists
            await self._link_to_previous_message(message_id, session_id)

            return message_id

        except Exception as e:
            print(f"Error saving message for {self.locrit_name}: {e}")
            raise

    async def _ensure_user_exists(self, user_id: str) -> None:
        """Ensure user node exists."""
        try:
            await asyncio.to_thread(self.conn.execute, """
                MERGE (u:User {id: $user_id})
                ON CREATE SET u.name = $user_id, u.created_at = $timestamp
            """, {"user_id": user_id, "timestamp": datetime.now()})
        except Exception as e:
            print(f"Error ensuring user exists: {e}")

    async def _ensure_session_exists(self, session_id: str, user_id: str) -> None:
        """Ensure session node exists."""
        try:
            await asyncio.to_thread(self.conn.execute, """
                MERGE (s:Session {id: $session_id})
                ON CREATE SET s.created_at = $timestamp, s.user_id = $user_id
            """, {"session_id": session_id, "user_id": user_id, "timestamp": datetime.now()})
        except Exception as e:
            print(f"Error ensuring session exists: {e}")

    async def _extract_and_link_concepts(self, message_id: str, content: str) -> None:
        """
        This function is deprecated.
        Concept extraction is now handled by the LLM through the new modular memory system.
        The LLM decides what to store and how to store it using memory tools.
        """
        # Concept extraction is now LLM-driven through the modular memory system
        # No automatic extraction based on capitalized letters
        pass

    async def _link_to_previous_message(self, message_id: str, session_id: str) -> None:
        """Link message to previous message in the same session."""
        try:
            # Find the most recent previous message in the session
            result = await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message)-[:PART_OF]->(s:Session {id: $session_id})
                WHERE m.id <> $message_id
                RETURN m.id as prev_id, m.timestamp as prev_time
                ORDER BY m.timestamp DESC
                LIMIT 1
            """, {"session_id": session_id, "message_id": message_id})

            if result.has_next():
                row = result.get_next()
                if row:
                    prev_id = row[0]

                    # Create RESPONDS_TO relationship
                    await asyncio.to_thread(self.conn.execute, """
                        MATCH (prev:Message {id: $prev_id}), (curr:Message {id: $message_id})
                        CREATE (curr)-[:RESPONDS_TO {delay_seconds: 0}]->(prev)
                    """, {"prev_id": prev_id, "message_id": message_id})

        except Exception as e:
            print(f"Error linking to previous message: {e}")

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages

        Returns:
            List of message dictionaries
        """
        if not self.is_initialized:
            return []

        try:
            def get_messages():
                result = self.conn.execute("""
                    MATCH (m:Message)-[:PART_OF]->(s:Session {id: $session_id})
                    RETURN m.id, m.role, m.content, m.timestamp, m.metadata
                    ORDER BY m.timestamp ASC
                    LIMIT $limit
                """, {"session_id": session_id, "limit": limit})

                messages = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        messages.append({
                            "id": row[0],
                            "role": row[1],
                            "content": row[2],
                            "timestamp": str(row[3]),
                            "metadata": json.loads(row[4]) if row[4] else {}
                        })
                return messages

            return await asyncio.to_thread(get_messages)

        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def search_memories(self, query: str, limit: int = 10, use_vector_search: bool = True) -> List[Dict]:
        """
        Search through memories using both content matching and vector similarity.

        Args:
            query: Search query
            limit: Maximum number of results
            use_vector_search: Whether to include vector similarity search

        Returns:
            List of matching messages with optional similarity scores
        """
        if not self.is_initialized:
            return []

        try:
            # If vector search is enabled and requested, use it first
            if use_vector_search and self.embeddings_enabled:
                vector_results = await self.vector_search_messages(query, limit)
                if vector_results:
                    return vector_results

            # Fallback to traditional text search
            def search_messages():
                result = self.conn.execute("""
                    MATCH (m:Message)
                    WHERE m.content CONTAINS $query
                    RETURN m.id, m.role, m.content, m.timestamp, m.session_id
                    ORDER BY m.timestamp DESC
                    LIMIT $limit
                """, {"query": query, "limit": limit})

                memories = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memories.append({
                            "id": row[0],
                            "role": row[1],
                            "content": row[2],
                            "timestamp": str(row[3]),
                            "session_id": row[4],
                            "similarity_score": None  # No similarity score for text search
                        })
                return memories

            return await asyncio.to_thread(search_messages)

        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    async def get_concept_details(self, concept_name: str, concept_type: str = None) -> Optional[Dict]:
        """
        Get detailed information about a specific concept.

        Args:
            concept_name: Name of the concept
            concept_type: Type of the concept (optional filter)

        Returns:
            Dictionary with concept details or None if not found
        """
        if not self.is_initialized:
            return None

        try:
            # Build query based on whether type filter is provided
            if concept_type:
                concept_query = """
                    MATCH (c:Concept {name: $concept_name, type: $concept_type})
                    RETURN c.id, c.name, c.type, c.description, c.confidence
                """
                params = {"concept_name": concept_name, "concept_type": concept_type}
            else:
                concept_query = """
                    MATCH (c:Concept {name: $concept_name})
                    RETURN c.id, c.name, c.type, c.description, c.confidence
                """
                params = {"concept_name": concept_name}

            def get_concept():
                result = self.conn.execute(concept_query, params)
                if result.has_next():
                    row = result.get_next()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "type": row[2],
                            "description": row[3],
                            "confidence": row[4]
                        }
                return None

            concept = await asyncio.to_thread(get_concept)
            if not concept:
                return None

            # Get mention count
            def get_mention_count():
                result = self.conn.execute("""
                    MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(m:Message)
                    RETURN COUNT(m) as mention_count
                """, {"concept_name": concept_name})

                if result.has_next():
                    row = result.get_next()
                    return row[0] if row else 0
                return 0

            mention_count = await asyncio.to_thread(get_mention_count)

            # Get first and last mention timestamps
            def get_timestamps():
                result = self.conn.execute("""
                    MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(m:Message)
                    RETURN m.timestamp as timestamp
                    ORDER BY m.timestamp ASC
                """, {"concept_name": concept_name})

                timestamps = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        timestamps.append(row[0])

                if timestamps:
                    return {
                        "first_mentioned": str(min(timestamps)),
                        "last_mentioned": str(max(timestamps))
                    }
                return {}

            timestamps = await asyncio.to_thread(get_timestamps)

            # Get context examples (recent messages mentioning this concept)
            def get_context_examples():
                result = self.conn.execute("""
                    MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(m:Message)
                    RETURN m.content, m.timestamp, m.role
                    ORDER BY m.timestamp DESC
                    LIMIT 5
                """, {"concept_name": concept_name})

                examples = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        examples.append({
                            "content": row[0][:200] + "..." if len(str(row[0])) > 200 else str(row[0]),
                            "timestamp": str(row[1]),
                            "role": row[2]
                        })
                return examples

            context_examples = await asyncio.to_thread(get_context_examples)

            # Get related concepts
            def get_related():
                result = self.conn.execute("""
                    MATCH (c:Concept {name: $concept_name})-[:RELATES_TO]-(related:Concept)
                    RETURN DISTINCT related.name as name, related.type as type,
                           related.description as description
                    LIMIT 10
                """, {"concept_name": concept_name})

                related = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        related.append({
                            "name": row["name"],
                            "type": row["type"],
                            "description": row["description"]
                        })
                return related

            related_concepts = await asyncio.to_thread(get_related)

            # Combine all information
            return {
                "id": concept["id"],
                "name": concept["name"],
                "type": concept["type"],
                "description": concept["description"],
                "confidence": concept["confidence"],
                "mentions": mention_count,
                **timestamps,
                "context_examples": context_examples,
                "related_concepts": related_concepts
            }

        except Exception as e:
            print(f"Error getting concept details for {concept_name}: {e}")
            return None

    async def get_related_concepts(self, concept_name: str, depth: int = 2) -> List[Dict]:
        """
        Get concepts related to a given concept.

        Args:
            concept_name: Name of the concept
            depth: Maximum traversal depth

        Returns:
            List of related concepts
        """
        if not self.is_initialized:
            return []

        try:
            result = await asyncio.to_thread(self.conn.execute, """
                MATCH (c:Concept {name: $concept_name})-[:RELATES_TO*1..$depth]-(related:Concept)
                RETURN DISTINCT related.name as name, related.type as type,
                       related.description as description
                LIMIT 20
            """, {"concept_name": concept_name, "depth": depth})

            concepts = []
            for row in result:
                concepts.append({
                    "name": row["name"],
                    "type": row["type"],
                    "description": row["description"]
                })

            return concepts

        except Exception as e:
            print(f"Error getting related concepts: {e}")
            return []

    async def get_full_memory_summary(self) -> Dict[str, Any]:
        """
        Get a complete summary of the Locrit's memory.

        Returns:
            Dictionary with memory statistics and content
        """
        if not self.is_initialized:
            return {"error": "Memory not initialized"}

        try:
            # Get counts - using simpler approach
            def get_count(query):
                result = self.conn.execute(query)
                if result.has_next():
                    row = result.get_next()
                    return row[0] if row else 0
                return 0

            message_count = await asyncio.to_thread(get_count, "MATCH (m:Message) RETURN COUNT(m)")
            session_count = await asyncio.to_thread(get_count, "MATCH (s:Session) RETURN COUNT(s)")
            concept_count = await asyncio.to_thread(get_count, "MATCH (c:Concept) RETURN COUNT(c)")
            user_count = await asyncio.to_thread(get_count, "MATCH (u:User) RETURN COUNT(u)")

            # Get recent messages
            def get_recent_messages():
                result = self.conn.execute("""
                    MATCH (m:Message)
                    RETURN m.role, m.content, m.timestamp, m.session_id
                    ORDER BY m.timestamp DESC
                    LIMIT 10
                """)
                messages = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        messages.append({
                            "role": row[0],
                            "content": row[1][:100] + "..." if len(str(row[1])) > 100 else str(row[1]),
                            "timestamp": str(row[2]),
                            "session_id": row[3]
                        })
                return messages

            # Get sessions
            def get_sessions():
                result = self.conn.execute("""
                    MATCH (s:Session)
                    RETURN s.id, s.created_at, s.user_id
                    ORDER BY s.created_at DESC
                """)
                sessions = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        sessions.append({
                            "id": row[0],
                            "name": row[0],  # Use ID as name for now
                            "created_at": str(row[1]),
                            "user_id": row[2]
                        })
                return sessions

            # Get concepts
            def get_concepts():
                result = self.conn.execute("""
                    MATCH (c:Concept)<-[:MENTIONS]-(m:Message)
                    RETURN c.name, c.type, COUNT(m)
                    ORDER BY COUNT(m) DESC
                    LIMIT 20
                """)
                concepts = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        concepts.append({
                            "name": row[0],
                            "type": row[1],
                            "mentions": row[2]
                        })
                return concepts

            recent_messages = await asyncio.to_thread(get_recent_messages)
            sessions = await asyncio.to_thread(get_sessions)
            concepts = await asyncio.to_thread(get_concepts)

            return {
                "locrit_name": self.locrit_name,
                "statistics": {
                    "total_messages": message_count,
                    "total_sessions": session_count,
                    "total_concepts": concept_count,
                    "total_users": user_count
                },
                "recent_messages": recent_messages,
                "sessions": sessions,
                "top_concepts": concepts
            }

        except Exception as e:
            print(f"Error getting memory summary: {e}")
            return {"error": str(e)}

    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message and its relationships.

        Args:
            message_id: ID of the message to delete

        Returns:
            True if deletion succeeds
        """
        if not self.is_initialized:
            return False

        try:
            # Delete the message and all its relationships
            await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message {id: $message_id})
                DETACH DELETE m
            """, {"message_id": message_id})

            return True

        except Exception as e:
            print(f"Error deleting message {message_id}: {e}")
            return False

    async def edit_message(self, message_id: str, new_content: str) -> bool:
        """
        Edit the content of an existing message.

        Args:
            message_id: ID of the message to edit
            new_content: New message content

        Returns:
            True if edit succeeds
        """
        if not self.is_initialized:
            return False

        try:
            # Update message content
            await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message {id: $message_id})
                SET m.content = $new_content
            """, {"message_id": message_id, "new_content": new_content})

            # Re-extract and link concepts for the updated message
            await self._extract_and_link_concepts(message_id, new_content)

            return True

        except Exception as e:
            print(f"Error editing message {message_id}: {e}")
            return False

    async def add_memory(self, content: str, importance: float = 0.5, metadata: Dict = None) -> str:
        """
        Add a standalone memory entry.

        Args:
            content: Memory content
            importance: Memory importance (0.0 to 1.0)
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            raise Exception(f"Memory service not initialized for {self.locrit_name}")

        timestamp = datetime.now()
        memory_id = f"memory_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            # Generate embedding for memory content
            content_embedding = await self._generate_embedding(content, "search_document")

            # Insert memory with embedding
            if content_embedding:
                await asyncio.to_thread(self.conn.execute, """
                    CREATE (m:Memory {
                        id: $memory_id,
                        content: $content,
                        importance: $importance,
                        created_at: $timestamp,
                        last_accessed: $timestamp,
                        content_embedding: $content_embedding
                    })
                """, {
                    "memory_id": memory_id,
                    "content": content,
                    "importance": importance,
                    "timestamp": timestamp,
                    "content_embedding": content_embedding
                })
            else:
                # Fallback to memory without embedding if generation fails
                await asyncio.to_thread(self.conn.execute, """
                    CREATE (m:Memory {
                        id: $memory_id,
                        content: $content,
                        importance: $importance,
                        created_at: $timestamp,
                        last_accessed: $timestamp
                    })
                """, {
                    "memory_id": memory_id,
                    "content": content,
                    "importance": importance,
                    "timestamp": timestamp
                })

            return memory_id

        except Exception as e:
            print(f"Error adding memory: {e}")
            raise

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory entry.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deletion succeeds
        """
        if not self.is_initialized:
            return False

        try:
            await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Memory {id: $memory_id})
                DETACH DELETE m
            """, {"memory_id": memory_id})

            return True

        except Exception as e:
            print(f"Error deleting memory {memory_id}: {e}")
            return False

    async def edit_concept(self, concept_id: str, name: str = None, description: str = None,
                          confidence: float = None) -> bool:
        """
        Edit a concept's properties.

        Args:
            concept_id: ID of the concept to edit
            name: New concept name (optional)
            description: New concept description (optional)
            confidence: New confidence score (optional)

        Returns:
            True if edit succeeds
        """
        if not self.is_initialized:
            return False

        try:
            # Build update clause dynamically
            updates = []
            params = {"concept_id": concept_id}

            if name is not None:
                updates.append("c.name = $name")
                params["name"] = name

            if description is not None:
                updates.append("c.description = $description")
                params["description"] = description

            if confidence is not None:
                updates.append("c.confidence = $confidence")
                params["confidence"] = confidence

            if not updates:
                return False

            query = f"""
                MATCH (c:Concept {{id: $concept_id}})
                SET {', '.join(updates)}
            """

            await asyncio.to_thread(self.conn.execute, query, params)

            return True

        except Exception as e:
            print(f"Error editing concept {concept_id}: {e}")
            return False

    async def delete_concept(self, concept_id: str) -> bool:
        """
        Delete a concept and its relationships.

        Args:
            concept_id: ID of the concept to delete

        Returns:
            True if deletion succeeds
        """
        if not self.is_initialized:
            return False

        try:
            await asyncio.to_thread(self.conn.execute, """
                MATCH (c:Concept {id: $concept_id})
                DETACH DELETE c
            """, {"concept_id": concept_id})

            return True

        except Exception as e:
            print(f"Error deleting concept {concept_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.

        Args:
            session_id: ID of the session to delete

        Returns:
            True if deletion succeeds
        """
        if not self.is_initialized:
            return False

        try:
            # Delete all messages in the session first
            await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message)-[:PART_OF]->(s:Session {id: $session_id})
                DETACH DELETE m
            """, {"session_id": session_id})

            # Delete the session
            await asyncio.to_thread(self.conn.execute, """
                MATCH (s:Session {id: $session_id})
                DETACH DELETE s
            """, {"session_id": session_id})

            return True

        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    async def clear_all_memory(self) -> bool:
        """
        Clear all memory data for this Locrit.

        Returns:
            True if clearing succeeds
        """
        if not self.is_initialized:
            return False

        try:
            # Delete all nodes and relationships
            await asyncio.to_thread(self.conn.execute, "MATCH (n) DETACH DELETE n")

            # Recreate schema
            await self._create_schema()

            return True

        except Exception as e:
            print(f"Error clearing all memory: {e}")
            return False

    async def get_message_by_id(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific message by ID.

        Args:
            message_id: ID of the message

        Returns:
            Message data or None if not found
        """
        if not self.is_initialized:
            return None

        try:
            def get_message():
                result = self.conn.execute("""
                    MATCH (m:Message {id: $message_id})
                    RETURN m.id, m.role, m.content, m.timestamp, m.session_id, m.metadata
                """, {"message_id": message_id})

                if result.has_next():
                    row = result.get_next()
                    if row:
                        return {
                            "id": row[0],
                            "role": row[1],
                            "content": row[2],
                            "timestamp": str(row[3]),
                            "session_id": row[4],
                            "metadata": json.loads(row[5]) if row[5] else {}
                        }
                return None

            return await asyncio.to_thread(get_message)

        except Exception as e:
            print(f"Error getting message {message_id}: {e}")
            return None

    async def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """
        Get a specific session by ID.

        Args:
            session_id: ID of the session

        Returns:
            Session data or None if not found
        """
        if not self.is_initialized:
            return None

        try:
            def get_session():
                result = self.conn.execute("""
                    MATCH (s:Session {id: $session_id})
                    RETURN s.id, s.name, s.topic, s.created_at, s.user_id
                """, {"session_id": session_id})

                if result.has_next():
                    row = result.get_next()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1] if row[1] else row[0],
                            "topic": row[2],
                            "created_at": str(row[3]),
                            "user_id": row[4]
                        }
                return None

            return await asyncio.to_thread(get_session)

        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None

    async def get_all_memories(self) -> List[Dict]:
        """
        Get all standalone memory entries.

        Returns:
            List of memory entries
        """
        if not self.is_initialized:
            return []

        try:
            def get_memories():
                result = self.conn.execute("""
                    MATCH (m:Memory)
                    RETURN m.id, m.content, m.importance, m.created_at, m.last_accessed
                    ORDER BY m.importance DESC, m.last_accessed DESC
                """)

                memories = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        memories.append({
                            "id": row[0],
                            "content": row[1],
                            "importance": row[2],
                            "created_at": str(row[3]),
                            "last_accessed": str(row[4])
                        })
                return memories

            return await asyncio.to_thread(get_memories)

        except Exception as e:
            print(f"Error getting all memories: {e}")
            return []

    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
            if self.db:
                del self.db
            self.is_initialized = False
        except Exception as e:
            print(f"Error closing Kuzu connection for {self.locrit_name}: {e}")