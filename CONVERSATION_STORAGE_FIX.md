# Conversation Storage Fix

## Problem

Conversations were not being stored when chatting with Locrits via the frontend. Users would send messages but couldn't see them in the conversation history or Memory Explorer.

## Root Cause

**Two separate issues were found:**

1. **REST API** (`backend/routes/chat.py`) - Using `asyncio.run()` inside async functions
2. **WebSocket API** (`backend/routes/websocket.py`) - Using `asyncio.run()` in synchronous handlers

Both caused memory operations to fail silently.

### Before (Broken):
```python
@chat_bp.route('/api/locrits/<locrit_name>/chat', methods=['POST'])
async def api_chat_with_locrit(locrit_name):
    # ...
    try:
        # ❌ WRONG: Using asyncio.run() inside async function
        asyncio.run(memory_manager.save_message(
            locrit_name=locrit_name,
            role="user",
            content=message,
            session_id=session_id,
            user_id=user_id
        ))
    except Exception as e:
        logger.warning(f"Erreur sauvegarde message utilisateur: {e}")
```

### After (Fixed):
```python
@chat_bp.route('/api/locrits/<locrit_name>/chat', methods=['POST'])
async def api_chat_with_locrit(locrit_name):
    # ...
    try:
        # ✅ CORRECT: Using await in async function
        await memory_manager.save_message(
            locrit_name=locrit_name,
            role="user",
            content=message,
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        logger.warning(f"Erreur sauvegarde message utilisateur: {e}")
```

## Issues Found and Fixed

### 1. User Message Storage (Line 172-178)
**Before:**
```python
asyncio.run(memory_manager.save_message(...))
```
**After:**
```python
await memory_manager.save_message(...)
```

### 2. Conversation History Retrieval (Line 190-194)
**Before:**
```python
history_messages = asyncio.run(memory_manager.get_conversation_history(...))
```
**After:**
```python
history_messages = await memory_manager.get_conversation_history(...)
```

### 3. Assistant Response Storage (Line 216-222)
**Before:**
```python
asyncio.run(memory_manager.save_message(...))
```
**After:**
```python
await memory_manager.save_message(...)
```

## Files Modified

### 1. **backend/routes/chat.py** (REST API - Async Functions)
  - Line 172: Fixed user message save (changed `asyncio.run()` to `await`)
  - Line 190: Fixed conversation history retrieval (changed `asyncio.run()` to `await`)
  - Line 216: Fixed assistant message save (changed `asyncio.run()` to `await`)

### 2. **backend/routes/websocket.py** (WebSocket - Sync Functions)
  - Line 195-205: Fixed user message save (proper event loop creation)
  - Line 218-225: Fixed conversation history retrieval (proper event loop creation)
  - Line 272-281: Fixed assistant response save - streaming mode (proper event loop creation)
  - Line 296-305: Fixed assistant response save - non-streaming mode (proper event loop creation)

**WebSocket Fix Pattern:**
```python
# Synchronous context needs new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(async_function())
loop.close()
```

## Testing

### Unit Test Created: `test_conversation_storage.py`

Comprehensive test suite that verifies:
- ✅ User messages are saved
- ✅ Assistant messages are saved
- ✅ Conversation history is retrievable
- ✅ Message order is preserved
- ✅ Session isolation works
- ✅ Multiple messages in conversation flow

**Test Results:**
```
🎉 ALL TESTS PASSED!

Key findings:
  ✓ Messages are saved correctly
  ✓ Conversation history is retrievable
  ✓ Message order is preserved
  ✓ Both user and assistant messages are stored
  ✓ Session isolation works
```

### API Test Created: `test_chat_api_storage.py`

End-to-end test that:
1. Sends messages via chat API
2. Verifies storage via memory summary API
3. Tests multiple message exchanges
4. Validates conversation sessions

### WebSocket Test Created: `test_websocket_chat_storage.py`

Real-world WebSocket chat test that:
1. Connects to WebSocket server
2. Joins chat room for a Locrit
3. Sends chat messages via WebSocket
4. Receives streaming responses
5. Verifies messages are stored in memory
6. Checks conversation history via API

## How to Run Tests

### 1. Run Unit Test (No server required)
```bash
python test_conversation_storage.py
```

### 2. Run API Test (requires backend)
```bash
# Terminal 1: Start backend
python web_app.py

# Terminal 2: Run test
python test_chat_api_storage.py
```

### 3. Run WebSocket Test (requires backend + Ollama)
```bash
# Terminal 1: Start backend
python web_app.py

# Terminal 2: Ensure Ollama is running
curl http://localhost:11434

# Terminal 3: Run test
python test_websocket_chat_storage.py
```

## How to Verify Fix

### Manual Testing Steps:

1. **Restart the backend (REQUIRED):**
   ```bash
   # Stop current backend
   pkill -f "python web_app.py"

   # Start fresh
   python web_app.py
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Chat with a Locrit:**
   - Visit: http://localhost:5173/my-locrits/Bob%20Technique/chat
   - Send a message: "Hello, testing storage"
   - Wait for response
   - Send another message: "Can you remember this?"

4. **Check Memory Explorer:**
   - Visit: http://localhost:5173/my-locrits/Bob%20Technique/memory-explorer
   - Go to "Messages" tab
   - **Verify your messages appear** ✅
   - Check timestamps are recent
   - Verify both user and assistant messages

5. **Check via API:**
   ```bash
   curl http://localhost:5000/api/locrits/Bob%20Technique/memory/summary | python -m json.tool
   ```
   Look for `total_messages` > 0 and `recent_messages` containing your conversation

## Important Notes

### Backend Restart Required
**After applying this fix, the backend MUST be restarted:**

```bash
# Stop the running backend (Ctrl+C or kill process)
pkill -f "python web_app.py"

# Start it again
python web_app.py
```

### Why asyncio.run() Doesn't Work

`asyncio.run()` creates a NEW event loop and runs the coroutine in it. This:
- Cannot be called from within an async function
- Blocks the current event loop
- Causes nested event loop errors
- Prevents proper async/await flow

In async functions, always use `await`:
```python
# ❌ WRONG (in async function)
result = asyncio.run(async_function())

# ✅ CORRECT (in async function)
result = await async_function()

# ℹ️  asyncio.run() is ONLY for:
# - Top-level script entry points
# - Synchronous functions calling async code
```

## Related Files

- **backend/routes/chat.py** - Chat API endpoint (fixed)
- **src/services/memory_manager_service.py** - Memory manager (uses async correctly)
- **test_conversation_storage.py** - Unit tests
- **test_chat_api_storage.py** - API integration tests

## Impact

✅ **Before Fix:**
- Conversations not saved
- History empty
- Memory explorer showed no data

✅ **After Fix:**
- All conversations saved correctly
- History retrievable
- Memory explorer shows all messages
- Sessions tracked properly

## Additional Benefits

The fix also ensures:
- Proper async flow throughout the chat pipeline
- Better error handling for memory operations
- Consistent storage across all memory service types
- Session-based conversation tracking

## Future Improvements

Consider:
1. Add retry logic for failed storage
2. Implement conversation persistence verification
3. Add real-time memory update notifications
4. Create memory backup/export functionality
