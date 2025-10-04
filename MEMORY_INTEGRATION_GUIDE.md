# Locrits Modular Memory System Integration Guide

## Overview

The new modular memory system provides sophisticated memory management for Locrits, separating **graph-based** (precise) memories from **vector-based** (fuzzy) memories. This allows LLMs to make intelligent decisions about how to store and retrieve different types of information.

## Architecture

```
src/services/memory/
├── __init__.py                  # Main package interface
├── interfaces.py               # Abstract base classes and types
├── config.py                   # Configuration management
├── graph_memory_service.py     # Structured memory (facts, events, relationships)
├── vector_memory_service.py    # Semantic memory (experiences, impressions, themes)
├── memory_manager.py           # Main orchestrator
├── memory_tools.py             # LLM-accessible tools
└── example_usage.py            # Usage examples
```

## Memory Types

### Graph Memory (Precise)
- **Facts**: "Paris is the capital of France"
- **Events**: "User scheduled meeting for 3 PM"
- **Relationships**: Connections between concepts
- **Structured data**: Anything with clear relationships

### Vector Memory (Fuzzy)
- **Souvenirs**: "The sunset was breathtaking"
- **Impressions**: "User seems interested in travel"
- **Themes**: "Machine learning concepts"
- **Experiences**: Emotional or sensory content

## Integration Steps

### 1. Install Dependencies

Add to your requirements.txt:
```
nomic>=1.0.0  # For vector embeddings
kuzu>=0.11.0  # For graph database
pyyaml>=6.0   # For configuration
```

### 2. Configuration

Create `config/memory.yaml`:
```yaml
memory:
  base_path: "data/memory"
  vector:
    enabled: true
    model: "nomic-embed-text-v1.5"
    dimension: 384
  graph:
    enabled: true
    max_concepts_per_message: 5
  updates:
    auto_update: true
    update_interval: 10  # messages
```

### 3. Initialize Memory System

```python
from src.services.memory import create_memory_system

# In your Locrit initialization
async def initialize_locrit(locrit_name: str):
    # Create memory system
    memory_manager, memory_tools = await create_memory_system(
        locrit_name=locrit_name,
        config_path="config/memory.yaml"
    )

    return memory_manager, memory_tools
```

### 4. Integration with Chat Loop

```python
async def process_conversation(messages: List[Dict], memory_tools: Dict):
    # Let LLM decide what to remember
    for message in messages:
        if should_store_memory(message):
            # Analyze content
            analysis = await memory_tools["analyze_memory_decision"](
                content=message["content"],
                context={"role": message["role"], "timestamp": message["timestamp"]}
            )

            # Store based on LLM decision
            if analysis["recommendation"]["memory_type"] == "graph":
                await memory_tools["store_graph_memory"](
                    content=message["content"],
                    importance=analysis["recommendation"]["importance"],
                    metadata={"source": "conversation"}
                )
            else:
                await memory_tools["store_vector_memory"](
                    content=message["content"],
                    importance=analysis["recommendation"]["importance"],
                    tags=analysis["recommendation"]["tags"]
                )

    # Check if memory update is needed
    await memory_tools["update_memory_now"]()
```

### 5. LLM Tool Integration

Add memory tools to your LLM's available functions:

```python
# Available tools for the LLM
MEMORY_TOOLS = [
    {
        "name": "store_graph_memory",
        "description": "Store precise facts, events, or structured information",
        "parameters": {
            "content": "Content to store",
            "memory_type": "Type: fact, event, concept, message",
            "importance": "Importance score 0-1",
            "relationships": "Optional relationships to create"
        }
    },
    {
        "name": "store_vector_memory",
        "description": "Store experiences, impressions, or fuzzy information",
        "parameters": {
            "content": "Content to store",
            "vector_type": "Type: souvenir, impression, theme",
            "importance": "Importance score 0-1",
            "emotional_tone": "Emotional context"
        }
    },
    {
        "name": "search_all_memory",
        "description": "Search across all memory types",
        "parameters": {
            "query": "Search query",
            "limit": "Max results",
            "strategy": "Search strategy: auto, graph_first, vector_first"
        }
    },
    {
        "name": "get_memory_status",
        "description": "Check memory system status and get recommendations"
    },
    {
        "name": "update_memory_now",
        "description": "Force immediate memory processing"
    }
]
```

## LLM Decision Framework

The LLM should decide memory storage based on content characteristics:

### Use Graph Memory For:
- **Facts and data**: Names, dates, numbers, addresses
- **Events**: Scheduled meetings, completed tasks
- **Relationships**: "X is related to Y", "A causes B"
- **Structured information**: Lists, procedures, steps

### Use Vector Memory For:
- **Experiences**: "I felt...", "It seemed...", "The atmosphere was..."
- **Opinions**: "I think...", "My impression is..."
- **Themes**: Abstract concepts, patterns
- **Emotional content**: Feelings, reactions, subjective experiences

### Use Hybrid Storage For:
- **Important information** that benefits from both precise and fuzzy retrieval
- **Complex content** with both factual and experiential aspects

## Memory Update Scheduling

The system automatically manages memory updates:

1. **Message-based**: Updates after N messages (configurable)
2. **Time-based**: Updates after specified time intervals
3. **User-triggered**: Manual updates via button/command
4. **Session-based**: Updates when conversation sessions end

## Example LLM Prompts

```
You have access to a sophisticated memory system with two types of storage:

1. **Graph Memory**: For precise facts, events, and structured information
   - Use store_graph_memory() for facts like "Paris is the capital of France"
   - Good for data that needs exact retrieval

2. **Vector Memory**: For experiences, impressions, and fuzzy content
   - Use store_vector_memory() for experiences like "The user seemed excited about travel"
   - Good for thematic and emotional content

When deciding what to remember:
- Consider: Is this a fact or an experience?
- Consider: Will I need exact retrieval or similarity-based retrieval?
- Consider: How important is this information?

You can search memories with search_all_memory() and check system status with get_memory_status().
```

## Migration from Legacy System

If you have an existing KuzuMemoryService:

1. **Create configuration**: Use the new YAML-based config
2. **Initialize new system**: Replace old service with MemoryManager
3. **Update tool calls**: Replace old methods with new memory tools
4. **Data migration**: The new system can coexist with old data

```python
# Old way
memory_service = KuzuMemoryService(locrit_name)
await memory_service.save_message(role, content, session_id)

# New way
memory_manager, memory_tools = await create_memory_system(locrit_name)
await memory_tools["store_graph_memory"](content, memory_type="message")
```

## Monitoring and Maintenance

### Status Monitoring
```python
status = await memory_tools["get_memory_status"]()
print(f"Total memories: {status['status']['statistics']['total_memories_stored']}")
print(f"Recommendations: {status['recommendations']}")
```

### Cleanup Management
```python
# Clean up old memories
cleanup_result = await memory_tools["cleanup_old_memories"](retention_days=30)
print(f"Cleaned up {cleanup_result['cleanup_results']['total_cleaned']} memories")
```

### Configuration Validation
```python
from src.services.memory import validate_config

issues = validate_config("config/memory.yaml")
if issues:
    print(f"Config issues: {issues}")
```

## Performance Considerations

- **Batch updates**: System processes memories in batches for efficiency
- **Vector indexing**: Automatic creation of similarity search indices
- **Cleanup policies**: Configurable retention and cleanup schedules
- **Service isolation**: Graph and vector services can be enabled/disabled independently

## Troubleshooting

### Common Issues

1. **"Vector embeddings disabled"**
   - Install: `pip install nomic`
   - Check configuration: `vector.enabled: true`

2. **"Graph memory service not available"**
   - Install: `pip install kuzu`
   - Check configuration: `graph.enabled: true`

3. **"Memory not updating"**
   - Check update interval in config
   - Use `update_memory_now(force=True)`

4. **Performance issues**
   - Reduce embedding dimension
   - Increase cleanup frequency
   - Enable batch processing

## Best Practices

1. **Let the LLM decide**: Use `analyze_memory_decision()` to get AI recommendations
2. **Use appropriate storage**: Facts in graph, experiences in vector
3. **Set importance levels**: Higher importance = longer retention
4. **Monitor regularly**: Check status and recommendations
5. **Configure retention**: Set appropriate cleanup policies
6. **Test thoroughly**: Use the example usage scripts

This modular system gives your Locrits sophisticated memory management with LLM agency over storage decisions, enabling more intelligent and contextual memory retrieval.