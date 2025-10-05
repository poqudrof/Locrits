#!/usr/bin/env python3
"""
Test script to verify conversation storage for Locrit root
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.memory_manager_service import MemoryManagerService

async def test_locrit_root_storage():
    """Test storing and retrieving messages for Locrit root"""
    print("🧪 Testing conversation storage for Locrit root...")

    locrit_name = "Locrit root"
    session_id = "test_session_123"
    user_id = "test_user"

    # Initialize memory manager
    memory_manager = MemoryManagerService()

    # Save test messages
    print(f"\n📝 Saving test messages...")
    await memory_manager.save_message(
        locrit_name=locrit_name,
        role="user",
        content="Hello, this is a test message from the user",
        session_id=session_id,
        user_id=user_id
    )
    print("✓ User message saved")

    await memory_manager.save_message(
        locrit_name=locrit_name,
        role="assistant",
        content="Hello! I am Locrit root. This is my test response.",
        session_id=session_id,
        user_id=user_id
    )
    print("✓ Assistant message saved")

    # Retrieve conversation history
    print(f"\n📖 Retrieving conversation history...")
    history = await memory_manager.get_conversation_history(
        locrit_name=locrit_name,
        session_id=session_id,
        limit=10
    )

    print(f"\n📊 Results:")
    print(f"   - Messages retrieved: {len(history)}")

    if len(history) >= 2:
        print(f"   ✅ SUCCESS: Found {len(history)} messages")
        for i, msg in enumerate(history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50]
            print(f"      {i}. [{role}] {content}...")

        # Get memory summary
        print(f"\n📊 Getting memory summary...")
        summary = await memory_manager.get_full_memory_summary(locrit_name)
        print(f"   - Total messages: {summary.get('statistics', {}).get('total_messages', 0)}")
        print(f"   - Total sessions: {summary.get('statistics', {}).get('total_sessions', 0)}")

        return True
    else:
        print(f"   ❌ FAILED: Expected at least 2 messages, found {len(history)}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_locrit_root_storage())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
