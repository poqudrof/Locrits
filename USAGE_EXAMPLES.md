# Locrit HTTP API Usage Examples

## Quick Start

### 1. Start the Servers
```bash
# Terminal 1: Start Flask backend
cd /mnt/storage/repos/Locrits
python -c "from backend import run_app; run_app()"

# Terminal 2: Start React frontend (optional)
cd frontend
npm run dev
```

### 2. Test the API
```bash
# Run comprehensive tests
python test_locrit_api.py

# Or use the interactive chat client
python chat_client.py
```

## cURL Examples

### List Available Locrits
```bash
curl -X GET "http://localhost:5000/api/locrits"
```

### Send a Chat Message
```bash
curl -X POST "http://localhost:5000/api/locrits/Bob%20Technique/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! How are you?"}'
```

### Test Memory Persistence
```bash
# Step 1: Introduce yourself
curl -X POST "http://localhost:5000/api/locrits/Bob%20Technique/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Alice. Please remember that."}'

# Step 2: Test recall
curl -X POST "http://localhost:5000/api/locrits/Bob%20Technique/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?"}'
```

## Python Code Examples

### Simple Chat
```python
import requests

def chat_with_locrit(locrit_name, message):
    url = f"http://localhost:5000/api/locrits/{locrit_name}/chat"
    payload = {"message": message}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get('response')
    else:
        return f"Error: {response.status_code}"

# Usage
response = chat_with_locrit("Bob Technique", "Hello!")
print(response)
```

### Memory Test
```python
import requests
import time
from urllib.parse import quote

def test_memory(locrit_name, test_name):
    base_url = "http://localhost:5000"
    encoded_name = quote(locrit_name)

    # Introduce name
    intro_msg = {"message": f"My name is {test_name}. Remember this."}
    response1 = requests.post(f"{base_url}/api/locrits/{encoded_name}/chat", json=intro_msg)
    print(f"Introduction: {response1.json()['response'][:100]}...")

    # Wait briefly
    time.sleep(2)

    # Test recall
    recall_msg = {"message": "What is my name?"}
    response2 = requests.post(f"{base_url}/api/locrits/{encoded_name}/chat", json=recall_msg)
    recall_response = response2.json()['response']
    print(f"Recall: {recall_response}")

    # Check if name was remembered
    if test_name.lower() in recall_response.lower():
        print("✅ Memory test PASSED!")
    else:
        print("❌ Memory test FAILED!")

# Usage
test_memory("Bob Technique", "TestUser")
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function chatWithLocrit(locritName, message) {
    try {
        const response = await axios.post(
            `http://localhost:5000/api/locrits/${encodeURIComponent(locritName)}/chat`,
            { message: message },
            { headers: { 'Content-Type': 'application/json' } }
        );

        return response.data.response;
    } catch (error) {
        return `Error: ${error.response?.status || error.message}`;
    }
}

// Usage
(async () => {
    const response = await chatWithLocrit("Bob Technique", "Hello from JavaScript!");
    console.log(response);
})();
```

## Test Results

When you run `python test_locrit_api.py`, you should see output like:

```
🧪 Starting Locrit HTTP API Tests
==================================================
🔌 Testing API connection...
✅ API server is running

📋 Testing Locrit listing...
✅ Found 4 Locrits:
  - Bob Technique: 🟢 Active
  - Marie Recherche: 🔴 Inactive
  ...

🤖 Testing basic chat functionality...
✅ Basic chat functionality working

🧠 Testing memory persistence...
✅ Memory persistence working! Locrit remembered the name 'TestUser'

==================================================
🎉 ALL TESTS PASSED!
✅ Locrit HTTP API is working correctly
✅ Memory persistence is functioning
✅ Conversation context is maintained
```

## Available Endpoints

- `GET /api/locrits` - List all Locrits
- `POST /api/locrits/{name}/chat` - Send message to Locrit
- `POST /api/locrits/{name}/toggle` - Start/stop Locrit
- `GET /api/locrits/{name}/memory/summary` - Get memory summary
- `GET /api/locrits/{name}/memory/stats` - Get memory statistics