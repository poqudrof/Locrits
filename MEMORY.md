# Locrit Memory System Documentation

## Overview

The Locrit memory system uses **Kuzu**, an embedded graph database, to store and manage per-Locrit conversation memories. Each Locrit maintains its own isolated memory graph, enabling persistent, context-aware conversations.

## Architecture

### Core Components

1. **KuzuMemoryService** (`src/services/kuzu_memory_service.py`)
   - Manages individual Locrit memory instances
   - Handles graph database operations
   - Provides conversation history and search capabilities

2. **MemoryManagerService** (`src/services/memory_manager_service.py`)
   - Coordinates memory services for multiple Locrits
   - Routes memory requests to specific Locrit instances
   - Acts as a central memory coordinator

3. **Memory Integration Points**
   - HTTP Chat API (`backend/routes/chat.py`)
   - WebSocket Chat Handler (`backend/routes/websocket.py`)
   - Memory Viewing API (`backend/routes/memory.py`)

## Data Storage Structure

### Database Location
```
data/memory/{locrit_name}/kuzu.db
```

Each Locrit gets its own Kuzu database file for complete isolation.

### Graph Schema

The memory is stored as a **graph database** with the following node types and relationships:

#### Node Types

**User Nodes**
```cypher
CREATE NODE TABLE User (
    user_id STRING,
    name STRING,
    created_at TIMESTAMP,
    PRIMARY KEY(user_id)
)
```

**Message Nodes**
```cypher
CREATE NODE TABLE Message (
    message_id STRING,
    content STRING,
    role STRING,
    timestamp TIMESTAMP,
    embedding FLOAT[],
    PRIMARY KEY(message_id)
)
```

**Session Nodes**
```cypher
CREATE NODE TABLE Session (
    session_id STRING,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    PRIMARY KEY(session_id)
)
```

**Concept Nodes**
```cypher
CREATE NODE TABLE Concept (
    concept_id STRING,
    name STRING,
    description STRING,
    confidence FLOAT,
    PRIMARY KEY(concept_id)
)
```

**Topic Nodes**
```cypher
CREATE NODE TABLE Topic (
    topic_id STRING,
    name STRING,
    summary STRING,
    PRIMARY KEY(topic_id)
)
```

**Memory Nodes**
```cypher
CREATE NODE TABLE Memory (
    memory_id STRING,
    content STRING,
    importance FLOAT,
    created_at TIMESTAMP,
    PRIMARY KEY(memory_id)
)
```

#### Relationships

**User-Message Relationships**
```cypher
CREATE REL TABLE SENT (FROM User TO Message, relationship_type STRING, timestamp TIMESTAMP)
CREATE REL TABLE RECEIVED (FROM User TO Message, response_to STRING)
```

**Session-Message Relationships**
```cypher
CREATE REL TABLE CONTAINS (FROM Session TO Message, sequence_number INT)
```

**Message-Concept Relationships**
```cypher
CREATE REL TABLE MENTIONS (FROM Message TO Concept, relevance FLOAT)
CREATE REL TABLE RELATES_TO (FROM Concept TO Concept, strength FLOAT, relationship_type STRING)
```

**Topic Relationships**
```cypher
CREATE REL TABLE DISCUSSES (FROM Message TO Topic, relevance FLOAT)
CREATE REL TABLE BELONGS_TO (FROM Session TO Topic, primary_topic BOOLEAN)
```

**Memory Relationships**
```cypher
CREATE REL TABLE TRIGGERS (FROM Message TO Memory, trigger_strength FLOAT)
CREATE REL TABLE REFERENCES (FROM Memory TO Concept, reference_type STRING)
```

## Memory Operations

### 1. Message Storage

When a message is sent or received, the system:

```python
async def save_message(self, locrit_name: str, role: str, content: str,
                      session_id: str, user_id: str = "unknown") -> bool:
    # 1. Create/update User node
    # 2. Create/update Session node
    # 3. Create Message node with embedding
    # 4. Create relationships (SENT/RECEIVED, CONTAINS)
    # 5. Extract and link concepts
    # 6. Update conversation flow
```

**Storage Flow:**
1. **User Node**: Create or update user information
2. **Session Node**: Create or update conversation session
3. **Message Node**: Store message with timestamp and role
4. **Embeddings**: Generate vector embeddings for semantic search
5. **Relationships**: Link messages to users, sessions, and concepts

### 2. Conversation History Retrieval

For context-aware responses:

```python
async def get_conversation_history(self, locrit_name: str, session_id: str,
                                 limit: int = 20) -> List[Dict]:
    # Retrieve last N messages from session in chronological order
    # Format: [{"role": "user/assistant", "content": "...", "timestamp": "..."}]
```

**Query Process:**
1. Find Session node by `session_id`
2. Get connected Message nodes via `CONTAINS` relationship
3. Order by timestamp (newest first)
4. Limit results and format for LLM consumption

### 3. Memory Search

Semantic search across stored memories:

```python
async def search_memories(self, locrit_name: str, query: str,
                         limit: int = 10) -> List[Dict]:
    # 1. Generate query embedding
    # 2. Perform vector similarity search
    # 3. Return relevant memories with scores
```

**Search Types:**
- **Semantic Search**: Vector similarity using embeddings
- **Keyword Search**: Text-based matching
- **Concept Search**: Find messages mentioning specific concepts
- **Time-based Search**: Messages from specific time periods

### 4. Memory Summary

Comprehensive memory overview:

```python
async def get_full_memory_summary(self, locrit_name: str) -> Dict:
    return {
        "statistics": {...},
        "recent_sessions": [...],
        "top_concepts": [...],
        "memory_insights": [...]
    }
```

## Integration Points

### HTTP Chat API

**Location**: `backend/routes/chat.py`

**Memory Integration:**
1. **Save User Message**: Before sending to Ollama
2. **Retrieve Context**: Get conversation history (last 20 messages)
3. **Build Context**: Include history in LLM prompt
4. **Save Response**: Store assistant's response

```python
# Context building
messages = [
    SystemMessage(content=system_prompt),
    *conversation_history,  # Retrieved from memory
    HumanMessage(content=current_message)
]
```

### WebSocket Chat Handler

**Location**: `backend/routes/websocket.py`

**Memory Integration:**
- Same flow as HTTP API
- Real-time message saving during streaming
- Context retrieval for each message
- Session persistence across connections

### Memory Viewing API

**Location**: `backend/routes/memory.py`

**Endpoints:**
- `GET /api/locrits/{name}/memory/summary` - Complete memory overview
- `GET /api/locrits/{name}/memory/search` - Search memories
- `GET /api/locrits/{name}/memory/sessions` - List conversation sessions
- `GET /api/locrits/{name}/memory/concepts` - Extracted concepts
- `GET /api/locrits/{name}/memory/stats` - Memory statistics

## Session Management

### Session ID Format

**HTTP API**: `web_{user_id}_{locrit_name}`
**WebSocket**: `websocket_{user_id}_{locrit_name}`

### Session Lifecycle

1. **Creation**: First message in a conversation
2. **Continuation**: Subsequent messages with same session_id
3. **Context**: Last 20 messages used for LLM context
4. **Persistence**: Sessions stored indefinitely in graph

## Memory Features

### 1. Conversation Context

- **Context Window**: Last 20 messages per session
- **Role Preservation**: User vs Assistant message tracking
- **Temporal Ordering**: Chronological message sequence
- **Cross-Session**: Memory persists across app restarts

### 2. Semantic Understanding

- **Embeddings**: Vector representations for semantic search
- **Concept Extraction**: Automatic identification of key concepts
- **Topic Modeling**: Conversation topic categorization
- **Relationship Mapping**: Connections between concepts

### 3. Search Capabilities

- **Vector Search**: Semantic similarity matching
- **Full-Text Search**: Keyword-based retrieval
- **Filtered Search**: By time, user, session, or concept
- **Ranked Results**: Relevance scoring

### 4. Memory Insights

- **Usage Statistics**: Message counts, session lengths
- **Concept Networks**: Relationship graphs between ideas
- **Conversation Patterns**: Temporal interaction analysis
- **Memory Evolution**: How understanding develops over time

## Configuration

### Memory Settings per Locrit

```yaml
access_to:
  quick_memory: true     # Basic memory access (5 results max)
  full_memory: true      # Complete memory access
  logs: true            # Access to conversation logs
```

### Memory Limits

- **Context Window**: 20 messages (configurable)
- **Search Results**: 50 maximum (API limited)
- **Quick Memory**: 5 results maximum
- **Embedding Dimensions**: 384 (sentence-transformers default)

## Performance Considerations

### Database Performance

- **Per-Locrit Isolation**: Separate databases prevent interference
- **Graph Queries**: Optimized traversal patterns
- **Indexing**: Primary keys and timestamp indexes
- **Memory Usage**: Embeddings cached in memory

### Scalability

- **Horizontal**: Each Locrit scales independently
- **Storage**: Disk-based persistence
- **Concurrency**: Async operations for non-blocking I/O
- **Cleanup**: Configurable retention policies (future)

## Security & Privacy

### Data Isolation

- **Per-Locrit Databases**: Complete separation between Locrits
- **Access Control**: Permission-based memory access
- **User Anonymization**: Configurable user ID handling

### Data Retention

- **Persistent Storage**: Memories stored indefinitely
- **Privacy Controls**: User-specific data handling
- **Cleanup Options**: Manual memory clearing (future feature)

## Troubleshooting

### Common Issues

1. **Database Corruption**: Delete `data/memory/{locrit}/kuzu.db` to reset
2. **Memory Not Persisting**: Check file permissions in `data/memory/`
3. **Context Not Working**: Verify memory saving logs
4. **Search Problems**: Check embedding generation

### Debug Information

**Memory Logs**: Check for saving/retrieval messages in backend logs
**Database Status**: Monitor `data/memory/` directory
**API Testing**: Use memory endpoints to verify storage

## Future Enhancements

### Planned Features

- **Memory Consolidation**: Compress old conversations
- **Smart Forgetting**: Importance-based retention
- **Cross-Locrit Memory**: Shared knowledge bases
- **Memory Backup**: Export/import capabilities
- **Advanced Analytics**: Conversation insights dashboard

### Extension Points

- **Custom Embeddings**: Pluggable embedding models
- **External Storage**: Cloud database backends
- **Memory Triggers**: Event-based memory actions
- **API Webhooks**: Memory change notifications

## Example Memory Flow

```
1. User: "My name is Alice"
   └── Save message to Alice's session
   └── Extract concept: "name=Alice"
   └── Generate embedding
   └── Link to user and session

2. Assistant: "Nice to meet you, Alice!"
   └── Save response to same session
   └── Link to previous message
   └── Update conversation flow

3. User: "What's my name?"
   └── Retrieve conversation history
   └── Include previous context in prompt
   └── LLM sees: [System, "My name is Alice", "Nice to meet you", "What's my name?"]
   └── Response: "Your name is Alice!"

4. Memory Search: "name"
   └── Vector search finds "My name is Alice"
   └── Returns relevant conversation snippets
   └── Ranked by semantic similarity
```

This memory system enables Locrits to maintain coherent, persistent conversations while providing powerful search and analysis capabilities.