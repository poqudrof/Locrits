# Locrit Memory System File Structure

This document describes the file structure for each memory service implementation in the Locrit system.

## Overview

Locrits supports multiple memory backend systems, each with its own file organization. All memory data is stored under `data/memory/` with per-Locrit isolation.

**Base Path:** `data/memory/{locrit_name}/`

Each Locrit can be configured to use one of the following memory services:
- **Kuzu Graph Database** (`kuzu_graph`) - Graph-based memory with relationships
- **Simple File** (`simple_file`) - JSON-based file storage (deprecated, stable)
- **Plain Text File** (`plaintext_file`) - Text files with JSON index
- **Basic Memory** (`basic_memory`) - Markdown-based via MCP
- **LanceDB LangChain** (`lancedb_langchain`) - Vector database with Python
- **LanceDB MCP** (`lancedb_mcp`) - Vector database via MCP protocol
- **Disabled** (`disabled`) - No memory persistence

---

## 1. Kuzu Graph Database (`kuzu_graph`)

**Type:** Graph database with vector embeddings
**Status:** Experimental (compatibility issues with Python 3.13+)
**Best For:** Complex relationships, semantic search, advanced queries

### Directory Structure

```
data/memory/{locrit_name}/
├── kuzu.db/                    # Main Kuzu database directory
│   ├── catalog/                # Database catalog metadata
│   ├── wal/                    # Write-ahead log for transactions
│   └── storage/                # Actual data storage
├── kuzu.db.wal                 # Write-ahead log file
└── .lock                       # Database lock file (temporary)
```

### Schema Structure (Logical)

**Node Tables:**
- `User` - User information
- `Message` - Conversation messages with embeddings
- `Session` - Conversation sessions
- `Concept` - Extracted concepts with embeddings
- `Topic` - Conversation topics
- `Memory` - Standalone memory entries with embeddings

**Relationship Tables:**
- `SENT` - User → Message (who sent)
- `RESPONDS_TO` - Message → Message (conversation flow)
- `PART_OF` - Message → Session (session membership)
- `MENTIONS` - Message → Concept (concept extraction)
- `DISCUSSES` - Session → Topic (topic classification)
- `LEARNS` - Session → Memory (memory creation)
- `RELATES_TO` - Concept → Concept (concept relationships)

### Vector Indices

```
{locrit_name}_message_embeddings    # Message content vectors
{locrit_name}_memory_embeddings     # Memory content vectors
{locrit_name}_concept_embeddings    # Concept name vectors
```

**Embedding Model:** `nomic-embed-text` or custom via Ollama
**Dimensions:** 768 (configurable 64-768)

### Example Files

```bash
data/memory/bob_technique/
├── kuzu.db/                    # ~1-50MB depending on conversation volume
├── kuzu.db.wal                 # Transaction log
└── kuzu.db.backup_20251005/   # Auto-created on corruption recovery
```

---

## 2. Simple File Memory (`simple_file`)

**Type:** JSON-based file storage
**Status:** Stable (deprecated, legacy compatibility)
**Best For:** Debugging, simple deployments, human-readable data

### Directory Structure

```
data/memory/{locrit_name}/simple_file/
├── index.json                  # Main index with statistics
├── messages/                   # Individual message files
│   ├── {uuid-1}.json
│   ├── {uuid-2}.json
│   └── ...
└── sessions/                   # Session index files
    ├── session_{id}.json
    └── ...
```

### File Formats

#### `index.json`
```json
{
  "total_messages": 42,
  "total_sessions": 5,
  "created_at": "2025-10-05T12:34:56.789"
}
```

#### `messages/{message_id}.json`
```json
{
  "id": "81ffea30-01cd-4d35-bc5f-37c0faf89148",
  "role": "user",
  "content": "Hello, how are you?",
  "session_id": "session_1759694139167",
  "user_id": "default",
  "timestamp": "2025-10-05T12:35:00.123",
  "metadata": {}
}
```

#### `sessions/{session_id}.json`
```json
{
  "id": "session_1759694139167",
  "message_ids": [
    "81ffea30-01cd-4d35-bc5f-37c0faf89148",
    "e82a78be-b88b-444d-9c9f-840cccc30530"
  ],
  "created_at": "2025-10-05T12:35:00.000",
  "updated_at": "2025-10-05T12:37:15.456"
}
```

### Example

```bash
data/memory/locrit_root/simple_file/
├── index.json                          # 150 bytes
├── messages/
│   ├── d7fd07dc-fa1e-4b23-87c6.json   # ~500 bytes each
│   ├── fbd0f886-3424-4cfb-8373.json
│   └── ... (12 messages)
└── sessions/
    ├── session_1759860212556.json      # ~200 bytes
    └── test_session_123.json
```

---

## 3. Plain Text File Memory (`plaintext_file`)

**Type:** Text files with JSON metadata
**Status:** Stable, recommended for simple use cases
**Best For:** Human-readable storage, easy debugging, no external dependencies

### Directory Structure

```
data/memory/{locrit_name}/plaintext/
├── index.json                  # Searchable index
└── memories/                   # Individual memory files
    ├── {memory_id}.txt
    ├── {memory_id}.txt
    └── ...
```

### File Formats

#### `index.json`
```json
{
  "memory-uuid-1": {
    "file": "memories/memory-uuid-1.txt",
    "created_at": "2025-10-05T12:00:00",
    "importance": 0.8,
    "tags": ["conversation", "important"],
    "content_preview": "First 200 characters of content..."
  },
  "memory-uuid-2": { ... }
}
```

#### `memories/{memory_id}.txt`
```
=== MEMORY METADATA ===
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-05T12:00:00",
  "last_accessed": "2025-10-05T14:30:00",
  "importance": 0.8,
  "memory_type": "conversation",
  "tags": ["user-preference", "context"],
  "metadata": {
    "source": "chat",
    "user_id": "alice"
  }
}
=== CONTENT ===
User prefers detailed technical explanations with code examples.
Interested in Python, AI, and graph databases.
```

### Example

```bash
data/memory/testbot/plaintext/
├── index.json                      # In-memory search index
└── memories/
    ├── abc123.txt                 # ~1KB each
    ├── def456.txt
    └── ...
```

---

## 4. Basic Memory (`basic_memory`)

**Type:** Markdown-based knowledge graph via MCP
**Status:** Experimental
**Best For:** Rich semantic markup, Obsidian integration, bidirectional links

### Directory Structure

```
data/memory/{locrit_name}/basic-memory/
├── entities/                   # Entity notes
│   └── {entity_name}.md
├── relations/                  # Relationship definitions
│   └── {relation_id}.md
└── observations/               # Observations and facts
    └── {observation_id}.md
```

### File Format (Markdown with Frontmatter)

#### `entities/{entity_name}.md`
```markdown
---
id: entity-12345
type: Person
created_at: 2025-10-05T12:00:00
tags: [user, important]
---

# Alice

## Attributes
- Role: User
- Preferences: Technical discussions

## Related
- [[Python Programming]]
- [[AI Research]]

## Observations
- Prefers detailed code examples
- Active during evening hours
```

#### `observations/{observation_id}.md`
```markdown
---
id: obs-67890
entity: Alice
created_at: 2025-10-05T12:30:00
importance: 0.9
---

# Alice's Programming Preference

User Alice mentioned preferring Python over JavaScript for data analysis tasks.

**Context:** Discussion about data processing tools
**Source:** Chat session 2025-10-05
```

### Integration

- **MCP Server:** `uvx basic-memory`
- **Environment:** `BASIC_MEMORY_PATH=data/memory/{locrit_name}/basic-memory`
- **Obsidian Vault:** Can be opened directly in Obsidian for visualization

---

## 5. LanceDB LangChain (`lancedb_langchain`)

**Type:** Vector database with Python integration
**Status:** Stable
**Best For:** Fast vector search, persistent storage, multimodal support

### Directory Structure

```
data/memory/{locrit_name}/lancedb_langchain/
├── {locrit_name}_memories.lance/    # LanceDB table directory
│   ├── data/                        # Vector data files
│   │   ├── chunk_0.lance
│   │   ├── chunk_1.lance
│   │   └── ...
│   ├── _versions/                   # Version history
│   │   ├── 1.manifest
│   │   ├── 2.manifest
│   │   └── ...
│   └── _indices/                    # Vector indices
│       └── {index_name}/
└── metadata.json                    # Table metadata
```

### Storage Format

**Database Format:** Apache Arrow + Lance
**Vector Index:** IVF-PQ or HNSW (configurable)
**Embedding Model:** `nomic-embed-text` via Ollama

### Data Structure

Each memory is stored as a LangChain Document:
```python
Document(
    page_content="Memory content here...",
    metadata={
        "id": "uuid",
        "memory_type": "conversation",
        "importance": 0.8,
        "created_at": "2025-10-05T12:00:00",
        "tags": ["tag1", "tag2"],
        "custom_field": "value"
    }
)
```

### Example

```bash
data/memory/locrit_root/lancedb_langchain/
└── locrit_root_memories.lance/
    ├── data/
    │   ├── chunk_0.lance           # ~1-10MB per chunk
    │   └── chunk_1.lance
    ├── _versions/
    │   ├── 1.manifest              # ~1KB each
    │   └── 2.manifest
    └── _indices/
        └── vector_index/
```

---

## 6. LanceDB MCP (`lancedb_mcp`)

**Type:** Vector database via MCP protocol
**Status:** Experimental
**Best For:** Remote-capable deployments, standardized protocol access

### Directory Structure

```
data/memory/{locrit_name}/lancedb_mcp/
└── {table_name}.lance/         # Same structure as LangChain variant
    ├── data/
    ├── _versions/
    └── _indices/
```

### Protocol

- **MCP Server:** Custom LanceDB MCP implementation
- **Communication:** JSON-RPC over stdio
- **Tools Exposed:**
  - `create_memory`
  - `search_memories`
  - `retrieve_memory`
  - `delete_memory`

### Differences from LangChain Variant

- Accessed via MCP protocol instead of direct Python
- Same underlying LanceDB storage format
- Supports remote/distributed deployments
- Additional overhead from MCP layer

---

## 7. Disabled Memory (`disabled`)

**Type:** No persistence
**Status:** Stable
**Best For:** Testing, stateless bots, performance testing

### Directory Structure

```
(No files created - memory is not persisted)
```

All operations return empty results or success without side effects.

---

## Memory Service Comparison

| Service | File Size/Message | Search Speed | Setup Complexity | Best Use Case |
|---------|------------------|--------------|------------------|---------------|
| Kuzu Graph | ~2KB + overhead | Fast (indexed) | High | Complex queries, relationships |
| Simple File | ~500 bytes | Slow (linear) | Low | Debugging, simple bots |
| Plaintext | ~1KB | Medium (indexed) | Low | Human-readable, stable |
| Basic Memory | ~2KB | Medium | Medium | Knowledge graphs, Obsidian |
| LanceDB LC | ~1KB + vectors | Very Fast | Medium | Semantic search, production |
| LanceDB MCP | ~1KB + vectors | Very Fast | High | Distributed systems |
| Disabled | 0 bytes | N/A | None | Testing, stateless |

---

## Configuration Example

In `config.yaml`:

```yaml
locrits:
  my_bot:
    active: true
    memory_service: "plaintext_file"  # Choose from above
    access_to:
      quick_memory: true
      full_memory: true
      logs: true
```

Available options:
- `kuzu_graph`
- `plaintext_file`
- `basic_memory`
- `lancedb_langchain`
- `lancedb_mcp`
- `disabled`

---

## Migration Between Services

Memory services are **not directly compatible**. To migrate:

1. **Export from old service:**
   ```bash
   GET /api/locrits/{name}/memory/summary
   ```

2. **Save conversation history**

3. **Change config:**
   ```yaml
   memory_service: "new_service_type"
   ```

4. **Restart application** - new service will initialize empty

5. **Optional:** Manually import critical memories via API

---

## Backup and Recovery

### Kuzu Graph
```bash
# Backup
cp -r data/memory/{locrit}/kuzu.db data/backups/

# Restore
cp -r data/backups/kuzu.db data/memory/{locrit}/
```

### Simple File / Plaintext
```bash
# Backup
tar -czf backup.tar.gz data/memory/{locrit}/

# Restore
tar -xzf backup.tar.gz -C data/memory/
```

### LanceDB
```bash
# Backup (includes versions)
cp -r data/memory/{locrit}/lancedb_* data/backups/

# Restore specific version
# Use LanceDB version control features
```

### Basic Memory
```bash
# Backup (Markdown files)
cp -r data/memory/{locrit}/basic-memory data/backups/

# Can also sync with git for version control
cd data/memory/{locrit}/basic-memory
git init && git add . && git commit -m "backup"
```

---

## Troubleshooting

### Kuzu Issues
- **Segfault:** Delete `kuzu.db`, will auto-recreate
- **Corruption:** System creates `.backup_*` automatically
- **Python 3.13+:** Use `plaintext_file` instead

### File Permission Issues
```bash
# Fix permissions
chmod -R 755 data/memory/
chown -R $USER data/memory/
```

### Disk Space
```bash
# Check memory usage
du -sh data/memory/*

# Clean up old backups
find data/memory -name "*.backup_*" -mtime +7 -delete
```

### Index Corruption
```bash
# Plaintext - rebuild index
rm data/memory/{locrit}/plaintext/index.json
# Restart app - will rebuild automatically

# LanceDB - reindex
# Use LanceDB compact() operation
```

---

## Performance Characteristics

### Storage Growth

| Service | Growth Rate | Cleanup Strategy |
|---------|-------------|------------------|
| Kuzu | ~2KB/msg | Auto-cleanup at 5000 msgs |
| Simple File | ~500B/msg | Manual deletion only |
| Plaintext | ~1KB/msg | Manual deletion only |
| Basic Memory | ~2KB/memory | Git-based versioning |
| LanceDB | ~1KB/msg + vectors | Version pruning |

### Query Performance (1000 messages)

| Service | Exact Match | Semantic Search | Full Scan |
|---------|------------|-----------------|-----------|
| Kuzu | <10ms | 50-100ms | 100ms |
| Simple File | 50-200ms | N/A | 200-500ms |
| Plaintext | 10-50ms | N/A | 100-200ms |
| Basic Memory | 20-100ms | 100-200ms | N/A |
| LanceDB | <5ms | 20-50ms | N/A |

---

## Security Considerations

### Data Isolation
- Each Locrit has **separate directory** - no cross-contamination
- Sanitized names prevent directory traversal

### Sensitive Data
- No encryption at rest (all formats store plaintext)
- Use system-level encryption (dm-crypt, LUKS) if needed
- Consider `disabled` memory for sensitive conversations

### Access Control
- File permissions control read/write access
- No built-in user authentication
- Rely on OS-level security

---

## Development Notes

### Adding a New Memory Service

1. Create adapter in `src/services/memory/`
2. Implement `BaseMemoryService` interface
3. Register in `memory_factory.py`
4. Add to `MemoryServiceType` enum
5. Document file structure here

### Testing
```bash
# Test specific service
pytest tests/memory/test_{service_name}_service.py

# Test all services
pytest tests/memory/
```

---

## Related Documentation

- [MEMORY.md](MEMORY.md) - Memory system architecture
- [config.yaml](config.yaml) - Configuration reference
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - API examples
