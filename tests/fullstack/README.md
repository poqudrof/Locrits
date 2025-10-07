# Fullstack Tests

This directory contains fullstack/API integration tests that test the entire application stack including backend APIs, WebSocket connections, and storage integration.

## Requirements

- **Backend server must be running**: `python backend/web_app.py`
- **Ollama must be running** (for tests that interact with LLMs): `curl http://localhost:11434`

## Test Files

### API Tests

- **test_config_api.py** - Configuration API endpoints
  - GET /api/config
  - POST /config/test-ollama
  - POST /api/config/save
  - CORS headers validation

- **test_ollama_integration.py** - Ollama integration with frontend URL forwarding
  - POST /config/test-ollama (frontend URL forwarding)
  - POST /api/ollama/models (with custom URL)
  - GET /api/ollama/models (default config)
  - Configuration save

- **test_locrit_api.py** - Locrit HTTP Chat API
  - Basic chat functionality
  - Memory persistence
  - Multiple message exchanges

- **test_conversation_api.py** - Conversation API
  - Conversation creation and management
  - Message storage and retrieval

### Storage & Memory Tests

- **test_chat_api_storage.py** - Chat API storage validation
  - Message storage via REST API
  - Memory summary retrieval
  - Multiple message exchanges
  - Conversation history verification

- **test_websocket_chat_storage.py** - WebSocket storage validation
  - WebSocket connection and chat
  - Real-time message streaming
  - Storage validation via Memory API

- **test_api_with_memory_monitoring.py** - Comprehensive API tests with memory leak detection
  - Conversation creation and deletion
  - Message sending and retrieval
  - Memory usage monitoring
  - Memory leak detection

### Utilities

- **debug_cors.py** - CORS debugging utility
  - Preflight request testing
  - Response header validation
  - Cross-origin request debugging

## Running Tests

### Individual Test

```bash
# From project root
python tests/fullstack/test_config_api.py
```

### All Fullstack Tests (via test suite)

```bash
# Run test suite including fullstack tests
./run_tests.sh

# Run only fullstack tests (skip others)
./run_tests.sh --skip-backend --skip-frontend --skip-memory
```

### Prerequisites Check

Before running tests, ensure:

1. **Backend is running**
   ```bash
   python backend/web_app.py
   ```

2. **Ollama is running** (for LLM-based tests)
   ```bash
   # Check Ollama status
   curl http://localhost:11434

   # If not running, start it
   ollama serve
   ```

3. **Required Locrit exists** (for some tests)
   - Some tests require "Bob Technique" or other configured Locrits
   - Check `config.yaml` for available Locrits

## Test Output

Each test provides detailed output including:
- ✅ Success indicators
- ❌ Failure indicators
- ℹ️ Informational messages
- 📊 Statistics and summaries

## Debugging

If tests fail:

1. **Check backend logs** - Server console output
2. **Verify Ollama** - `curl http://localhost:11434`
3. **Check CORS** - `python tests/fullstack/debug_cors.py`
4. **Restart backend** - Fresh start often resolves issues

## Adding New Tests

When adding new fullstack tests:

1. Create test file: `test_<feature>.py`
2. Follow the pattern:
   - Import required modules
   - Define BASE_URL = "http://localhost:5000"
   - Implement test functions
   - Add main() with backend check
3. Document in this README
4. Update run_tests.sh if needed
