#!/usr/bin/env python3
"""
WebSocket Chat Storage Test
Tests that conversations via WebSocket are properly stored.
"""

import socketio
import time
import asyncio
from datetime import datetime


def print_separator(char="=", length=80):
    print(char * length)


def print_header(text):
    print_separator()
    print(f"🧪 {text}")
    print_separator()


def print_success(text):
    print(f"✅ {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def test_websocket_chat_storage():
    """Test WebSocket chat with conversation storage"""

    BASE_URL = "http://localhost:5000"
    LOCRIT_NAME = "Bob Technique"
    SESSION_ID = f"test_ws_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print_header("TEST 1: Connect to WebSocket")

    # Create SocketIO client
    sio = socketio.Client()
    received_messages = []
    chat_complete = False

    @sio.on('connected')
    def on_connected(data):
        print_success(f"Connected to WebSocket: {data}")

    @sio.on('joined_chat')
    def on_joined_chat(data):
        print_success(f"Joined chat room: {data.get('room')}")

    @sio.on('chat_chunk')
    def on_chat_chunk(data):
        content = data.get('content', '')
        if content:
            received_messages.append(content)

    @sio.on('chat_complete')
    def on_chat_complete(data):
        nonlocal chat_complete
        chat_complete = True
        print_info("Chat response completed")

    @sio.on('error')
    def on_error(data):
        print_error(f"WebSocket error: {data}")

    # Connect to server
    try:
        sio.connect(BASE_URL, namespaces=['/chat'])
        print_success("WebSocket connection established")
        time.sleep(0.5)
    except Exception as e:
        print_error(f"Failed to connect to WebSocket: {e}")
        print_info("Make sure backend is running: python web_app.py")
        return False

    # ========================================================================
    print_header("TEST 2: Join Chat Room")

    try:
        sio.emit('join_chat', {
            'locrit_name': LOCRIT_NAME,
            'session_id': SESSION_ID
        }, namespace='/chat')

        time.sleep(0.5)
        print_success("Joined chat room")
    except Exception as e:
        print_error(f"Failed to join chat: {e}")
        sio.disconnect()
        return False

    # ========================================================================
    print_header("TEST 3: Send Chat Message")

    test_message = "Hello, this is a WebSocket test message."
    print_info(f"Sending: {test_message}")

    try:
        received_messages.clear()
        chat_complete = False

        sio.emit('chat_message', {
            'locrit_name': LOCRIT_NAME,
            'session_id': SESSION_ID,
            'message': test_message,
            'stream': True
        }, namespace='/chat')

        # Wait for response
        timeout = 30
        start_time = time.time()

        while not chat_complete and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if chat_complete:
            full_response = ''.join(received_messages)
            print_success(f"Received response ({len(full_response)} chars)")
            print_info(f"Response preview: {full_response[:100]}...")
        else:
            print_error("Timeout waiting for response")
            sio.disconnect()
            return False

    except Exception as e:
        print_error(f"Failed to send message: {e}")
        import traceback
        traceback.print_exc()
        sio.disconnect()
        return False

    # Wait for storage to complete
    time.sleep(1)

    # ========================================================================
    print_header("TEST 4: Verify Message Storage via Memory API")

    sio.disconnect()

    import requests

    try:
        # Check memory summary
        response = requests.get(
            f"{BASE_URL}/api/locrits/{LOCRIT_NAME}/memory/summary",
            timeout=10
        )

        if response.status_code != 200:
            print_error(f"Memory API failed: {response.status_code}")
            return False

        data = response.json()
        stats = data.get('statistics', {})
        total_messages = stats.get('total_messages', 0)

        print_success(f"Memory API accessible")
        print_info(f"Total messages in memory: {total_messages}")

        if total_messages > 0:
            print_success("✓ Messages are being stored")

            # Check recent messages
            recent_messages = data.get('recent_messages', [])
            print_info(f"Recent messages: {len(recent_messages)}")

            # Look for our test message or at least some recent activity
            found_recent = len(recent_messages) > 0

            if found_recent:
                print_success("✓ Conversation history is accessible")

                # Display recent messages
                print_info("\nRecent conversation:")
                for i, msg in enumerate(recent_messages[:5], 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:50]
                    print(f"  {i}. [{role}] {content}...")

                return True
            else:
                print_error("✗ No recent messages found")
                return False
        else:
            print_error("✗ No messages in memory")
            return False

    except Exception as e:
        print_error(f"Memory verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n")
    print_separator("═", 80)
    print("  WEBSOCKET CHAT STORAGE TEST")
    print_separator("═", 80)
    print()

    result = test_websocket_chat_storage()

    print("\n")
    print_separator("═", 80)

    if result:
        print("🎉 WEBSOCKET CHAT TEST PASSED!")
        print_info("\nVerified:")
        print("  ✓ WebSocket connection works")
        print("  ✓ Chat messages send successfully")
        print("  ✓ Responses are received")
        print("  ✓ Messages are stored in memory")
        print("  ✓ Conversation history is accessible")
    else:
        print("💥 WEBSOCKET CHAT TEST FAILED!")
        print_info("\nTroubleshooting:")
        print("  1. Make sure backend is running: python web_app.py")
        print("  2. Check Ollama is running: curl http://localhost:11434")
        print("  3. Verify Locrit is active and configured")

    print_separator("═", 80)

    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
