# Memory & Storage Tests

This directory contains tests for memory services, conversation storage, and persistence functionality.

## Test Files

### Memory Progression Tests

- **test_memory_progression.py** - Progressive information sharing test
  - Tests Locrit's ability to remember and recall information across multiple conversations
  - Creates a fictive character and progressively adds details
  - Verifies memory storage and recall capabilities
  - **Requires**: Backend server running, Ollama running, configured Locrit

- **test_memory_progression_simple.py** - Simplified memory/conversation API test
  - Tests conversation structure without requiring a running Locrit
  - Uses Faker to generate test data
  - Tests memory API endpoints
  - **Requires**: Backend server running

### Storage Tests

- **test_conversation_storage.py** - Unit test for conversation storage
  - Tests message saving (user/assistant)
  - Tests conversation history retrieval
  - Direct memory manager testing (no API)
  - **Requires**: No server needed (unit test)

- **test_locrit_root_storage.py** - Storage test for Locrit root
  - Tests storing and retrieving messages for Locrit root user
  - Verifies storage persistence
  - **Requires**: No server needed (unit test)

### WebSocket Memory Tests

- **test_websocket_memory.py** - WebSocket conversation context and memory
  - Tests WebSocket conversation functionality
  - Validates memory context in real-time chat
  - **Requires**: Backend server running, configured Locrit

## Running Tests

### Individual Tests

```bash
# Memory progression (requires full stack)
python tests/memory/test_memory_progression.py "Bob Technique"

# Simplified memory test (requires backend only)
python tests/memory/test_memory_progression_simple.py

# Unit tests (no server required)
python tests/memory/test_conversation_storage.py
python tests/memory/test_locrit_root_storage.py

# WebSocket memory test (requires backend + Locrit)
python tests/memory/test_websocket_memory.py
```

### Via Test Suite

```bash
# Run all tests including memory tests
./run_tests.sh

# Run only memory tests (skip others)
./run_tests.sh --skip-backend --skip-frontend --skip-fullstack
```

## Prerequisites

### For Unit Tests
- No server required
- Tests run directly against memory services

### For API/Integration Tests
- **Backend server**: `python backend/web_app.py`
- **Configured Locrit** in `config.yaml`

### For Full Memory Tests
- **Backend server**: `python backend/web_app.py`
- **Ollama running**: `curl http://localhost:11434`
- **Configured Locrit** with working LLM connection

## Test Descriptions

### Memory Progression Flow

1. **Initial conversation** - Introduce basic character info (name)
2. **Second conversation** - Add more traits and details
3. **Third conversation** - Add final details
4. **Memory verification** - Check stored memory directly
5. **Memory recall** - Ask Locrit to recall all character information

### Expected Results

- ✅ Character generation with all traits
- ✅ Progressive information storage across conversations
- ✅ Accurate memory recall in final conversation
- ✅ Conversation history persistence
- ✅ Session management

## Memory Services Tested

These tests validate:
- **Memory Manager Service** - Conversation storage and retrieval
- **Plaintext Memory Service** - File-based storage
- **LanceDB LangChain Service** - Vector embeddings (if available)
- **Session Management** - Conversation context tracking

## Debugging

If tests fail:

1. **Check memory service logs** - Server console output
2. **Verify data directory** - `data/memory/` should be writable
3. **Check conversation files** - `data/conversations/*.yaml`
4. **Verify Locrit config** - `config.yaml` settings
5. **Test memory API** - Direct API calls to `/api/locrits/{name}/memory/summary`

## Adding New Memory Tests

When adding new memory tests:

1. Create test file: `test_<feature>_memory.py`
2. Import required services:
   ```python
   from src.services.memory_manager_service import memory_manager
   ```
3. Test both storage and retrieval
4. Document prerequisites clearly
5. Update this README
