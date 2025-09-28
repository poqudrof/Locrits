#!/usr/bin/env python3
"""
Test WebSocket conversation context and memory functionality
"""

import socketio
import time
import sys

# Create a Socket.IO client
sio = socketio.Client()

# Configuration
BASE_URL = "http://localhost:5000"
LOCRIT_NAME = "Bob Technique"
TEST_NAME = "WebSocketTester"

# Variables to track responses
responses = []
response_count = 0

@sio.on('connect')
def on_connect():
    print("🔌 Connected to WebSocket server")

@sio.on('connected')
def on_connected(data):
    print(f"✅ Server confirmed connection: {data}")

@sio.on('joined_chat')
def on_joined_chat(data):
    print(f"✅ Joined chat room for: {data.get('locrit_name', 'Unknown')}")

@sio.on('chat_chunk')
def on_chat_chunk(data):
    global response_count
    if data.get('locrit_name') == LOCRIT_NAME:
        responses.append(data.get('content', ''))

@sio.on('chat_complete')
def on_chat_complete(data):
    global response_count
    response_count += 1
    if data.get('locrit_name') == LOCRIT_NAME:
        full_response = ''.join(responses)
        print(f"🤖 Full response {response_count}: {full_response[:100]}...")
        responses.clear()  # Clear for next message

@sio.on('error')
def on_error(data):
    print(f"❌ WebSocket error: {data}")

def send_message(message):
    print(f"📤 Sending: {message}")
    sio.emit('chat_message', {
        'locrit_name': LOCRIT_NAME,
        'message': message,
        'stream': True
    })

def test_websocket_memory():
    """Test WebSocket conversation memory"""

    try:
        # Connect to the server
        print("🧪 Testing WebSocket Conversation Memory")
        print("=" * 50)

        sio.connect(BASE_URL)

        # Join the chat room
        sio.emit('join_chat', {'locrit_name': LOCRIT_NAME})

        # Wait for connection setup
        time.sleep(2)

        print("\n🧠 Step 1: Introducing ourselves...")
        send_message(f"Hello! My name is {TEST_NAME}. Please remember my name.")

        # Wait for response
        time.sleep(8)

        print("\n🔍 Step 2: Testing name recall...")
        send_message("What is my name?")

        # Wait for response
        time.sleep(8)

        print("\n📝 Step 3: Testing conversation continuity...")
        send_message("Can you tell me what we just talked about?")

        # Wait for response
        time.sleep(8)

        print("\n✅ WebSocket memory test completed!")
        print("Check the responses above to see if:")
        print("1. The Locrit remembered your name")
        print("2. The Locrit referenced previous conversation")

        sio.disconnect()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_websocket_memory()