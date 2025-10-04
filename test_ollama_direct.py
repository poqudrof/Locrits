#!/usr/bin/env python3
"""Quick test of Ollama integration"""

import requests

# Test Ollama directly
print("Testing Ollama...")
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.1:8b-instruct-q3_K_M",
        "prompt": "Say hello in one sentence",
        "stream": False
    },
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Ollama works: {result.get('response', '')[:100]}...")
else:
    print(f"❌ Ollama failed: {response.status_code}")

# Test conversation API
print("\nTesting Conversation API...")
import time

# Create conversation
create_resp = requests.post(
    "http://localhost:5000/api/conversations/create",
    json={"locrit_name": "Bob Technique", "user_id": "quick_test"}
)

if create_resp.status_code == 200:
    conv_id = create_resp.json()['conversation_id']
    print(f"✅ Conversation created: {conv_id[:16]}...")

    # Send message
    print("Sending message...")
    start = time.time()
    msg_resp = requests.post(
        f"http://localhost:5000/api/conversations/{conv_id}/message",
        json={"message": "Say hello"},
        timeout=90
    )
    duration = time.time() - start

    if msg_resp.status_code == 200:
        print(f"✅ Message sent successfully in {duration:.2f}s")
        print(f"   Response: {msg_resp.json().get('response', '')[:100]}...")
    else:
        print(f"❌ Message failed: {msg_resp.status_code}")
        print(f"   Error: {msg_resp.text[:200]}")
else:
    print(f"❌ Create failed: {create_resp.status_code}")
