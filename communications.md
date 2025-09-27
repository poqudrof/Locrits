# Locrits Communication and Configuration

This document outlines the communication flow between the frontend, backend, and the Ollama service, as well as how Locrit configurations are managed.

## Communication Flow: Frontend - Backend - Ollama

The real-time chat functionality is built on a WebSocket connection managed by Flask-SocketIO on the backend and socket.io-client on the frontend.

### Text-Based Flow

```
1. User -> Frontend (React)
   - Action: Enters and sends a message in the UI.

2. Frontend (React) -> Backend (Flask)
   - Via: WebSocket
   - Event: `chat_message`
   - Payload: { locrit_name, message, stream: true }

3. Backend (Flask) -> Ollama
   - Action: The `on_chat_message` handler retrieves the Locrit's configuration and sends a streaming chat request to the Ollama service.

4. Ollama -> Backend (Flask)
   - Via: HTTP Stream
   - Action: Streams the response back in chunks.

5. Backend (Flask) -> Frontend (React)
   - Via: WebSocket
   - Event (repeatedly): `chat_chunk` for each piece of the response.
   - Event (at the end): `chat_complete` to signal the end of the stream.

6. Frontend (React) -> User
   - Action: Renders the incoming `chat_chunk` content in real-time, creating a typing effect.
   - Action: Hides the typing indicator upon receiving the `chat_complete` event.
```

### Detailed Steps

1.  **User Sends Message:** The user types a message in the chat interface in `frontend/src/pages/Chat.tsx` and clicks send.
2.  **Frontend Emits Event:** The `handleSendMessage` function is triggered. Instead of making an HTTP request, it emits a `chat_message` event over the established WebSocket connection. This event includes the target `locrit_name`, the `message` content, and a `stream: true` flag.
3.  **Backend Receives Event:** The `on_chat_message` handler in the `ChatNamespace` class (`backend/routes/websocket.py`) receives the event.
4.  **Configuration and Validation:** The backend retrieves the settings for the specified Locrit from `config.yaml` to get its description, assigned Ollama model, and permissions.
5.  **Backend to Ollama:** The backend constructs a request to the Ollama service, including the system prompt and the user's message. It requests a streaming response.
6.  **Streaming Response:**
    *   Ollama streams the generated response back to the Flask backend.
    *   For each chunk of text received from Ollama, the backend emits a `chat_chunk` event back to the frontend over the WebSocket.
7.  **Frontend Renders Chunks:** The frontend listens for `chat_chunk` events. Upon receiving a chunk, it appends the content to the current assistant message, creating the real-time "typing" effect.
8.  **Completion:** Once the stream from Ollama is complete, the backend emits a single `chat_complete` event. The frontend listens for this to know when to stop waiting for more chunks and finalizes the assistant's message.

This architecture centralizes real-time communication through a single WebSocket channel, making it efficient and stateful.

---

## Locrit Configuration Management

Locrit configurations are primarily stored in a central `config.yaml` file in the project root. This file is the single source of truth for the backend.

### Where Configurations are Stored

1.  **Backend (Primary Storage):** The `config.yaml` file contains a `locrits.instances` section where each Locrit is defined with its properties:
    *   `description`: A text description of the Locrit's purpose.
    *   `ollama_model`: The specific Ollama model to use (e.g., `codellama`, `llama3.1:8b-instruct-q3_K_M`).
    *   `active`: A boolean to activate or deactivate the Locrit.
    *   `open_to`: Permissions defining who can interact with the Locrit (e.g., `humans`, `locrits`).
    *   `access_to`: Permissions defining what data other Locrits can access.
    *   Timestamps (`created_at`, `updated_at`).

    The `src/services/config_service.py` is responsible for reading from and writing to this file.

2.  **Frontend (State, not Storage):** The frontend does **not** store configurations. When a user navigates to the chat page, the frontend fetches the specific Locrit's details from the backend API (`/api/v1/locrits/<locrit_name>/info`) and holds it in its component state for the duration of the session.

3.  **Cloud (Optional):** This project is configured to optionally use Firebase for authentication (`.env` file), but Locrit configurations themselves are **not** currently stored in the cloud. They remain local in the `config.yaml` file.

### How to Edit Locrit Configurations

There are two ways to edit Locrit configurations:

1.  **Via the Web UI (Recommended):**
    *   Navigate to the "My Locrits" page.
    *   From here, you can **create**, **edit**, **delete**, or **toggle the active status** of any Locrit.
    *   When you save changes, the backend's `locrits` routes (`backend/routes/locrits.py`) are called. These routes use the `config_service` to safely update the `config.yaml` file and save the changes.

2.  **Manually (For Advanced Users):**
    *   You can directly edit the `locrits.instances` section in the `config.yaml` file.
    *   **Caution:** Be careful with the YAML syntax (indentation is critical).
    *   You must restart the backend server for the changes to be loaded into the application.

Using the web UI is the safest and recommended method as it ensures data integrity and does not require a server restart.