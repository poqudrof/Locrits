#!/usr/bin/env python3
"""
Test script for the Locrit conversation API.
This script demonstrates how to use the conversation service to chat with a Locrit.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_conversation_api(locrit_name="Pixie l'Organisateur"):
    """Test the conversation API with a Locrit."""

    print(f"🧪 Testing Conversation API with {locrit_name}\n")
    print("=" * 60)

    # Step 1: Create a conversation
    print("\n1️⃣ Creating a new conversation...")
    create_response = requests.post(
        f"{BASE_URL}/api/conversations/create",
        json={
            "locrit_name": locrit_name,
            "user_id": "test_user",
            "metadata": {
                "source": "test_script",
                "test": True
            }
        }
    )

    if create_response.status_code != 200:
        print(f"❌ Failed to create conversation: {create_response.text}")
        return False

    conversation_data = create_response.json()
    conversation_id = conversation_data.get('conversation_id')

    print(f"✅ Conversation created successfully!")
    print(f"   Conversation ID: {conversation_id}")
    print(f"   Locrit: {conversation_data.get('locrit_name')}")
    print(f"   Created at: {conversation_data.get('created_at')}")

    # Step 2: Send first message
    print("\n2️⃣ Sending first message...")
    message1 = "Bonjour! Peux-tu te présenter?"
    print(f"   User: {message1}")

    msg1_response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/message",
        json={"message": message1}
    )

    if msg1_response.status_code != 200:
        print(f"❌ Failed to send message: {msg1_response.text}")
        return False

    msg1_data = msg1_response.json()
    print(f"   {locrit_name}: {msg1_data.get('response')}")
    print(f"   Message count: {msg1_data.get('message_count')}")

    # Step 3: Send second message (conversation context should be maintained)
    print("\n3️⃣ Sending second message (context should be maintained)...")
    message2 = "De quoi venons-nous de parler?"
    print(f"   User: {message2}")

    msg2_response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/message",
        json={"message": message2}
    )

    if msg2_response.status_code != 200:
        print(f"❌ Failed to send message: {msg2_response.text}")
        return False

    msg2_data = msg2_response.json()
    print(f"   {locrit_name}: {msg2_data.get('response')}")
    print(f"   Message count: {msg2_data.get('message_count')}")

    # Step 4: Get conversation history
    print("\n4️⃣ Retrieving conversation history...")
    history_response = requests.get(
        f"{BASE_URL}/api/conversations/{conversation_id}"
    )

    if history_response.status_code != 200:
        print(f"❌ Failed to get history: {history_response.text}")
        return False

    history_data = history_response.json()
    print(f"✅ Retrieved conversation history")
    print(f"   Total messages: {history_data.get('message_count')}")
    print(f"   Messages:")
    for i, msg in enumerate(history_data.get('messages', []), 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        # Truncate long messages
        if len(content) > 80:
            content = content[:77] + "..."
        print(f"      {i}. [{role}] {content}")

    # Step 5: Test using conversation_id with the old chat API
    print("\n5️⃣ Testing conversation_id with legacy chat API...")
    message3 = "Rappelle-moi ton nom"
    print(f"   User: {message3}")

    chat_response = requests.post(
        f"{BASE_URL}/api/locrits/{locrit_name}/chat",
        json={
            "conversation_id": conversation_id,
            "message": message3
        }
    )

    if chat_response.status_code != 200:
        print(f"❌ Failed to use chat API: {chat_response.text}")
        return False

    chat_data = chat_response.json()
    print(f"   {locrit_name}: {chat_data.get('response')}")
    print(f"   Message count: {chat_data.get('message_count')}")

    # Step 6: List user conversations
    print("\n6️⃣ Listing user conversations...")
    list_response = requests.get(
        f"{BASE_URL}/api/conversations",
        params={"user_id": "test_user"}
    )

    if list_response.status_code != 200:
        print(f"❌ Failed to list conversations: {list_response.text}")
        return False

    list_data = list_response.json()
    print(f"✅ Found {list_data.get('count')} conversation(s)")
    for conv in list_data.get('conversations', []):
        print(f"   - {conv.get('conversation_id')}: {conv.get('locrit_name')} ({conv.get('message_count')} messages)")

    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print(f"\n💡 Key takeaway: The Locrit maintains all conversation context internally.")
    print(f"   You only need to send the conversation_id + message, no context needed!")

    return True


def test_api_v1_conversation(locrit_name="Pixie l'Organisateur"):
    """Test the API v1 endpoint with conversation support."""

    print(f"\n\n🧪 Testing API v1 with Conversation Support\n")
    print("=" * 60)

    # Create conversation
    print("\n1️⃣ Creating conversation via conversation API...")
    create_response = requests.post(
        f"{BASE_URL}/api/conversations/create",
        json={
            "locrit_name": locrit_name,
            "user_id": "api_test_user"
        }
    )

    if create_response.status_code != 200:
        print(f"❌ Failed: {create_response.text}")
        return False

    conversation_id = create_response.json().get('conversation_id')
    print(f"✅ Conversation created: {conversation_id}")

    # Use API v1 with conversation_id
    print("\n2️⃣ Using API v1 endpoint with conversation_id...")
    message = "Qui es-tu?"
    print(f"   User: {message}")

    api_response = requests.post(
        f"{BASE_URL}/api/v1/locrits/{locrit_name}/chat",
        json={
            "conversation_id": conversation_id,
            "message": message
        }
    )

    if api_response.status_code != 200:
        print(f"❌ Failed: {api_response.text}")
        return False

    api_data = api_response.json()
    print(f"   {locrit_name}: {api_data.get('response')}")
    print(f"✅ API v1 conversation support works!")

    return True


if __name__ == "__main__":
    # Check if server is running
    try:
        ping_response = requests.get(f"{BASE_URL}/api/v1/ping")
        if ping_response.status_code != 200:
            print("❌ Server is not responding correctly")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure the backend is running: python -m backend.app")
        sys.exit(1)

    # Get Locrit name from command line or use default
    locrit_name = sys.argv[1] if len(sys.argv) > 1 else "Pixie l'Organisateur"

    # Run tests
    success = test_conversation_api(locrit_name)
    if success:
        test_api_v1_conversation(locrit_name)
    else:
        sys.exit(1)
