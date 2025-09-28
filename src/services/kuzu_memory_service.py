"""
Kuzu-based memory service for per-Locrit memory isolation.
Each Locrit gets its own Kuzu database instance for complete memory separation.
"""

import kuzu
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from langchain_kuzu.graphs.kuzu_graph import KuzuGraph


class KuzuMemoryService:
    """Kuzu-based memory service with per-Locrit database isolation."""

    def __init__(self, locrit_name: str, base_path: str = "data/memory"):
        """
        Initialize Kuzu memory service for a specific Locrit.

        Args:
            locrit_name: Name of the Locrit (used for database path)
            base_path: Base directory for memory databases
        """
        self.locrit_name = locrit_name
        self.base_path = Path(base_path)
        self.db_dir = self.base_path / self._sanitize_name(locrit_name)
        self.db_path = self.db_dir / "kuzu.db"

        self.db = None
        self.conn = None
        self.graph = None
        self.is_initialized = False

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

            # Create schema
            await self._create_schema()

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

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Message(
                    id STRING,
                    role STRING,
                    content STRING,
                    timestamp TIMESTAMP,
                    session_id STRING,
                    metadata STRING,
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

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Concept(
                    id STRING,
                    name STRING,
                    type STRING,
                    description STRING,
                    confidence DOUBLE,
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

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Memory(
                    id STRING,
                    content STRING,
                    importance DOUBLE,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
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

        except Exception as e:
            print(f"Error creating schema for {self.locrit_name}: {e}")
            raise

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

            # Insert message
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
        """Extract concepts from message content and create relationships."""
        try:
            # Simple concept extraction (can be enhanced with NLP)
            import re

            # Extract capitalized words as potential concepts
            concepts = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', content)
            concepts = list(set(concepts))  # Remove duplicates

            for concept_name in concepts:
                concept_id = f"concept_{concept_name.lower()}"

                # Create or merge concept
                await asyncio.to_thread(self.conn.execute, """
                    MERGE (c:Concept {id: $concept_id})
                    ON CREATE SET c.name = $concept_name, c.type = 'extracted', c.confidence = 0.7
                """, {"concept_id": concept_id, "concept_name": concept_name})

                # Link message to concept
                await asyncio.to_thread(self.conn.execute, """
                    MATCH (m:Message {id: $message_id}), (c:Concept {id: $concept_id})
                    CREATE (m)-[:MENTIONS {confidence: 0.7}]->(c)
                """, {"message_id": message_id, "concept_id": concept_id})

        except Exception as e:
            print(f"Error extracting concepts: {e}")

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

    async def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search through memories using content matching.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        if not self.is_initialized:
            return []

        try:
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
                            "session_id": row[4]
                        })
                return memories

            return await asyncio.to_thread(search_messages)

        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

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