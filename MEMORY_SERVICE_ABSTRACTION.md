# Memory Service Abstraction Layer

## Overview

The Locrits memory system has been refactored to support multiple memory backend implementations through an abstraction layer. This allows each Locrit to choose the most suitable memory service based on stability, features, and compatibility requirements.

## Architecture

### Core Components

```
src/services/memory/
├── interfaces.py              # Abstract base classes and interfaces
├── memory_factory.py          # Factory for creating memory services
├── kuzu_adapter.py           # Kuzu graph database adapter
├── plaintext_memory_service.py  # Plain text file storage
├── basic_memory_adapter.py    # Basic Memory MCP adapter
├── lancedb_langchain_adapter.py  # LanceDB LangChain adapter
└── lancedb_mcp_adapter.py    # LanceDB MCP adapter
```

### Class Hierarchy

```
BaseMemoryService (ABC)
├── GraphMemoryService (ABC)
│   └── KuzuMemoryAdapter
├── PlainTextMemoryService
├── BasicMemoryAdapter
├── LanceDBLangChainAdapter
└── LanceDBMCPAdapter
```

## Available Memory Services

### 1. Plain Text File Storage (`plaintext_file`)
**Status:** ✅ Stable
**Recommended:** Yes (default)

**Description:**
Simple file-based storage using JSON metadata and plain text files.

**Pros:**
- ✅ No external dependencies
- ✅ Stable, no compatibility issues
- ✅ Human-readable files
- ✅ Easy to debug and backup
- ✅ Works on all Python versions

**Cons:**
- ❌ Limited query capabilities
- ❌ Slower for large datasets
- ❌ No relationship tracking
- ❌ No semantic search

**File Structure:**
```
data/memory/{locrit_name}/plaintext/
├── index.json           # Metadata index
└── memories/
    ├── {id1}.txt       # Individual memory files
    ├── {id2}.txt
    └── ...
```

**Memory File Format:**
```
=== MEMORY METADATA ===
{
  "id": "uuid",
  "created_at": "2025-10-05T...",
  "importance": 0.8,
  "tags": ["fact", "user_preference"],
  "metadata": {...}
}
=== CONTENT ===
The actual memory content goes here...
```

### 2. Kuzu Graph Database (`kuzu_graph`)
**Status:** ⚠️ Experimental
**Recommended:** Only if you need advanced features

**Description:**
Sophisticated graph-based memory with relationships and vector embeddings.

**Pros:**
- ✅ Advanced relationship tracking
- ✅ Semantic search with embeddings
- ✅ Complex graph queries
- ✅ Memory networks and associations

**Cons:**
- ❌ Compatibility issues with Python 3.13+
- ❌ May cause segmentation faults
- ❌ Higher complexity
- ❌ More dependencies

**When to Use:**
- You need relationship tracking between memories
- Semantic search is critical
- You're on Python 3.11 or 3.12
- You can handle occasional crashes

### 3. Basic Memory MCP (`basic_memory`)
**Status:** ⚠️ Experimental
**Recommended:** For advanced users who want semantic search

**Description:**
Markdown-based knowledge graph with semantic search capabilities, accessed via Model Context Protocol (MCP).

**Pros:**
- ✅ Rich semantic markup
- ✅ Bi-directional read/write
- ✅ Knowledge graph structure
- ✅ Integrates with Obsidian
- ✅ Human-readable Markdown files
- ✅ Advanced semantic search

**Cons:**
- ❌ Requires MCP setup
- ❌ Experimental/newer technology
- ❌ External dependency (uvx)
- ❌ More complex troubleshooting

**File Structure:**
```
data/memory/{locrit_name}/basic-memory/
└── *.md  # Markdown files with semantic markup
```

**Memory File Format (Markdown):**
```markdown
# User Preference: Python

The user prefers Python over JavaScript for backend development.

Related: [[programming]], [[languages]]
Tags: #user_preference #coding
```

**MCP Tools Used:**
- `write_note` - Store new memories as Markdown
- `read_note` - Retrieve specific memories
- `search` - Semantic search across all memories
- `build_context` - Build knowledge graph context

**Setup Requirements:**
1. Install uvx: `pip install uvx`
2. Install basic-memory: `uvx basic-memory`
3. Configure MCP in `.mcp.json`
4. Set `BASIC_MEMORY_PATH` environment variable

**When to Use:**
- You want semantic search capabilities
- You prefer Markdown-based storage
- You want to use Obsidian or other Markdown tools
- You're comfortable with MCP setup

### 4. LanceDB LangChain (`lancedb_langchain`)
**Status:** ✅ Stable
**Recommended:** For users who need vector search and semantic capabilities

**Description:**
Vector database with direct Python/LangChain integration for fast semantic search and persistent storage.

**Pros:**
- ✅ Fast vector-based semantic search
- ✅ Persistent storage with LanceDB
- ✅ Direct Python integration (no MCP needed)
- ✅ Multimodal support (text + images)
- ✅ LangChain ecosystem compatibility
- ✅ Efficient for large datasets

**Cons:**
- ❌ Requires embedding model (Ollama)
- ❌ Higher memory usage than plaintext
- ❌ More dependencies
- ❌ Slightly more complex setup

**File Structure:**
```
data/memory/{locrit_name}/lancedb_langchain/
└── *.lance  # LanceDB internal format
```

**Embedding Models:**
- Uses Ollama for embeddings (default: `nomic-embed-text`)
- Configurable embedding dimension (default: 768)

**Setup Requirements:**
1. Install dependencies: `pip install lancedb tantivy langchain-community`
2. Ensure Ollama is running: `http://localhost:11434`
3. Pull embedding model: `ollama pull nomic-embed-text`

**When to Use:**
- You need semantic search capabilities
- You have large amounts of conversational data
- You want Python-native integration
- You prefer stable, production-ready solutions

### 5. LanceDB MCP (`lancedb_mcp`)
**Status:** ⚠️ Experimental
**Recommended:** For advanced users exploring MCP protocol

**Description:**
Vector database via Model Context Protocol for remote-capable semantic search.

**Pros:**
- ✅ Standardized MCP protocol
- ✅ Remote-capable architecture
- ✅ Efficient vector operations
- ✅ Semantic search capabilities
- ✅ Future-proof with MCP ecosystem

**Cons:**
- ❌ Requires MCP setup
- ❌ Experimental/newer integration
- ❌ External dependency (uvx, mcp-lance-db)
- ❌ More complex troubleshooting
- ❌ Less documentation

**File Structure:**
```
data/memory/{locrit_name}/lancedb_mcp/
└── *.lance  # LanceDB internal format
```

**MCP Tools Used:**
- `create_table` - Initialize vector table
- `add_vector` - Store embeddings
- `search_vectors` - Semantic similarity search
- `query_by_metadata` - Filter by metadata
- `delete_by_metadata` - Remove vectors
- `get_table_stats` - Database statistics
- `embed_text` - Generate embeddings (optional)

**Setup Requirements:**
1. Install uvx: `pip install uvx`
2. Install mcp-lance-db: `uvx mcp-lance-db`
3. Configure MCP in `.mcp.json`
4. Set `LANCEDB_URI` environment variable

**When to Use:**
- You're exploring MCP protocol
- You want remote database access
- You need standardized tool interfaces
- You're comfortable with experimental tech

### 6. Disabled (`disabled`)
**Status:** ✅ Stable

**Description:**
No memory persistence. Conversations are not saved.

**Use Cases:**
- Testing
- Temporary Locrits
- Privacy-sensitive applications
- Troubleshooting memory issues

## Configuration

### Per-Locrit Configuration

Edit `config.yaml`:

```yaml
locrits:
  default_settings:
    memory_service: plaintext_file  # Default for new Locrits

  instances:
    Bob Technique:
      memory_service: plaintext_file  # Stable choice

    Advanced Locrit:
      memory_service: kuzu_graph      # Advanced features (risky)

    Semantic Bot:
      memory_service: basic_memory    # Markdown + semantic search (experimental)

    Vector Search Bot:
      memory_service: lancedb_langchain  # Fast vector search (stable)

    MCP Explorer:
      memory_service: lancedb_mcp     # Vector search via MCP (experimental)

    Temporary Bot:
      memory_service: disabled        # No persistence
```

### Global Memory Configuration

```yaml
memory:
  enabled: false  # Legacy - set to false to disable globally
  use_kuzu: false  # Legacy - not used with new system
  database_path: data/memory
  embedding_model: nomic-embed-text
  max_messages: 10000
```

## Frontend Integration

The memory service can be selected in the Locrit Settings page:

**Location:** Platform → Locrit Settings → "Type de mémoire magique"

**Options:**
1. **Fichiers texte (Recommandé)** - Plain text file storage
2. **LanceDB LangChain** - Vector search with Python integration
3. **Basic Memory (MCP)** - Markdown knowledge graph
4. **LanceDB MCP** - Vector search via MCP protocol
5. **Base de données Kuzu** - Graph database
6. **Désactivé** - No memory

**UI Features:**
- Visual indicators for stability (✅ Stable / ⚠️ Experimental)
- Description of pros/cons
- Automatic default to `plaintext_file`

## Usage in Code

### Creating a Memory Service

```python
from src.services.memory.memory_factory import MemoryServiceFactory

# Create a memory service
service = MemoryServiceFactory.create_memory_service(
    locrit_name="Bob Technique",
    service_type="plaintext_file",  # or "kuzu_graph" or "disabled"
    config={
        'database_path': 'data/memory',
        'embedding_model': 'nomic-embed-text'
    }
)

# Initialize
await service.initialize()
```

### Using the Memory Service Manager

```python
from src.services.memory.memory_factory import memory_service_manager

# Get or create service for a Locrit
service = await memory_service_manager.get_or_create_service(
    locrit_name="Bob Technique",
    service_type="plaintext_file",
    config={...}
)

# Use the service
await service.store_memory(memory_item)
results = await service.search_memories("query")
```

### Storing a Memory

```python
from src.services.memory.interfaces import MemoryItem, MemoryType
from datetime import datetime

memory = MemoryItem(
    id="unique-id",
    content="User prefers Python over JavaScript",
    memory_type=MemoryType.GRAPH,
    importance=0.8,
    created_at=datetime.now(),
    last_accessed=datetime.now(),
    metadata={"category": "preference"},
    tags=["user_preference", "coding"]
)

memory_id = await service.store_memory(memory)
```

### Searching Memories

```python
results = await service.search_memories(
    query="programming preferences",
    limit=10,
    filters={'min_importance': 0.5}
)

for result in results:
    print(f"Score: {result.relevance_score}")
    print(f"Content: {result.item.content}")
```

## Migration Guide

### From Kuzu to Plain Text

1. **Update config.yaml:**
   ```yaml
   Bob Technique:
     memory_service: plaintext_file  # Change from kuzu_graph
   ```

2. **Restart the application**

3. **Old memories in Kuzu remain in:**
   ```
   data/memory/bob_technique/kuzu.db
   ```

4. **New memories will be stored in:**
   ```
   data/memory/bob_technique/plaintext/
   ```

### Migration Script (Optional)

```python
# Future: Create migration script to export from Kuzu to plaintext
# Located at: scripts/migrate_kuzu_to_plaintext.py
```

## Implementation Checklist

- [x] Create abstract `BaseMemoryService` interface
- [x] Implement `KuzuMemoryAdapter` wrapper
- [x] Implement `PlainTextMemoryService`
- [x] Implement `BasicMemoryAdapter` (MCP)
- [x] Create `MemoryServiceFactory`
- [x] Add `memory_service` parameter to Locrit config
- [x] Update TypeScript types
- [x] Add UI selector in LocritSettings
- [x] Set `plaintext_file` as default for all Locrits
- [x] Configure Basic Memory in `.mcp.json`
- [x] Add dependencies to requirements.txt
- [x] Update documentation
- [ ] Test plain text service with conversations
- [ ] Test Basic Memory service with conversations
- [ ] Create migration script (Kuzu → Plaintext)
- [ ] Create migration script (any → Basic Memory)
- [ ] Add metrics/monitoring for memory services

## Testing

### Test Plain Text Service

```bash
# Run memory progression test
.venv/bin/python test_memory_progression_simple.py
```

### Test Service Switching

```python
# Create test script: test_memory_service_switching.py
import asyncio
from src.services.memory.memory_factory import MemoryServiceFactory

async def test_services():
    for service_type in ['plaintext_file', 'kuzu_graph', 'disabled']:
        service = MemoryServiceFactory.create_memory_service(
            locrit_name="Test Bot",
            service_type=service_type,
            config={'database_path': 'data/memory'}
        )
        if service:
            await service.initialize()
            print(f"✅ {service_type} initialized successfully")
            await service.close()

asyncio.run(test_services())
```

## Troubleshooting

### Kuzu Segmentation Faults

**Problem:** Kuzu crashes with segfault
**Solution:** Switch to `plaintext_file`

```yaml
memory_service: plaintext_file  # Instead of kuzu_graph
```

### Basic Memory MCP Connection Issues

**Problem:** Basic Memory service fails to initialize
**Symptoms:**
- "Failed to initialize memory service" error
- MCP connection timeout
- uvx command not found

**Solutions:**

1. **Install uvx:**
   ```bash
   pip install uvx
   ```

2. **Verify basic-memory is available:**
   ```bash
   uvx basic-memory --help
   ```

3. **Check MCP configuration in `.mcp.json`:**
   ```json
   {
     "mcpServers": {
       "basic-memory": {
         "command": "uvx",
         "args": ["basic-memory"],
         "env": {
           "BASIC_MEMORY_PATH": "data/memory/basic-memory"
         }
       }
     }
   }
   ```

4. **Check memory path exists:**
   ```bash
   mkdir -p data/memory/{locrit_name}/basic-memory
   ```

5. **Test MCP connection manually:**
   ```bash
   BASIC_MEMORY_PATH=data/memory/basic-memory uvx basic-memory
   ```

### Memory Not Persisting

**Check:**
1. `memory_service` is not set to `disabled`
2. File permissions on `data/memory/` directory
3. Disk space available
4. For Basic Memory: MCP server is properly configured

### Migration Issues

**Problem:** Old memories not accessible
**Solution:** Both storage systems coexist. Old Kuzu memories remain in `kuzu.db`, new memories go to `plaintext/` or `basic-memory/`.

## Future Enhancements

### Planned Features

1. **SQLite Memory Service** - SQL-based storage with full-text search
2. **Vector Database Service** - Pinecone, Weaviate, or Qdrant integration
3. **Hybrid Service** - Combine multiple backends
4. **Memory Migration Tools** - Convert between services
5. **Memory Export/Import** - Backup and restore
6. **Memory Analytics** - Usage statistics and insights

### API Endpoints (Planned)

```
GET  /api/locrits/{name}/memory/service/info
POST /api/locrits/{name}/memory/service/switch
GET  /api/locrits/{name}/memory/stats
POST /api/locrits/{name}/memory/export
POST /api/locrits/{name}/memory/import
```

## Performance Comparison

| Feature | Plain Text | LanceDB LC | LanceDB MCP | Basic Memory | Kuzu Graph | Disabled |
|---------|-----------|-----------|-------------|-------------|------------|----------|
| **Initialization** | Fast | Medium | Medium | Medium | Slow | Instant |
| **Storage** | O(1) | O(log n) | O(log n) | O(1) | O(log n) | N/A |
| **Search** | O(n) | O(log n) | O(log n) | O(log n) | O(log n) | N/A |
| **Relationships** | ❌ | ❌ | ❌ | ✅ (links) | ✅ | ❌ |
| **Semantic Search** | ❌ | ✅✅ | ✅✅ | ✅ | ✅ | ❌ |
| **Stability** | ✅✅✅ | ✅✅ | ⚠️ | ⚠️ | ⚠️ | ✅✅✅ |
| **Memory Usage** | Low | High | High | Medium | Medium | None |
| **Disk Usage** | Low | Medium | Medium | Low | Medium | None |
| **Human Readable** | ✅ | ❌ | ❌ | ✅✅ (MD) | ❌ | N/A |
| **MCP Required** | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Embeddings** | ❌ | ✅ (Ollama) | ✅ (Ollama) | ❌ | ✅ | ❌ |
| **Multimodal** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Conclusion

The memory service abstraction layer provides flexibility and reliability:

- **Use `plaintext_file`** for stability and simplicity (recommended for most users)
- **Use `lancedb_langchain`** for fast vector search with Python integration (recommended for semantic search)
- **Use `basic_memory`** for semantic search + Markdown integration (experimental, requires MCP)
- **Use `lancedb_mcp`** for vector search via MCP protocol (experimental, exploring MCP)
- **Use `kuzu_graph`** only if you need advanced graph features and accept risks (Python 3.11-3.12 only)
- **Use `disabled`** for testing or privacy

Each Locrit can have its own memory service, allowing experimentation without affecting the entire system.

### Quick Recommendation Guide

**Choose Plain Text if:**
- You want the most stable option
- You don't need semantic search
- You want simple debugging
- You're new to Locrits

**Choose LanceDB LangChain if:**
- You need fast vector/semantic search
- You have large conversation datasets
- You want stable, production-ready solution
- You're comfortable running Ollama for embeddings
- You need multimodal support (text + images)

**Choose LanceDB MCP if:**
- You're exploring MCP protocol
- You want remote database capabilities
- You need standardized tool interfaces
- You're comfortable with experimental tech

**Choose Basic Memory if:**
- You want semantic search + Markdown
- You like Markdown and knowledge graphs
- You're comfortable with MCP setup
- You want to use Obsidian integration

**Choose Kuzu if:**
- You need complex relationship queries
- You're on Python 3.11 or 3.12 (not 3.13+)
- You're willing to troubleshoot crashes
- You need advanced graph database features

**Choose Disabled if:**
- You're just testing
- You need maximum privacy
- You're troubleshooting issues
