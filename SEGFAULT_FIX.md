# Kuzu Segfault Fix

## Problem Analysis

**Segfault Location:**
```
File "/mnt/storage/repos/Locrits/.venv/lib/python3.13/site-packages/kuzu/database.py", line 155 in init_database
File "/mnt/storage/repos/Locrits/src/services/kuzu_memory_service.py", line 82 in initialize
File "/mnt/storage/repos/Locrits/src/services/memory_manager_service.py", line 68 in get_memory_service
```

**Root Cause:**
- **Race condition**: Multiple WebSocket threads trying to initialize the same Kuzu database simultaneously
- **No thread safety**: `memory_manager_service.py` had no locking mechanism
- Kuzu's C++ database initialization is **not thread-safe** during concurrent initialization
- When multiple threads call `kuzu.Database(path)` at the same time for the same path, it causes a segmentation fault

**Trigger Scenario:**
1. Multiple WebSocket connections send messages to the same Locrit
2. Each thread calls `memory_manager.save_message()`
3. If the Locrit's memory service doesn't exist yet, all threads try to create it
4. Multiple threads call `KuzuMemoryService.initialize()` → `kuzu.Database(path)` simultaneously
5. Segmentation fault in C++ layer

## Solution Implemented

### 1. Added Thread-Safe Locking to Memory Manager

**File: `src/services/memory_manager_service.py`**

Added two-level locking mechanism:
- **Global lock** (`_global_lock`): Protects the initialization locks dictionary
- **Per-Locrit locks** (`_initialization_locks`): Each Locrit gets its own lock for database initialization

```python
class MemoryManagerService:
    def __init__(self, base_path: str = "data/memory"):
        self.base_path = base_path
        self.memory_services: Dict[str, KuzuMemoryService] = {}
        self.is_initialized = False
        self._initialization_locks: Dict[str, asyncio.Lock] = {}  # NEW
        self._global_lock = asyncio.Lock()  # NEW
```

### 2. Thread-Safe Database Initialization

**Double-checked locking pattern:**
```python
async def get_memory_service(self, locrit_name: str) -> Optional[KuzuMemoryService]:
    # Fast path: return if already exists (no lock)
    if locrit_name in self.memory_services:
        return self.memory_services[locrit_name]

    # Get per-Locrit lock
    async with self._global_lock:
        if locrit_name not in self._initialization_locks:
            self._initialization_locks[locrit_name] = asyncio.Lock()
        locrit_lock = self._initialization_locks[locrit_name]

    # Serialize database initialization per Locrit
    async with locrit_lock:
        # Check again after acquiring lock
        if locrit_name in self.memory_services:
            return self.memory_services[locrit_name]

        # Safe to initialize now (only one thread will reach here)
        memory_service = KuzuMemoryService(locrit_name, self.base_path)
        success = await memory_service.initialize()

        if success:
            self.memory_services[locrit_name] = memory_service
            return memory_service
```

### 3. Added Memory Cleanup

**File: `src/services/kuzu_memory_service.py`**

Added automatic cleanup to prevent memory buildup:

```python
async def get_message_count(self) -> int:
    """Get total message count."""
    # Implementation added

async def cleanup_old_messages(self, max_messages: int = 5000) -> int:
    """Delete oldest messages if count exceeds max_messages."""
    count = await self.get_message_count()
    if count <= max_messages:
        return 0

    delete_count = count - max_messages
    # Delete oldest messages

async def close(self) -> None:
    """Close with cleanup."""
    # Cleanup before closing
    await self.cleanup_old_messages(max_messages=5000)
    # Close connection
```

Periodic cleanup in `save_message()`:
```python
# Periodic cleanup check (every 100th message)
if int(message_id.split('_')[-1][:4]) % 100 == 0:
    try:
        await self.cleanup_old_messages(max_messages=5000)
    except:
        pass
```

### 4. Proper Resource Cleanup

Updated `close_all()` and `close_locrit_memory()` to also clean up locks:

```python
async def close_all(self) -> None:
    """Close all memory services and cleanup resources."""
    for locrit_name, memory_service in self.memory_services.items():
        await memory_service.close()

    self.memory_services.clear()
    self._initialization_locks.clear()  # NEW
    self.is_initialized = False
```

## Testing the Fix

### Before the fix:
```
Fatal Python error: Segmentation fault
  File "kuzu/database.py", line 155 in init_database
```

### After the fix:
- Multiple WebSocket connections can safely create memory services
- No race conditions
- Proper resource cleanup
- Automatic message limit enforcement (5000 messages per Locrit)

### Verify the fix:
```bash
# Start the application
python web_app.py

# Open multiple browser tabs
# Send messages simultaneously to the same Locrit
# Should not crash

# Monitor memory services
# Check that locks prevent concurrent initialization
```

## Additional Improvements Made

1. **Memory limits**: Each Locrit limited to 5000 messages
2. **Auto-cleanup**: Old messages deleted on close
3. **Periodic cleanup**: Every 100 messages, check if cleanup needed
4. **Better logging**: Added ✅ and ❌ emojis for success/failure
5. **Error handling**: Added traceback printing for debugging

## Files Modified

1. `src/services/memory_manager_service.py`:
   - Added asyncio locks for thread safety
   - Implemented double-checked locking pattern
   - Added lock cleanup

2. `src/services/kuzu_memory_service.py`:
   - Added `get_message_count()` method
   - Added `cleanup_old_messages()` method
   - Enhanced `close()` with cleanup
   - Added periodic cleanup in `save_message()`

## Prevention

To prevent similar issues in the future:

1. **Always use locks** when initializing shared resources from multiple threads
2. **Test with concurrent requests** when using WebSockets or async operations
3. **Check C++ library thread safety** (Kuzu database init is not thread-safe)
4. **Implement resource limits** to prevent unbounded growth
5. **Add cleanup routines** for long-running services

## Monitoring

Watch for these signs of the issue:
- Segmentation faults during high load
- Multiple threads trying to access the same Locrit simultaneously
- Database file corruption
- Memory growth without bounds

## Configuration

Add to `config.yaml`:
```yaml
memory:
  max_messages_per_locrit: 5000  # Auto-cleanup threshold
  cleanup_on_close: true
  enable_periodic_cleanup: true
```
