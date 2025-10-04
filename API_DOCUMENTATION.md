# Locrit HTTP API Documentation

## Chat API

### Send Message to Locrit

**Endpoint:** `POST /api/locrits/{locrit_name}/chat`

**Description:** Send a message to a specific Locrit and receive a response with conversation context.

**URL Parameters:**
- `locrit_name` (string): The name of the Locrit to chat with

**Request Body:**
```json
{
  "message": "Your message text here"
}
```

**Response (Success):**
```json
{
  "success": true,
  "response": "Locrit's response text",
  "locrit_name": "Locrit Name",
  "model": "ollama_model_name"
}
```

**Response (Error):**
```json
{
  "error": "Error description"
}
```

**HTTP Status Codes:**
- `200 OK` - Successful chat response
- `400 Bad Request` - Invalid message or Locrit inactive
- `404 Not Found` - Locrit not found
- `500 Internal Server Error` - Ollama service unavailable or generation error

**Example Usage:**

```bash
# Send a message to a Locrit named "Bob Technique"
curl -X POST "http://localhost:5000/api/locrits/Bob%20Technique/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, my name is Alice!"}'
```

**Example Response:**
```json
{
  "success": true,
  "response": "Hello Alice! Nice to meet you. I'm Bob Technique, a specialized AI assistant. How can I help you today?",
  "locrit_name": "Bob Technique",
  "model": "llama3.2:latest"
}
```

## Memory Features

The chat API automatically:
- **Saves user messages** to the Locrit's memory (Kuzu database)
- **Saves assistant responses** to the Locrit's memory
- **Retrieves conversation history** (last 20 messages) for context
- **Maintains conversation continuity** across multiple requests

Each conversation is identified by a session ID format: `web_{user_id}_{locrit_name}`

## Other API Endpoints

### List Locrits
- `GET /api/locrits` - Get all configured Locrits

### Locrit Management
- `POST /api/locrits/{locrit_name}/toggle` - Start/stop a Locrit
- `POST /api/locrits/{locrit_name}/delete` - Delete a Locrit

### Memory Access
- `GET /api/locrits/{locrit_name}/memory/summary` - Get memory summary
- `GET /api/locrits/{locrit_name}/memory/stats` - Get memory statistics
- `GET /api/locrits/{locrit_name}/memory/search?q={query}` - Search memory

## Notes

- All endpoints are currently accessible without authentication
- Messages are automatically saved to per-Locrit Kuzu memory databases
- Conversation context is maintained automatically
- The Locrit must be active (`"active": true`) to receive chat messages