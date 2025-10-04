#!/usr/bin/env python3
"""
Comprehensive API Tests with Memory Leak Detection
Tests the autonomous conversation API and monitors memory usage.
"""

import os
import sys
import time
import psutil
import requests
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import yaml

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_api"
TEST_LOCRIT = "Bob Technique"  # Assuming this exists in config

# Memory monitoring
process = psutil.Process(os.getpid())


class MemoryMonitor:
    """Monitor memory usage during tests."""

    def __init__(self):
        self.samples: List[Dict] = []
        self.start_memory = 0
        self.server_pid = None
        self.server_process = None

    def find_server_process(self):
        """Find the Flask server process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'web_app.py' in ' '.join(cmdline):
                    self.server_pid = proc.info['pid']
                    self.server_process = psutil.Process(self.server_pid)
                    print(f"📊 Found server process: PID {self.server_pid}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def start(self):
        """Start monitoring."""
        self.find_server_process()
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        if self.server_process:
            self.server_start_memory = self.server_process.memory_info().rss / 1024 / 1024
            print(f"🔬 Memory monitoring started")
            print(f"   Test process: {self.start_memory:.2f} MB")
            print(f"   Server process: {self.server_start_memory:.2f} MB")

    def sample(self, label: str):
        """Take a memory sample."""
        client_memory = process.memory_info().rss / 1024 / 1024

        sample = {
            'timestamp': datetime.now().isoformat(),
            'label': label,
            'client_memory_mb': round(client_memory, 2),
            'client_delta_mb': round(client_memory - self.start_memory, 2)
        }

        if self.server_process:
            try:
                server_memory = self.server_process.memory_info().rss / 1024 / 1024
                sample['server_memory_mb'] = round(server_memory, 2)
                sample['server_delta_mb'] = round(server_memory - self.server_start_memory, 2)
            except psutil.NoSuchProcess:
                pass

        self.samples.append(sample)
        return sample

    def report(self):
        """Generate memory report."""
        print("\n" + "="*70)
        print("📊 MEMORY USAGE REPORT")
        print("="*70)

        for sample in self.samples:
            client_delta = sample['client_delta_mb']
            server_delta = sample.get('server_delta_mb', 0)

            print(f"\n{sample['label']}:")
            print(f"  Client: {sample['client_memory_mb']:.2f} MB (Δ {client_delta:+.2f} MB)")
            if 'server_memory_mb' in sample:
                print(f"  Server: {sample['server_memory_mb']:.2f} MB (Δ {server_delta:+.2f} MB)")

        # Check for memory leaks
        if len(self.samples) > 2:
            last_delta = self.samples[-1].get('server_delta_mb', 0)
            if last_delta > 100:  # More than 100MB increase
                print(f"\n⚠️  WARNING: Potential memory leak detected!")
                print(f"   Server memory increased by {last_delta:.2f} MB")
            elif last_delta < 10:
                print(f"\n✅ Memory usage is stable (Δ {last_delta:.2f} MB)")
            else:
                print(f"\n✓  Memory usage increased by {last_delta:.2f} MB (acceptable)")

        print("="*70)

        # Save report to file
        with open('memory_test_report.yaml', 'w') as f:
            yaml.dump({
                'test_run': datetime.now().isoformat(),
                'samples': self.samples
            }, f, default_flow_style=False)
        print(f"\n💾 Memory report saved to: memory_test_report.yaml")


class APITester:
    """Test the Locrit API."""

    def __init__(self, monitor: MemoryMonitor):
        self.monitor = monitor
        self.conversation_id: Optional[str] = None
        self.passed = 0
        self.failed = 0

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        icon = "✅" if passed else "❌"
        status = "PASS" if passed else "FAIL"
        print(f"{icon} {name}: {status}")
        if details:
            print(f"   {details}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def test_create_conversation(self):
        """Test creating a conversation."""
        print("\n" + "="*70)
        print("🧪 TEST: Create Conversation")
        print("="*70)

        try:
            response = requests.post(
                f"{BASE_URL}/api/conversations/create",
                json={
                    "locrit_name": TEST_LOCRIT,
                    "user_id": TEST_USER_ID,
                    "metadata": {
                        "test": "api_test",
                        "timestamp": datetime.now().isoformat()
                    }
                },
                timeout=10
            )

            self.log_test(
                "Create conversation - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Create conversation - Response has conversation_id",
                    'conversation_id' in data,
                    f"ID: {data.get('conversation_id', 'N/A')[:16]}..."
                )

                if 'conversation_id' in data:
                    self.conversation_id = data['conversation_id']

                    # Verify YAML file was created
                    yaml_path = f"data/conversations/{self.conversation_id}.yaml"
                    file_exists = os.path.exists(yaml_path)
                    self.log_test(
                        "Create conversation - YAML file created",
                        file_exists,
                        f"Path: {yaml_path}"
                    )

                    if file_exists:
                        # Verify YAML content
                        with open(yaml_path, 'r') as f:
                            conv_data = yaml.safe_load(f)

                        self.log_test(
                            "Create conversation - YAML has correct locrit_name",
                            conv_data.get('locrit_name') == TEST_LOCRIT,
                            f"Locrit: {conv_data.get('locrit_name')}"
                        )

                        self.log_test(
                            "Create conversation - YAML has status",
                            conv_data.get('status') == 'active',
                            f"Status: {conv_data.get('status')}"
                        )

            self.monitor.sample("After creating conversation")

        except Exception as e:
            self.log_test("Create conversation", False, f"Error: {str(e)}")

    def test_send_message(self):
        """Test sending a message."""
        print("\n" + "="*70)
        print("🧪 TEST: Send Message")
        print("="*70)

        if not self.conversation_id:
            self.log_test("Send message", False, "No conversation_id available")
            return

        try:
            # Test message
            test_message = "Bonjour! Peux-tu me dire ce que tu fais?"

            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/conversations/{self.conversation_id}/message",
                json={"message": test_message},
                timeout=60
            )
            duration = time.time() - start_time

            self.log_test(
                "Send message - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}, Duration: {duration:.2f}s"
            )

            if response.status_code == 200:
                data = response.json()

                self.log_test(
                    "Send message - Response has 'response' field",
                    'response' in data,
                    f"Response length: {len(data.get('response', ''))} chars"
                )

                self.log_test(
                    "Send message - Response has message_count",
                    'message_count' in data,
                    f"Count: {data.get('message_count', 0)}"
                )

                if 'response' in data:
                    print(f"\n   💬 Locrit response: {data['response'][:100]}...")

                # Verify YAML was updated
                yaml_path = f"data/conversations/{self.conversation_id}.yaml"
                with open(yaml_path, 'r') as f:
                    conv_data = yaml.safe_load(f)

                self.log_test(
                    "Send message - YAML message_count updated",
                    conv_data.get('message_count') == 2,  # 1 user + 1 assistant
                    f"Count in YAML: {conv_data.get('message_count')}"
                )

                self.log_test(
                    "Send message - YAML last_activity updated",
                    'last_activity' in conv_data,
                    f"Last activity: {conv_data.get('last_activity', 'N/A')}"
                )

            self.monitor.sample("After sending message")

        except Exception as e:
            self.log_test("Send message", False, f"Error: {str(e)}")

    def test_get_conversation_history(self):
        """Test getting conversation history."""
        print("\n" + "="*70)
        print("🧪 TEST: Get Conversation History")
        print("="*70)

        if not self.conversation_id:
            self.log_test("Get history", False, "No conversation_id available")
            return

        try:
            response = requests.get(
                f"{BASE_URL}/api/conversations/{self.conversation_id}",
                params={"limit": 50},
                timeout=10
            )

            self.log_test(
                "Get history - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()

                self.log_test(
                    "Get history - Has messages array",
                    'messages' in data,
                    f"Messages count: {len(data.get('messages', []))}"
                )

                messages = data.get('messages', [])
                if messages:
                    self.log_test(
                        "Get history - Messages have required fields",
                        all('role' in msg and 'content' in msg for msg in messages),
                        f"First message role: {messages[0].get('role')}"
                    )

                    # Check message order (should be chronological)
                    if len(messages) >= 2:
                        self.log_test(
                            "Get history - Messages in correct order",
                            messages[0].get('role') == 'user' and messages[1].get('role') == 'assistant',
                            "User message followed by assistant response"
                        )

            self.monitor.sample("After getting history")

        except Exception as e:
            self.log_test("Get history", False, f"Error: {str(e)}")

    def test_list_conversations(self):
        """Test listing conversations."""
        print("\n" + "="*70)
        print("🧪 TEST: List Conversations")
        print("="*70)

        try:
            response = requests.get(
                f"{BASE_URL}/api/conversations",
                params={
                    "user_id": TEST_USER_ID,
                    "locrit_name": TEST_LOCRIT
                },
                timeout=10
            )

            self.log_test(
                "List conversations - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()

                self.log_test(
                    "List conversations - Has conversations array",
                    'conversations' in data,
                    f"Count: {data.get('count', 0)}"
                )

                conversations = data.get('conversations', [])
                if conversations and self.conversation_id:
                    # Find our conversation
                    found = any(c.get('conversation_id') == self.conversation_id for c in conversations)
                    self.log_test(
                        "List conversations - Our conversation is listed",
                        found,
                        f"Found: {found}"
                    )

            self.monitor.sample("After listing conversations")

        except Exception as e:
            self.log_test("List conversations", False, f"Error: {str(e)}")

    def test_multiple_messages_memory_leak(self):
        """Test sending multiple messages to check for memory leaks."""
        print("\n" + "="*70)
        print("🧪 TEST: Multiple Messages (Memory Leak Detection)")
        print("="*70)

        if not self.conversation_id:
            self.log_test("Multiple messages", False, "No conversation_id available")
            return

        num_messages = 5
        messages = [
            "Quel est ton langage de programmation préféré?",
            "Peux-tu m'expliquer les boucles?",
            "Comment fonctionnent les fonctions?",
            "Qu'est-ce qu'une variable?",
            "Merci pour ton aide!"
        ]

        try:
            initial_sample = self.monitor.sample("Before multiple messages")

            for i, msg in enumerate(messages, 1):
                print(f"   Sending message {i}/{num_messages}...")
                response = requests.post(
                    f"{BASE_URL}/api/conversations/{self.conversation_id}/message",
                    json={"message": msg},
                    timeout=60
                )

                if response.status_code != 200:
                    self.log_test(f"Multiple messages - Message {i}", False, f"Status: {response.status_code}")
                    break

                # Brief pause between messages
                time.sleep(0.5)

            final_sample = self.monitor.sample(f"After {num_messages} messages")

            # Check memory growth
            if 'server_delta_mb' in final_sample and 'server_delta_mb' in initial_sample:
                memory_growth = final_sample['server_delta_mb'] - initial_sample['server_delta_mb']

                # Should not grow more than 50MB for 5 messages
                self.log_test(
                    f"Multiple messages - Memory growth acceptable",
                    abs(memory_growth) < 50,
                    f"Growth: {memory_growth:.2f} MB"
                )

            self.log_test(
                "Multiple messages - All messages sent successfully",
                True,
                f"Sent {num_messages} messages"
            )

        except Exception as e:
            self.log_test("Multiple messages", False, f"Error: {str(e)}")

    def test_conversation_info(self):
        """Test getting conversation info."""
        print("\n" + "="*70)
        print("🧪 TEST: Get Conversation Info")
        print("="*70)

        if not self.conversation_id:
            self.log_test("Get info", False, "No conversation_id available")
            return

        try:
            response = requests.get(
                f"{BASE_URL}/api/conversations/{self.conversation_id}/info",
                timeout=10
            )

            self.log_test(
                "Get info - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()

                required_fields = ['conversation_id', 'locrit_name', 'user_id', 'message_count']
                has_all_fields = all(field in data for field in required_fields)

                self.log_test(
                    "Get info - Has all required fields",
                    has_all_fields,
                    f"Fields: {', '.join(required_fields)}"
                )

                # Should NOT have messages
                self.log_test(
                    "Get info - Does not include messages",
                    'messages' not in data,
                    "Info endpoint should not return messages"
                )

            self.monitor.sample("After getting info")

        except Exception as e:
            self.log_test("Get info", False, f"Error: {str(e)}")

    def test_cleanup(self):
        """Test conversation deletion."""
        print("\n" + "="*70)
        print("🧪 TEST: Delete Conversation")
        print("="*70)

        if not self.conversation_id:
            self.log_test("Delete conversation", False, "No conversation_id available")
            return

        try:
            response = requests.delete(
                f"{BASE_URL}/api/conversations/{self.conversation_id}",
                timeout=10
            )

            self.log_test(
                "Delete conversation - HTTP status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            # Verify YAML file status was updated
            yaml_path = f"data/conversations/{self.conversation_id}.yaml"
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r') as f:
                    conv_data = yaml.safe_load(f)

                self.log_test(
                    "Delete conversation - Status updated to 'deleted'",
                    conv_data.get('status') == 'deleted',
                    f"Status: {conv_data.get('status')}"
                )

            self.monitor.sample("After deleting conversation")

        except Exception as e:
            self.log_test("Delete conversation", False, f"Error: {str(e)}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("📋 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total:  {self.passed + self.failed}")

        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        print(f"✓  Success rate: {success_rate:.1f}%")
        print("="*70)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 LOCRITS API TESTS WITH MEMORY MONITORING")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"Test Locrit: {TEST_LOCRIT}")
    print("="*70)

    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server is not accessible: {e}")
        print(f"   Please ensure the server is running: python web_app.py")
        sys.exit(1)

    # Initialize monitor and tester
    monitor = MemoryMonitor()
    monitor.start()

    tester = APITester(monitor)

    # Run tests
    monitor.sample("Initial state")

    tester.test_create_conversation()
    tester.test_send_message()
    tester.test_get_conversation_history()
    tester.test_list_conversations()
    tester.test_multiple_messages_memory_leak()
    tester.test_conversation_info()
    tester.test_cleanup()

    monitor.sample("Final state")

    # Print results
    tester.print_summary()
    monitor.report()

    # Exit with appropriate code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
