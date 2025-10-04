# Kuzu Memory Issues & Fixes

## Problems Identified

1. **Segfault Causes**:
   - No connection pooling - each operation creates new connections
   - Vector embeddings (768-dimensional) stored for every message without limits
   - No memory cleanup or message archival
   - Database files growing unchecked (Bob Technique: 38MB)
   - Memory leaks in `asyncio.to_thread` calls

2. **Resource Exhaustion**:
   - Unlimited message accumulation
   - Each Locrit has separate DB instance
   - No batch size limits on queries
   - Embeddings generated synchronously, blocking memory

## Immediate Fixes Needed

### 1. Add Connection Management
```python
# Add to __init__
self._connection_lock = asyncio.Lock()
self._max_connections = 5
self._connection_pool = []

async def get_connection(self):
    async with self._connection_lock:
        if not self._connection_pool:
            return kuzu.Connection(self.db)
        return self._connection_pool.pop()

async def release_connection(self, conn):
    async with self._connection_lock:
        if len(self._connection_pool) < self._max_connections:
            self._connection_pool.append(conn)
        else:
            conn.close()
```

### 2. Add Message Archival/Cleanup
```python
async def archive_old_messages(self, days_old: int = 30, keep_count: int = 1000):
    """Archive or delete messages older than X days, keeping Y most recent"""
    cutoff_date = datetime.now() - timedelta(days=days_old)

    # Get message count
    total = await self.get_message_count()

    if total > keep_count:
        # Delete oldest messages beyond keep_count
        await asyncio.to_thread(self.conn.execute, """
            MATCH (m:Message)
            WHERE m.timestamp < $cutoff_date
            WITH m ORDER BY m.timestamp ASC
            LIMIT $delete_count
            DETACH DELETE m
        """, {
            "cutoff_date": cutoff_date,
            "delete_count": total - keep_count
        })
```

### 3. Disable Embeddings for Low-Priority Messages
```python
async def save_message(self, role: str, content: str,
                      generate_embedding: bool = None, **kwargs):
    # Auto-disable embeddings for system messages or very short messages
    if generate_embedding is None:
        generate_embedding = (
            role != "system" and
            len(content) > 20 and
            self.embeddings_enabled
        )

    if generate_embedding:
        content_embedding = await self._generate_embedding(content)
    else:
        content_embedding = None
```

### 4. Add Memory Monitoring
```python
async def get_memory_usage(self) -> Dict:
    """Get current memory usage statistics"""
    import psutil
    import os

    # DB file size
    db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

    # Process memory
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info().rss

    # Message count
    message_count = await self.get_message_count()

    return {
        "db_file_size_mb": db_size / 1024 / 1024,
        "process_memory_mb": process_memory / 1024 / 1024,
        "message_count": message_count,
        "estimated_embedding_size_mb": (message_count * 768 * 4) / 1024 / 1024
    }

async def check_memory_limit(self, max_size_mb: int = 100):
    """Check if memory usage exceeds limit and cleanup if needed"""
    usage = await self.get_memory_usage()

    if usage["db_file_size_mb"] > max_size_mb:
        # Trigger cleanup
        await self.archive_old_messages(days_old=7, keep_count=500)
```

### 5. Fix Connection Leaks
```python
async def close(self) -> None:
    """Close all connections and cleanup resources"""
    try:
        # Close connection pool
        async with self._connection_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except:
                    pass
            self._connection_pool.clear()

        # Close main connection
        if self.conn:
            self.conn.close()
            self.conn = None

        # Close database
        if self.db:
            del self.db
            self.db = None

        self.is_initialized = False
    except Exception as e:
        print(f"Error closing Kuzu connection for {self.locrit_name}: {e}")
```

## Quick Fix Script

```python
# add to kuzu_memory_service.py after initialize()

async def emergency_cleanup(self):
    """Emergency cleanup to prevent crashes"""
    if not self.is_initialized:
        return

    try:
        # Get current message count
        result = await asyncio.to_thread(
            self.conn.execute,
            "MATCH (m:Message) RETURN COUNT(m)"
        )
        count = result.get_next()[0] if result.has_next() else 0

        # If more than 5000 messages, delete oldest 50%
        if count > 5000:
            delete_count = count // 2
            await asyncio.to_thread(self.conn.execute, f"""
                MATCH (m:Message)
                WITH m ORDER BY m.timestamp ASC
                LIMIT {delete_count}
                DETACH DELETE m
            """)
            print(f"Emergency cleanup: deleted {delete_count} old messages")

    except Exception as e:
        print(f"Emergency cleanup failed: {e}")
```

## Configuration Changes

Add to `config.yaml`:
```yaml
memory:
  max_db_size_mb: 100
  max_messages_per_locrit: 5000
  archive_after_days: 30
  enable_embeddings: false  # Disable to save memory
  auto_cleanup: true
  cleanup_interval_hours: 24
```

## Monitoring Commands

```bash
# Check database sizes
ls -lh data/memory/*/kuzu.db

# Monitor memory usage
watch -n 1 'ps aux | grep python | grep -v grep'

# Check for memory leaks
valgrind --leak-check=full python app.py
```
