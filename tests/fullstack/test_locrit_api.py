#!/usr/bin/env python3
"""
Comprehensive tests for Locrit HTTP Chat API
Tests basic functionality and memory persistence
"""

import requests
import json
import time
import sys
from urllib.parse import quote

# Configuration
BASE_URL = "http://localhost:5000"
TEST_LOCRIT_NAME = "Bob Technique"  # Change this to match your Locrit name
TEST_USER_NAME = "TestUser"

def test_api_connection():
    """Test if the API server is running"""
    print("🔌 Testing API connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/locrits", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to API server: {e}")
        return False

def test_list_locrits():
    """Test listing available Locrits"""
    print("\n📋 Testing Locrit listing...")
    try:
        response = requests.get(f"{BASE_URL}/api/locrits")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'locrits' in data:
                locrits = data['locrits']['instances']
                print(f"✅ Found {len(locrits)} Locrits:")
                for name, settings in locrits.items():
                    status = "🟢 Active" if settings.get('active') else "🔴 Inactive"
                    print(f"  - {name}: {status}")

                # Check if our test Locrit exists
                if TEST_LOCRIT_NAME in locrits:
                    print(f"✅ Test Locrit '{TEST_LOCRIT_NAME}' found")
                    return True, locrits[TEST_LOCRIT_NAME]
                else:
                    print(f"❌ Test Locrit '{TEST_LOCRIT_NAME}' not found")
                    print("Available Locrits:", list(locrits.keys()))
                    return False, None
            else:
                print(f"❌ Unexpected response format: {data}")
                return False, None
        else:
            print(f"❌ Failed to list Locrits: {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_locrit_activation(locrit_settings):
    """Ensure the test Locrit is active"""
    print(f"\n⚡ Checking if '{TEST_LOCRIT_NAME}' is active...")

    if locrit_settings.get('active'):
        print("✅ Locrit is already active")
        return True

    print("🔄 Activating Locrit...")
    try:
        encoded_name = quote(TEST_LOCRIT_NAME)
        response = requests.post(f"{BASE_URL}/api/locrits/{encoded_name}/toggle")

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('active'):
                print("✅ Locrit activated successfully")
                return True
            else:
                print(f"❌ Failed to activate Locrit: {data}")
                return False
        else:
            print(f"❌ Activation request failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Activation request failed: {e}")
        return False

def send_chat_message(message, expect_success=True):
    """Send a chat message to the Locrit"""
    print(f"\n💬 Sending message: '{message}'")

    try:
        encoded_name = quote(TEST_LOCRIT_NAME)
        payload = {"message": message}

        response = requests.post(
            f"{BASE_URL}/api/locrits/{encoded_name}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # Longer timeout for LLM generation
        )

        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Locrit responded: '{data.get('response', '')[:100]}...'")
                return True, data.get('response', '')
            else:
                print(f"❌ Chat failed: {data.get('error', 'Unknown error')}")
                return False, data.get('error', '')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', f'HTTP {response.status_code}')
            except:
                error_msg = f'HTTP {response.status_code}'

            if expect_success:
                print(f"❌ Chat request failed: {error_msg}")
            else:
                print(f"✅ Expected failure: {error_msg}")
            return False, error_msg

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, str(e)

def test_basic_chat():
    """Test basic chat functionality"""
    print("\n🤖 Testing basic chat functionality...")

    # Test simple greeting
    success, response = send_chat_message("Hello! How are you today?")
    if not success:
        return False

    # Test follow-up message
    success, response = send_chat_message("Can you tell me a joke?")
    if not success:
        return False

    print("✅ Basic chat functionality working")
    return True

def test_memory_persistence():
    """Test memory persistence - name recall test"""
    print("\n🧠 Testing memory persistence...")

    # Step 1: Introduce ourselves with a name
    print("👋 Step 1: Introducing ourselves...")
    success, response = send_chat_message(f"Hello! My name is {TEST_USER_NAME}. Please remember that.")
    if not success:
        print("❌ Failed to send introduction message")
        return False

    print(f"🤖 Locrit's introduction response: '{response[:150]}...'")

    # Brief pause to ensure message is saved
    print("⏳ Waiting for memory to be saved...")
    time.sleep(2)

    # Step 2: Ask the Locrit to recall our name
    print("🔍 Step 2: Testing name recall...")
    success, response = send_chat_message("What is my name?")
    if not success:
        print("❌ Failed to send name recall question")
        return False

    print(f"🤖 Locrit's recall response: '{response}'")

    # Check if the response contains our name
    if TEST_USER_NAME.lower() in response.lower():
        print(f"✅ Memory persistence working! Locrit remembered the name '{TEST_USER_NAME}'")
        return True
    else:
        print(f"❌ Memory persistence failed! Locrit did not recall the name '{TEST_USER_NAME}'")
        print("This could indicate:")
        print("  - Memory system not working properly")
        print("  - Conversation context not being sent to Ollama")
        print("  - LLM not understanding the context")
        return False

def test_error_cases():
    """Test various error scenarios"""
    print("\n🚨 Testing error cases...")

    # Test empty message
    print("📝 Testing empty message...")
    try:
        encoded_name = quote(TEST_LOCRIT_NAME)
        response = requests.post(
            f"{BASE_URL}/api/locrits/{encoded_name}/chat",
            json={"message": ""},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            print("✅ Empty message correctly rejected")
        else:
            print(f"⚠️ Empty message returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Empty message test failed: {e}")

    # Test non-existent Locrit
    print("👻 Testing non-existent Locrit...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/locrits/NonExistentLocrit/chat",
            json={"message": "Hello"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 404:
            print("✅ Non-existent Locrit correctly rejected")
        else:
            print(f"⚠️ Non-existent Locrit returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Non-existent Locrit test failed: {e}")

    print("✅ Error case testing completed")

def main():
    """Run all tests"""
    print("🧪 Starting Locrit HTTP API Tests")
    print("=" * 50)

    # Test 1: API Connection
    if not test_api_connection():
        print("\n❌ API connection failed. Make sure the Flask server is running on http://localhost:5000")
        return False

    # Test 2: List Locrits
    success, locrit_settings = test_list_locrits()
    if not success:
        print(f"\n❌ Cannot find test Locrit '{TEST_LOCRIT_NAME}'")
        return False

    # Test 3: Ensure Locrit is active
    if not test_locrit_activation(locrit_settings):
        print(f"\n❌ Cannot activate test Locrit '{TEST_LOCRIT_NAME}'")
        return False

    # Test 4: Basic chat functionality
    if not test_basic_chat():
        print("\n❌ Basic chat functionality failed")
        return False

    # Test 5: Memory persistence (the main test)
    if not test_memory_persistence():
        print("\n❌ Memory persistence test failed")
        return False

    # Test 6: Error cases
    test_error_cases()

    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Locrit HTTP API is working correctly")
    print("✅ Memory persistence is functioning")
    print("✅ Conversation context is maintained")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)