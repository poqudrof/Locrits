"""
Example usage of the modular memory system.

This demonstrates how to integrate the memory system with a Locrit
and how the LLM can make decisions about memory storage.
"""

import asyncio
from typing import Dict, List, Any

from . import create_memory_system, create_default_config, validate_config


async def example_basic_usage():
    """Basic example of using the memory system."""
    print("=== Basic Memory System Usage ===\n")

    # Create memory system for a Locrit
    try:
        memory_manager, memory_tools = await create_memory_system(
            locrit_name="ExampleLocrit",
            config_path="config/memory.yaml"
        )
        print("✅ Memory system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize memory system: {e}")
        return

    # Example 1: Store different types of memories
    print("\n1. Storing different types of memories:")

    # Store a fact (graph memory)
    fact_result = await memory_tools["store_graph_memory"](
        content="Paris is the capital of France",
        memory_type="fact",
        importance=0.8,
        metadata={"category": "geography", "verified": True}
    )
    print(f"Stored fact: {fact_result}")

    # Store an experience (vector memory)
    experience_result = await memory_tools["store_vector_memory"](
        content="The sunset from the Eiffel Tower was breathtaking, with warm golden light",
        vector_type="souvenir",
        importance=0.6,
        emotional_tone="positive",
        tags=["travel", "visual", "emotional"]
    )
    print(f"Stored experience: {experience_result}")

    # Store an impression (vector memory)
    impression_result = await memory_tools["store_vector_memory"](
        content="I think the user is interested in travel and cultural experiences",
        vector_type="impression",
        importance=0.7,
        emotional_tone="neutral",
        metadata={"subject": "user_interests"}
    )
    print(f"Stored impression: {impression_result}")

    # Example 2: Let AI decide storage strategy
    print("\n2. AI-driven memory decisions:")

    test_contents = [
        "The meeting is scheduled for 3 PM tomorrow",
        "I felt really inspired after reading that book",
        "Machine learning is about finding patterns in data",
        "2 + 2 = 4"
    ]

    for content in test_contents:
        analysis = await memory_tools["analyze_memory_decision"](content)
        print(f"Content: '{content}'")
        print(f"  Recommendation: {analysis['recommendation']}")

        # Store using AI recommendation
        decision = analysis["recommendation"]
        if decision["memory_type"] == "graph":
            result = await memory_tools["store_graph_memory"](
                content=content,
                importance=decision["importance"],
                metadata={"ai_classified": True}
            )
        else:
            result = await memory_tools["store_vector_memory"](
                content=content,
                importance=decision["importance"],
                tags=decision["tags"],
                metadata={"ai_classified": True}
            )
        print(f"  Stored: {result['success']}")

    # Example 3: Search memories
    print("\n3. Searching memories:")

    # Search for facts about geography
    graph_results = await memory_tools["search_graph_memory"](
        query="capital France",
        limit=5,
        filters={"min_importance": 0.5}
    )
    print(f"Graph search results: {len(graph_results['results'])} found")
    for result in graph_results["results"][:2]:
        print(f"  - {result['content']} (relevance: {result['relevance_score']})")

    # Search for travel experiences
    vector_results = await memory_tools["search_vector_memory"](
        query="travel beautiful sunset",
        similarity_threshold=0.5,
        limit=5
    )
    print(f"Vector search results: {len(vector_results['results'])} found")
    for result in vector_results["results"][:2]:
        print(f"  - {result['content']} (similarity: {result.get('similarity_score', 'N/A')})")

    # Comprehensive search
    all_results = await memory_tools["search_all_memory"](
        query="Paris travel",
        strategy="parallel",
        limit=5
    )
    print(f"Comprehensive search results: {len(all_results['results'])} found")

    # Example 4: Memory status and management
    print("\n4. Memory management:")

    status = await memory_tools["get_memory_status"]()
    print(f"Memory status: {status['status']['statistics']}")
    print(f"Recommendations: {status['recommendations']}")

    # Force memory update
    update_result = await memory_tools["update_memory_now"](force=True)
    print(f"Memory update: {update_result}")

    # Close the memory system
    await memory_manager.close()
    print("\n✅ Memory system closed")


async def example_conversation_integration():
    """Example of integrating memory with conversation flow."""
    print("\n=== Conversation Integration Example ===\n")

    memory_manager, memory_tools = await create_memory_system(
        locrit_name="ConversationLocrit"
    )

    # Simulate a conversation
    conversation_messages = [
        {
            "role": "user",
            "content": "Hi! I'm planning a trip to Japan next month.",
            "timestamp": "2024-01-15T10:00:00",
            "id": "msg_001"
        },
        {
            "role": "assistant",
            "content": "That's exciting! Japan in February is beautiful. Are you interested in any specific regions?",
            "timestamp": "2024-01-15T10:00:30",
            "id": "msg_002"
        },
        {
            "role": "user",
            "content": "I want to see cherry blossoms, but I know it's not the season. Maybe temples instead?",
            "timestamp": "2024-01-15T10:01:00",
            "id": "msg_003"
        },
        {
            "role": "assistant",
            "content": "Cherry blossom season is typically March-May, but winter temples are magical! Kyoto has amazing temple complexes.",
            "timestamp": "2024-01-15T10:01:30",
            "id": "msg_004"
        }
    ]

    # Process conversation and update memories
    update_results = await memory_manager.update_memories_from_conversation(conversation_messages)
    print(f"Conversation processed: {update_results}")

    # Demonstrate how LLM would decide what to remember
    for message in conversation_messages:
        if message["role"] == "user":
            # Store user preferences and intentions
            analysis = await memory_tools["analyze_memory_decision"](
                content=message["content"],
                context={
                    "role": "user",
                    "conversation_context": "travel_planning",
                    "user_intent": "seeking_advice"
                }
            )

            if analysis["success"]:
                rec = analysis["recommendation"]
                print(f"User message: '{message['content']}'")
                print(f"  AI decision: {rec['memory_type']} (importance: {rec['importance']})")
                print(f"  Reasoning: {rec['reasoning']}")

                # Store based on recommendation
                if rec["memory_type"] == "vector":
                    await memory_tools["store_vector_memory"](
                        content=message["content"],
                        importance=rec["importance"],
                        tags=rec["tags"] + ["user_intent"],
                        metadata={"conversation_role": "user", "intent": "travel_planning"}
                    )
                else:
                    await memory_tools["store_graph_memory"](
                        content=message["content"],
                        importance=rec["importance"],
                        metadata={"conversation_role": "user", "intent": "travel_planning"}
                    )

    # Show how to search for user preferences later
    preferences = await memory_tools["search_vector_memory"](
        query="user travel preferences interests",
        vector_type="impression",
        limit=3
    )
    print(f"\nUser preferences found: {len(preferences['results'])}")
    for pref in preferences["results"]:
        print(f"  - {pref['content']}")

    await memory_manager.close()


async def example_memory_relationships():
    """Example of creating and using memory relationships."""
    print("\n=== Memory Relationships Example ===\n")

    memory_manager, memory_tools = await create_memory_system(
        locrit_name="RelationshipLocrit"
    )

    # Store related facts
    paris_id = (await memory_tools["store_graph_memory"](
        content="Paris is the capital of France",
        memory_type="fact",
        importance=0.8
    ))["memory_id"]

    france_id = (await memory_tools["store_graph_memory"](
        content="France is a country in Western Europe",
        memory_type="fact",
        importance=0.7
    ))["memory_id"]

    europe_id = (await memory_tools["store_graph_memory"](
        content="Europe is a continent with many countries",
        memory_type="fact",
        importance=0.6
    ))["memory_id"]

    # Create relationships
    rel1 = await memory_tools["create_memory_relationship"](
        from_memory_id=paris_id,
        to_memory_id=france_id,
        relationship_type="CAPITAL_OF",
        properties={"confidence": 1.0}
    )
    print(f"Created relationship: {rel1}")

    rel2 = await memory_tools["create_memory_relationship"](
        from_memory_id=france_id,
        to_memory_id=europe_id,
        relationship_type="PART_OF",
        properties={"confidence": 1.0, "relationship_details": "geographic"}
    )
    print(f"Created relationship: {rel2}")

    # Explore the memory network
    network = await memory_tools["get_memory_network"](
        memory_id=paris_id,
        radius=2
    )
    print(f"Memory network around Paris: {network}")

    await memory_manager.close()


def example_configuration():
    """Example of configuration management."""
    print("\n=== Configuration Management Example ===\n")

    # Create default configuration
    create_default_config("example_memory_config.yaml")

    # Validate configuration
    issues = validate_config("example_memory_config.yaml")
    if issues:
        print(f"Configuration issues found: {issues}")
    else:
        print("✅ Configuration is valid")

    # Load and examine configuration
    from .config import MemoryConfigManager
    config_manager = MemoryConfigManager("example_memory_config.yaml")
    config = config_manager.load_config()

    print(f"Vector service enabled: {config.vector.enabled}")
    print(f"Graph service enabled: {config.graph.enabled}")
    print(f"Update interval: {config.updates.update_interval} messages")
    print(f"Auto cleanup: {config.retention.auto_cleanup}")


async def main():
    """Run all examples."""
    try:
        await example_basic_usage()
        await example_conversation_integration()
        await example_memory_relationships()
        example_configuration()

        print("\n🎉 All examples completed successfully!")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())