#!/usr/bin/env python3
"""
Memory Test for Locrits - Progressive Information Sharing
Tests the Locrit's ability to remember and recall information about a fictive character
across multiple conversations.

Test Flow:
1. Initial conversation - Introduce basic character info (name)
2. Second conversation - Add more traits and details
3. Third conversation - Add final details
4. Memory verification - Check stored memory directly
5. Memory recall - Ask Locrit to recall all character information
"""

import requests
import json
import sys
import time
from faker import Faker

# Configuration
BASE_URL = "http://localhost:5000"
DEFAULT_LOCRIT = "Bob Technique"

# Initialize Faker for generating fictive character
fake = Faker()

class MemoryTest:
    """Test class for Locrit memory functionality"""

    def __init__(self, locrit_name=DEFAULT_LOCRIT):
        self.locrit_name = locrit_name
        self.conversation_id = None
        self.character = self._generate_character()

    def _generate_character(self):
        """Generate a fictive character with multiple traits"""
        return {
            "name": fake.name(),
            "age": fake.random_int(min=25, max=65),
            "occupation": fake.job(),
            "city": fake.city(),
            "hobby": fake.random_element(["painting", "photography", "cooking", "gardening", "reading"]),
            "pet": fake.random_element(["dog", "cat", "parrot", "fish", "hamster"]),
            "favorite_color": fake.color_name(),
            "personality": fake.random_element(["cheerful", "thoughtful", "energetic", "calm", "curious"])
        }

    def create_conversation(self):
        """Create a new conversation with the Locrit"""
        print(f"\n🔧 Creating conversation with {self.locrit_name}...")

        response = requests.post(
            f"{BASE_URL}/api/conversations/create",
            json={
                "locrit_name": self.locrit_name,
                "user_id": "memory_test_user",
                "metadata": {
                    "test_type": "memory_progression",
                    "character_name": self.character["name"]
                }
            },
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ Failed to create conversation: {response.text}")
            return False

        data = response.json()
        self.conversation_id = data.get('conversation_id')
        print(f"✅ Conversation created: {self.conversation_id}")
        return True

    def send_message(self, message):
        """Send a message in the conversation"""
        if not self.conversation_id:
            print("❌ No conversation created yet")
            return None

        try:
            response = requests.post(
                f"{BASE_URL}/api/conversations/{self.conversation_id}/message",
                json={"message": message},
                timeout=30  # Add timeout to prevent hanging
            )

            if response.status_code != 200:
                print(f"❌ Failed to send message: {response.text}")
                return None

            return response.json()
        except requests.exceptions.Timeout:
            print(f"⚠️  Message request timed out - Locrit may not be running")
            return {"response": "[TIMEOUT - Locrit not responding]", "error": "timeout"}

    def get_conversation_history(self):
        """Get the conversation history"""
        if not self.conversation_id:
            return None

        response = requests.get(
            f"{BASE_URL}/api/conversations/{self.conversation_id}",
            timeout=10
        )

        if response.status_code != 200:
            return None

        return response.json()

    def check_memory(self):
        """Check the Locrit's memory directly"""
        print(f"\n🧠 Checking Locrit's memory directly...")

        # Try to get memory endpoint
        try:
            response = requests.get(
                f"{BASE_URL}/api/locrits/{self.locrit_name}/memory",
                params={"conversation_id": self.conversation_id},
                timeout=10
            )

            if response.status_code == 200:
                memory_data = response.json()
                print(f"✅ Memory retrieved successfully")
                return memory_data
            else:
                print(f"⚠️  Memory endpoint not available or error: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print(f"⚠️  Memory request timed out")
            return None

    def run_test(self):
        """Run the complete memory test"""
        print("=" * 80)
        print("🧪 LOCRIT MEMORY PROGRESSION TEST")
        print("=" * 80)

        # Display character info
        print(f"\n📋 Generated Fictive Character:")
        print(f"   Name: {self.character['name']}")
        print(f"   Age: {self.character['age']}")
        print(f"   Occupation: {self.character['occupation']}")
        print(f"   City: {self.character['city']}")
        print(f"   Hobby: {self.character['hobby']}")
        print(f"   Pet: {self.character['pet']}")
        print(f"   Favorite Color: {self.character['favorite_color']}")
        print(f"   Personality: {self.character['personality']}")

        # Create conversation
        if not self.create_conversation():
            return False

        # Conversation 1: Introduce name and age
        print("\n" + "=" * 80)
        print("📝 CONVERSATION 1: Basic Introduction")
        print("=" * 80)

        message1 = f"Hello! I want to tell you about someone named {self.character['name']}. They are {self.character['age']} years old. Please remember this person."
        print(f"\n👤 User: {message1}")

        response1 = self.send_message(message1)
        if response1:
            print(f"🤖 {self.locrit_name}: {response1.get('response')}")
            time.sleep(2)

        # Conversation 2: Add occupation and city
        print("\n" + "=" * 80)
        print("📝 CONVERSATION 2: Adding More Details")
        print("=" * 80)

        message2 = f"{self.character['name']} works as a {self.character['occupation']} and lives in {self.character['city']}. Can you tell me what you know about {self.character['name']} so far?"
        print(f"\n👤 User: {message2}")

        response2 = self.send_message(message2)
        if response2:
            print(f"🤖 {self.locrit_name}: {response2.get('response')}")
            time.sleep(2)

        # Conversation 3: Add hobby, pet, and personality
        print("\n" + "=" * 80)
        print("📝 CONVERSATION 3: Final Details")
        print("=" * 80)

        message3 = f"Some more things about {self.character['name']}: they love {self.character['hobby']}, have a pet {self.character['pet']}, their favorite color is {self.character['favorite_color']}, and they have a {self.character['personality']} personality. What do you remember about this person now?"
        print(f"\n👤 User: {message3}")

        response3 = self.send_message(message3)
        if response3:
            print(f"🤖 {self.locrit_name}: {response3.get('response')}")
            time.sleep(2)

        # Memory Check 1: Direct memory inspection
        print("\n" + "=" * 80)
        print("🔍 MEMORY VERIFICATION 1: Direct Memory Inspection")
        print("=" * 80)

        memory_data = self.check_memory()
        if memory_data:
            print(f"\n📊 Memory contents:")
            print(json.dumps(memory_data, indent=2))

        # Memory Check 2: Ask Locrit to recall
        print("\n" + "=" * 80)
        print("🔍 MEMORY VERIFICATION 2: Recall Test")
        print("=" * 80)

        recall_message = f"Can you tell me everything you remember about {self.character['name']}? Include all the details I told you."
        print(f"\n👤 User: {recall_message}")

        recall_response = self.send_message(recall_message)
        if recall_response:
            print(f"🤖 {self.locrit_name}: {recall_response.get('response')}")

        # Memory Check 3: Specific detail recall
        print("\n" + "=" * 80)
        print("🔍 MEMORY VERIFICATION 3: Specific Detail Recall")
        print("=" * 80)

        specific_questions = [
            f"What is {self.character['name']}'s occupation?",
            f"Where does {self.character['name']} live?",
            f"What hobby does {self.character['name']} enjoy?",
            f"What pet does {self.character['name']} have?"
        ]

        for question in specific_questions:
            print(f"\n👤 User: {question}")
            q_response = self.send_message(question)
            if q_response:
                print(f"🤖 {self.locrit_name}: {q_response.get('response')}")
            time.sleep(1)

        # Final summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        history = self.get_conversation_history()
        if history:
            print(f"\n✅ Total messages in conversation: {history.get('message_count')}")
            print(f"✅ Conversation ID: {self.conversation_id}")

        print("\n🎯 Expected Information to Remember:")
        print(f"   ✓ Name: {self.character['name']}")
        print(f"   ✓ Age: {self.character['age']}")
        print(f"   ✓ Occupation: {self.character['occupation']}")
        print(f"   ✓ City: {self.character['city']}")
        print(f"   ✓ Hobby: {self.character['hobby']}")
        print(f"   ✓ Pet: {self.character['pet']}")
        print(f"   ✓ Favorite Color: {self.character['favorite_color']}")
        print(f"   ✓ Personality: {self.character['personality']}")

        print("\n📝 Review the Locrit's responses above to verify:")
        print("   1. Did it remember the name across all conversations?")
        print("   2. Did it accumulate information progressively?")
        print("   3. Can it recall specific details when asked?")
        print("   4. Does the memory persist throughout the conversation?")

        print("\n" + "=" * 80)
        print("✅ Memory test completed!")
        print("=" * 80)

        return True


def main():
    """Main test function"""
    # Check if server is running
    try:
        ping_response = requests.get(f"{BASE_URL}/api/v1/ping", timeout=5)
        if ping_response.status_code != 200:
            print("❌ Server is not responding correctly")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure the backend is running")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ Server at {BASE_URL} timed out")
        print("   Server may be overloaded or unresponsive")
        sys.exit(1)

    # Get Locrit name from command line or use default
    locrit_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOCRIT

    print(f"\n⚠️  NOTE: This test requires the Locrit '{locrit_name}' to be running and responding.")
    print(f"   If messages timeout, make sure the Locrit is active and configured properly.\n")

    # Run the test
    test = MemoryTest(locrit_name)
    success = test.run_test()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
