# Conversation API - Server-Side Context Management

The Conversation API allows you to interact with Locrits using only conversation IDs. All conversation context (message history) is managed server-side, so you don't need to forward the entire conversation history with each request.

## Key Concept

Instead of:
```
Client -> [sends message + entire conversation history] -> Server
```

You now do:
```
Client -> [sends message + conversation_id] -> Server
                                                   |
                                    Server manages context internally
```

## API Endpoints

### 1. Create a New Conversation

**Endpoint:** `POST /api/conversations/create`

**Request:**
```json
{
  "locrit_name": "Pixie l'Organisateur",
  "user_id": "user123",
  "metadata": {
    "source": "web_app",
    "device": "mobile"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "locrit_name": "Pixie l'Organisateur",
  "created_at": "2025-10-03T10:30:00.000Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Send a Message

**Endpoint:** `POST /api/conversations/{conversation_id}/message`

**Request:**
```json
{
  "message": "Bonjour! Comment vas-tu?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Bonjour! Je vais très bien, merci de demander! Comment puis-je t'aider aujourd'hui?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "locrit_name": "Pixie l'Organisateur",
  "timestamp": "2025-10-03T10:31:00.000Z",
  "message_count": 2
}
```

### 3. Get Conversation History

**Endpoint:** `GET /api/conversations/{conversation_id}?limit=50`

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "locrit_name": "Pixie l'Organisateur",
  "user_id": "user123",
  "created_at": "2025-10-03T10:30:00.000Z",
  "last_activity": "2025-10-03T10:31:00.000Z",
  "message_count": 2,
  "messages": [
    {
      "role": "user",
      "content": "Bonjour! Comment vas-tu?",
      "timestamp": "2025-10-03T10:30:30.000Z"
    },
    {
      "role": "assistant",
      "content": "Bonjour! Je vais très bien, merci de demander! Comment puis-je t'aider aujourd'hui?",
      "timestamp": "2025-10-03T10:31:00.000Z"
    }
  ]
}
```

### 4. List User Conversations

**Endpoint:** `GET /api/conversations?user_id=user123&locrit_name=Pixie`

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "locrit_name": "Pixie l'Organisateur",
      "created_at": "2025-10-03T10:30:00.000Z",
      "last_activity": "2025-10-03T10:31:00.000Z",
      "message_count": 2
    }
  ],
  "count": 1
}
```

### 5. Get Conversation Info (without messages)

**Endpoint:** `GET /api/conversations/{conversation_id}/info`

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "locrit_name": "Pixie l'Organisateur",
  "user_id": "user123",
  "created_at": "2025-10-03T10:30:00.000Z",
  "last_activity": "2025-10-03T10:31:00.000Z",
  "message_count": 2,
  "metadata": {
    "source": "web_app",
    "device": "mobile"
  }
}
```

### 6. Delete a Conversation

**Endpoint:** `DELETE /api/conversations/{conversation_id}`

**Response:**
```json
{
  "success": true,
  "message": "Conversation deleted"
}
```

## Example Usage (Python)

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. Create a conversation
response = requests.post(f"{BASE_URL}/api/conversations/create", json={
    "locrit_name": "Pixie l'Organisateur",
    "user_id": "alice"
})
data = response.json()
conversation_id = data["conversation_id"]
print(f"Created conversation: {conversation_id}")

# 2. Send messages - no need to maintain context!
response = requests.post(
    f"{BASE_URL}/api/conversations/{conversation_id}/message",
    json={"message": "Bonjour!"}
)
print(f"Locrit: {response.json()['response']}")

# 3. Send another message - context is maintained server-side
response = requests.post(
    f"{BASE_URL}/api/conversations/{conversation_id}/message",
    json={"message": "Peux-tu me rappeler de quoi on parlait?"}
)
print(f"Locrit: {response.json()['response']}")

# 4. Get conversation history
response = requests.get(f"{BASE_URL}/api/conversations/{conversation_id}")
history = response.json()
print(f"Total messages: {history['message_count']}")

# 5. List all conversations
response = requests.get(f"{BASE_URL}/api/conversations", params={"user_id": "alice"})
conversations = response.json()['conversations']
print(f"Alice has {len(conversations)} conversation(s)")
```

## Example Usage (JavaScript/TypeScript)

```typescript
const BASE_URL = "http://localhost:5000";

// 1. Create a conversation
const createResponse = await fetch(`${BASE_URL}/api/conversations/create`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    locrit_name: "Pixie l'Organisateur",
    user_id: "alice"
  })
});
const { conversation_id } = await createResponse.json();
console.log(`Created conversation: ${conversation_id}`);

// 2. Send a message
const sendMessage = async (message: string) => {
  const response = await fetch(
    `${BASE_URL}/api/conversations/${conversation_id}/message`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    }
  );
  const data = await response.json();
  return data.response;
};

// 3. Chat - context is maintained automatically
const response1 = await sendMessage("Bonjour!");
console.log(`Locrit: ${response1}`);

const response2 = await sendMessage("Peux-tu me rappeler de quoi on parlait?");
console.log(`Locrit: ${response2}`);

// 4. Get conversation history
const historyResponse = await fetch(
  `${BASE_URL}/api/conversations/${conversation_id}`
);
const history = await historyResponse.json();
console.log(`Total messages: ${history.message_count}`);
```

## Example Usage (cURL)

```bash
# 1. Create a conversation
CONV_ID=$(curl -X POST http://localhost:5000/api/conversations/create \
  -H "Content-Type: application/json" \
  -d '{"locrit_name":"Pixie l'\''Organisateur","user_id":"alice"}' \
  | jq -r '.conversation_id')

echo "Conversation ID: $CONV_ID"

# 2. Send a message
curl -X POST "http://localhost:5000/api/conversations/$CONV_ID/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"Bonjour!"}'

# 3. Send another message
curl -X POST "http://localhost:5000/api/conversations/$CONV_ID/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"Comment vas-tu?"}'

# 4. Get conversation history
curl "http://localhost:5000/api/conversations/$CONV_ID"

# 5. List conversations
curl "http://localhost:5000/api/conversations?user_id=alice"

# 6. Delete conversation
curl -X DELETE "http://localhost:5000/api/conversations/$CONV_ID"
```

## Benefits

1. **Simplified Client Code**: No need to manage conversation history on the client
2. **Reduced Bandwidth**: Only send the new message, not the entire conversation
3. **Centralized Context**: Server maintains the conversation state
4. **Multi-Device Support**: Access the same conversation from different devices
5. **Scalability**: Easy to implement caching and optimization on the server

## Migration from Old API

**Old way (manual context management):**
```javascript
// Client maintains messages array
const messages = [...previousMessages, newMessage];
const response = await fetch('/api/locrits/Pixie/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: newMessage,
    context: messages  // Send entire history
  })
});
```

**New way (server-side context):**
```javascript
// Server maintains context
const response = await fetch(`/api/conversations/${conversationId}/message`, {
  method: 'POST',
  body: JSON.stringify({
    message: newMessage  // Only send new message
  })
});
```

## Notes

- Conversation IDs are persistent and can be stored in client-side storage
- The server uses the conversation_id as the session_id for memory storage
- Conversations are kept in memory; for production, consider implementing persistence
- Message history is automatically retrieved from the Locrit's memory service
