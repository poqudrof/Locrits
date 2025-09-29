"""
Graph-based memory service for precise, structured memories.

Handles facts, events, relationships, and structured knowledge using Kuzu graph database.
This service is optimized for:
- Precise fact storage and retrieval
- Relationship tracking between entities
- Temporal sequences and event chains
- Structured knowledge representation
"""

import kuzu
import os
import json
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

def safe_json_dumps(obj: Any) -> str:
    """Safely serialize objects to JSON, handling datetime objects."""
    def json_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=json_serializer)
from langchain_kuzu.graphs.kuzu_graph import KuzuGraph

from .interfaces import GraphMemoryService as BaseGraphService, MemoryItem, MemorySearchResult, MemoryType
from .config import MemoryConfig, GraphMemoryConfig


class KuzuGraphMemoryService(BaseGraphService):
    """Kuzu-based graph memory service for structured, precise memories."""

    def __init__(self, locrit_name: str, config: MemoryConfig):
        super().__init__(locrit_name, config.graph.__dict__)
        self.full_config = config
        self.graph_config = config.graph

        self.base_path = Path(config.base_path)
        self.db_dir = self.base_path / "graph" / self._sanitize_name(locrit_name)
        self.db_path = self.db_dir / "kuzu.db"

        self.db = None
        self.conn = None
        self.graph = None

        # Create directory if it doesn't exist
        self.db_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize Locrit name for use as directory name."""
        return re.sub(r'[^\w\-_]', '_', name.lower())

    async def initialize(self) -> bool:
        """Initialize the Kuzu database and create schema."""
        if not self.graph_config.enabled:
            return False

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
            print(f"Error initializing graph memory for {self.locrit_name}: {e}")
            return False

    async def _create_schema(self) -> None:
        """Create the graph schema for structured memory storage."""
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
                CREATE NODE TABLE IF NOT EXISTS Message(
                    id STRING,
                    role STRING,
                    content STRING,
                    timestamp TIMESTAMP,
                    session_id STRING,
                    metadata STRING,
                    importance DOUBLE,
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
                    created_at TIMESTAMP,
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
                CREATE NODE TABLE IF NOT EXISTS Fact(
                    id STRING,
                    subject STRING,
                    predicate STRING,
                    object STRING,
                    confidence DOUBLE,
                    source_message_id STRING,
                    created_at TIMESTAMP,
                    PRIMARY KEY(id)
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE NODE TABLE IF NOT EXISTS Event(
                    id STRING,
                    name STRING,
                    description STRING,
                    event_type STRING,
                    timestamp TIMESTAMP,
                    importance DOUBLE,
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
                CREATE REL TABLE IF NOT EXISTS PART_OF(
                    FROM Message TO Session,
                    position INT64
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS MENTIONS(
                    FROM Message TO Concept,
                    confidence DOUBLE,
                    position INT64
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS DISCUSSES(
                    FROM Session TO Topic,
                    relevance DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                    FROM Concept TO Concept,
                    relationship_type STRING,
                    strength DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS RESPONDS_TO(
                    FROM Message TO Message,
                    delay_seconds INT64
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS CONTAINS_FACT(
                    FROM Message TO Fact,
                    confidence DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS TRIGGERS_EVENT(
                    FROM Message TO Event,
                    causality DOUBLE
                )
            """)

            await asyncio.to_thread(self.conn.execute, """
                CREATE REL TABLE IF NOT EXISTS FOLLOWED_BY(
                    FROM Event TO Event,
                    time_delta INT64
                )
            """)

        except Exception as e:
            print(f"Error creating graph schema for {self.locrit_name}: {e}")
            raise

    async def store_memory(self, item: MemoryItem) -> str:
        """Store a memory item in the graph."""
        if not self.is_initialized:
            raise Exception(f"Graph memory service not initialized for {self.locrit_name}")

        try:
            # Determine storage strategy based on content type
            memory_type = item.metadata.get('graph_type', 'message')

            if memory_type == 'fact':
                return await self._store_fact(item)
            elif memory_type == 'event':
                return await self._store_event(item)
            elif memory_type == 'concept':
                return await self._store_concept(item)
            else:
                return await self._store_message(item)

        except Exception as e:
            print(f"Error storing graph memory: {e}")
            raise

    async def _store_message(self, item: MemoryItem) -> str:
        """Store a message-based memory."""
        timestamp = item.created_at
        message_id = item.id or f"msg_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        # Get session and user info from metadata
        session_id = item.metadata.get('session_id', f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}")
        user_id = item.metadata.get('user_id', 'default')
        role = item.metadata.get('role', 'user')

        # Ensure user and session exist
        await self._ensure_user_exists(user_id)
        await self._ensure_session_exists(session_id, user_id)

        # Insert message
        await asyncio.to_thread(self.conn.execute, """
            CREATE (m:Message {
                id: $message_id,
                role: $role,
                content: $content,
                timestamp: $timestamp,
                session_id: $session_id,
                metadata: $metadata,
                importance: $importance
            })
        """, {
            "message_id": message_id,
            "role": role,
            "content": item.content,
            "timestamp": timestamp,
            "session_id": session_id,
            "metadata": safe_json_dumps(item.metadata),
            "importance": item.importance
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

        # Extract and link concepts if enabled
        if self.graph_config.auto_create_relationships:
            await self._extract_and_link_concepts(message_id, item.content)

        # Link to previous message in session
        await self._link_to_previous_message(message_id, session_id)

        return message_id

    async def _store_fact(self, item: MemoryItem) -> str:
        """Store a structured fact."""
        fact_data = item.metadata.get('fact_data', {})
        fact_id = item.id or f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        await asyncio.to_thread(self.conn.execute, """
            CREATE (f:Fact {
                id: $fact_id,
                subject: $subject,
                predicate: $predicate,
                object: $object,
                confidence: $confidence,
                source_message_id: $source_message_id,
                created_at: $created_at
            })
        """, {
            "fact_id": fact_id,
            "subject": fact_data.get('subject', ''),
            "predicate": fact_data.get('predicate', ''),
            "object": fact_data.get('object', ''),
            "confidence": fact_data.get('confidence', item.importance),
            "source_message_id": fact_data.get('source_message_id', ''),
            "created_at": item.created_at
        })

        return fact_id

    async def _store_event(self, item: MemoryItem) -> str:
        """Store an event-based memory."""
        event_data = item.metadata.get('event_data', {})
        event_id = item.id or f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        await asyncio.to_thread(self.conn.execute, """
            CREATE (e:Event {
                id: $event_id,
                name: $name,
                description: $description,
                event_type: $event_type,
                timestamp: $timestamp,
                importance: $importance
            })
        """, {
            "event_id": event_id,
            "name": event_data.get('name', item.content[:50]),
            "description": item.content,
            "event_type": event_data.get('event_type', 'general'),
            "timestamp": event_data.get('timestamp', item.created_at),
            "importance": item.importance
        })

        return event_id

    async def _store_concept(self, item: MemoryItem) -> str:
        """Store a concept-based memory."""
        concept_data = item.metadata.get('concept_data', {})
        concept_id = item.id or f"concept_{item.content.lower().replace(' ', '_')}"

        await asyncio.to_thread(self.conn.execute, """
            MERGE (c:Concept {id: $concept_id})
            ON CREATE SET c.name = $name, c.type = $type, c.description = $description,
                         c.confidence = $confidence, c.created_at = $created_at
            ON MATCH SET c.description = $description, c.confidence = $confidence
        """, {
            "concept_id": concept_id,
            "name": concept_data.get('name', item.content),
            "type": concept_data.get('type', 'extracted'),
            "description": concept_data.get('description', item.content),
            "confidence": concept_data.get('confidence', item.importance),
            "created_at": item.created_at
        })

        return concept_id

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory by ID."""
        if not self.is_initialized:
            return None

        try:
            # Try different node types
            for node_type in ['Message', 'Fact', 'Event', 'Concept']:
                result = await asyncio.to_thread(self._get_node_by_id, node_type, memory_id)
                if result:
                    return self._convert_to_memory_item(result, node_type.lower())

            return None

        except Exception as e:
            print(f"Error retrieving memory {memory_id}: {e}")
            return None

    def _get_node_by_id(self, node_type: str, node_id: str) -> Optional[Dict]:
        """Get a node by ID and type."""
        try:
            if node_type == 'Message':
                result = self.conn.execute("""
                    MATCH (n:Message {id: $id})
                    RETURN n.id, n.role, n.content, n.timestamp, n.session_id, n.metadata, n.importance
                """, {"id": node_id})
            elif node_type == 'Fact':
                result = self.conn.execute("""
                    MATCH (n:Fact {id: $id})
                    RETURN n.id, n.subject, n.predicate, n.object, n.confidence, n.created_at
                """, {"id": node_id})
            elif node_type == 'Event':
                result = self.conn.execute("""
                    MATCH (n:Event {id: $id})
                    RETURN n.id, n.name, n.description, n.event_type, n.timestamp, n.importance
                """, {"id": node_id})
            elif node_type == 'Concept':
                result = self.conn.execute("""
                    MATCH (n:Concept {id: $id})
                    RETURN n.id, n.name, n.type, n.description, n.confidence, n.created_at
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

        if memory_type == 'message':
            return MemoryItem(
                id=data[0],
                content=data[2],
                memory_type=MemoryType.GRAPH,
                importance=data[6] if len(data) > 6 else 0.5,
                created_at=data[3],
                last_accessed=datetime.now(),
                metadata=json.loads(data[5]) if len(data) > 5 and data[5] else {},
                tags=[]
            )
        elif memory_type == 'fact':
            return MemoryItem(
                id=data[0],
                content=f"{data[1]} {data[2]} {data[3]}",  # subject predicate object
                memory_type=MemoryType.GRAPH,
                importance=data[4],
                created_at=data[5],
                last_accessed=datetime.now(),
                metadata={"fact_data": {"subject": data[1], "predicate": data[2], "object": data[3]}},
                tags=["fact"]
            )
        elif memory_type == 'event':
            return MemoryItem(
                id=data[0],
                content=data[2],  # description
                memory_type=MemoryType.GRAPH,
                importance=data[5],
                created_at=data[4],
                last_accessed=datetime.now(),
                metadata={"event_data": {"name": data[1], "event_type": data[3]}},
                tags=["event"]
            )
        elif memory_type == 'concept':
            return MemoryItem(
                id=data[0],
                content=data[3],  # description
                memory_type=MemoryType.GRAPH,
                importance=data[4],
                created_at=data[5],
                last_accessed=datetime.now(),
                metadata={"concept_data": {"name": data[1], "type": data[2]}},
                tags=["concept"]
            )

    async def search_memories(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[MemorySearchResult]:
        """Search for memories using graph queries."""
        if not self.is_initialized:
            return []

        try:
            results = []

            # Search messages
            message_results = await self._search_messages(query, limit // 2)
            results.extend(message_results)

            # Search concepts
            concept_results = await self._search_concepts(query, limit // 2)
            results.extend(concept_results)

            # Apply filters if provided
            if filters:
                results = self._apply_filters(results, filters)

            # Sort by relevance and limit
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"Error searching graph memories: {e}")
            return []

    async def _search_messages(self, query: str, limit: int) -> List[MemorySearchResult]:
        """Search messages by content."""
        def search():
            result = self.conn.execute("""
                MATCH (m:Message)
                WHERE m.content CONTAINS $query
                RETURN m.id, m.role, m.content, m.timestamp, m.session_id, m.metadata, m.importance
                ORDER BY m.importance DESC, m.timestamp DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})

            results = []
            while result.has_next():
                row = result.get_next()
                if row:
                    memory_item = MemoryItem(
                        id=row[0],
                        content=row[2],
                        memory_type=MemoryType.GRAPH,
                        importance=row[6] if len(row) > 6 else 0.5,
                        created_at=row[3],
                        last_accessed=datetime.now(),
                        metadata=json.loads(row[5]) if row[5] else {},
                        tags=["message"]
                    )

                    # Simple relevance scoring based on query match
                    relevance = min(1.0, query.lower().count(row[2].lower()) * 0.1 + 0.5)

                    results.append(MemorySearchResult(
                        item=memory_item,
                        relevance_score=relevance,
                        reasoning=f"Content contains '{query}'"
                    ))
            return results

        return await asyncio.to_thread(search)

    async def _search_concepts(self, query: str, limit: int) -> List[MemorySearchResult]:
        """Search concepts by name or description."""
        def search():
            result = self.conn.execute("""
                MATCH (c:Concept)
                WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                RETURN c.id, c.name, c.type, c.description, c.confidence, c.created_at
                ORDER BY c.confidence DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})

            results = []
            while result.has_next():
                row = result.get_next()
                if row:
                    memory_item = MemoryItem(
                        id=row[0],
                        content=row[3],
                        memory_type=MemoryType.GRAPH,
                        importance=row[4],
                        created_at=row[5],
                        last_accessed=datetime.now(),
                        metadata={"concept_data": {"name": row[1], "type": row[2]}},
                        tags=["concept"]
                    )

                    relevance = min(1.0, row[4] + 0.2)  # Use confidence as base relevance

                    results.append(MemorySearchResult(
                        item=memory_item,
                        relevance_score=relevance,
                        reasoning=f"Concept match for '{query}'"
                    ))
            return results

        return await asyncio.to_thread(search)

    def _apply_filters(self, results: List[MemorySearchResult], filters: Dict[str, Any]) -> List[MemorySearchResult]:
        """Apply filters to search results."""
        filtered = results

        if 'min_importance' in filters:
            filtered = [r for r in filtered if r.item.importance >= filters['min_importance']]

        if 'tags' in filters:
            required_tags = set(filters['tags'])
            filtered = [r for r in filtered if required_tags.intersection(set(r.item.tags))]

        if 'date_range' in filters:
            start_date = filters['date_range'].get('start')
            end_date = filters['date_range'].get('end')
            if start_date:
                filtered = [r for r in filtered if r.item.created_at >= start_date]
            if end_date:
                filtered = [r for r in filtered if r.item.created_at <= end_date]

        return filtered

    async def create_relationship(self, from_id: str, to_id: str,
                                 relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two memory items."""
        if not self.is_initialized:
            return False

        try:
            # Create relationship based on type
            if relationship_type == "RELATES_TO":
                await asyncio.to_thread(self.conn.execute, """
                    MATCH (a {id: $from_id}), (b {id: $to_id})
                    CREATE (a)-[:RELATES_TO {
                        relationship_type: $rel_type,
                        strength: $strength,
                        created_at: $created_at
                    }]->(b)
                """, {
                    "from_id": from_id,
                    "to_id": to_id,
                    "rel_type": properties.get('type', 'general') if properties else 'general',
                    "strength": properties.get('strength', 0.5) if properties else 0.5,
                    "created_at": datetime.now()
                })

            return True

        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False

    async def get_related_memories(self, memory_id: str, relationship_types: List[str] = None,
                                  max_depth: int = 2) -> List[MemorySearchResult]:
        """Get memories related through graph relationships."""
        if not self.is_initialized:
            return []

        try:
            rel_filter = ""
            if relationship_types:
                rel_types = "', '".join(relationship_types)
                rel_filter = f"WHERE type(r) IN ['{rel_types}']"

            def get_related():
                result = self.conn.execute(f"""
                    MATCH (start {{id: $memory_id}})-[r*1..{max_depth}]-(related)
                    {rel_filter}
                    RETURN DISTINCT related.id, labels(related)[0], related
                    LIMIT 20
                """, {"memory_id": memory_id})

                results = []
                while result.has_next():
                    row = result.get_next()
                    if row and row[0] != memory_id:  # Don't include the starting node
                        # Convert based on node type
                        node_data = {"type": row[1].lower(), "data": row[2]}
                        memory_item = self._convert_to_memory_item(node_data, row[1].lower())

                        results.append(MemorySearchResult(
                            item=memory_item,
                            relevance_score=0.8,  # High relevance for related items
                            reasoning=f"Related through graph relationships"
                        ))

                return results

            return await asyncio.to_thread(get_related)

        except Exception as e:
            print(f"Error getting related memories: {e}")
            return []

    async def get_memory_network(self, center_id: str, radius: int = 2) -> Dict[str, Any]:
        """Get the network of memories around a central memory."""
        if not self.is_initialized:
            return {}

        try:
            def get_network():
                # Get nodes within radius
                result = self.conn.execute(f"""
                    MATCH (center {{id: $center_id}})-[r*0..{radius}]-(node)
                    RETURN DISTINCT node.id, labels(node)[0], node
                """, {"center_id": center_id})

                nodes = []
                while result.has_next():
                    row = result.get_next()
                    if row:
                        nodes.append({
                            "id": row[0],
                            "type": row[1],
                            "properties": dict(row[2])
                        })

                # Get relationships between these nodes
                node_ids = [n["id"] for n in nodes]
                rel_result = self.conn.execute("""
                    MATCH (a)-[r]->(b)
                    WHERE a.id IN $node_ids AND b.id IN $node_ids
                    RETURN a.id, type(r), b.id, properties(r)
                """, {"node_ids": node_ids})

                relationships = []
                while rel_result.has_next():
                    rel_row = rel_result.get_next()
                    if rel_row:
                        relationships.append({
                            "from": rel_row[0],
                            "type": rel_row[1],
                            "to": rel_row[2],
                            "properties": dict(rel_row[3])
                        })

                return {
                    "center_id": center_id,
                    "radius": radius,
                    "nodes": nodes,
                    "relationships": relationships,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships)
                }

            return await asyncio.to_thread(get_network)

        except Exception as e:
            print(f"Error getting memory network: {e}")
            return {}

    # Helper methods from original service
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
        Concept extraction is now handled by the LLM through memory tools.
        The LLM decides what concepts to store and how to relate them.
        """
        # Concept extraction is now LLM-driven through memory tools
        # No automatic extraction based on capitalized letters
        pass

    async def _link_to_previous_message(self, message_id: str, session_id: str) -> None:
        """Link message to previous message in the same session."""
        try:
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
                    await asyncio.to_thread(self.conn.execute, """
                        MATCH (prev:Message {id: $prev_id}), (curr:Message {id: $message_id})
                        CREATE (curr)-[:RESPONDS_TO {delay_seconds: 0}]->(prev)
                    """, {"prev_id": prev_id, "message_id": message_id})

        except Exception as e:
            print(f"Error linking to previous message: {e}")

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory."""
        if not self.is_initialized:
            return False

        try:
            # Update based on what fields are provided
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

            return True

        except Exception as e:
            print(f"Error updating memory {memory_id}: {e}")
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
            print(f"Error deleting memory {memory_id}: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if not self.is_initialized:
            return {"error": "Not initialized"}

        try:
            def get_stats():
                stats = {}

                # Count nodes by type
                for node_type in ['Message', 'Concept', 'Session', 'User', 'Fact', 'Event']:
                    result = self.conn.execute(f"MATCH (n:{node_type}) RETURN COUNT(n)")
                    if result.has_next():
                        row = result.get_next()
                        stats[f"{node_type.lower()}_count"] = row[0] if row else 0

                # Count relationships
                result = self.conn.execute("MATCH ()-[r]->() RETURN COUNT(r)")
                if result.has_next():
                    row = result.get_next()
                    stats["relationship_count"] = row[0] if row else 0

                return stats

            return await asyncio.to_thread(get_stats)

        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_memories(self, retention_days: int = 30) -> int:
        """Clean up old, low-importance memories."""
        if not self.is_initialized:
            return 0

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # Delete low-importance messages older than retention period
            result = await asyncio.to_thread(self.conn.execute, """
                MATCH (m:Message)
                WHERE m.timestamp < $cutoff_date AND m.importance < 0.3
                DETACH DELETE m
                RETURN COUNT(m)
            """, {"cutoff_date": cutoff_date})

            if result.has_next():
                row = result.get_next()
                return row[0] if row else 0

            return 0

        except Exception as e:
            print(f"Error cleaning up memories: {e}")
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
            print(f"Error closing graph connection for {self.locrit_name}: {e}")