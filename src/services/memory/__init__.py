"""
Modular Memory System for Locrits

This package provides a sophisticated memory management system that separates
graph-based (precise) memories from vector-based (fuzzy) memories, allowing
LLMs to make intelligent decisions about how to store and retrieve information.

Key Components:
- GraphMemoryService: Handles facts, events, relationships, structured data
- VectorMemoryService: Handles experiences, impressions, themes, semantic content
- MemoryManager: Orchestrates between services and provides intelligent decisions
- MemoryTools: LLM-accessible tools for memory management

Usage:
    from src.services.memory import create_memory_system

    # Initialize the memory system
    memory_manager, memory_tools = await create_memory_system(
        locrit_name="MyLocrit",
        config_path="config/memory.yaml"
    )

    # Use memory tools in LLM context
    result = await memory_tools["store_graph_memory"](
        content="Paris is the capital of France",
        memory_type="fact",
        importance=0.8
    )
"""

from .interfaces import (
    MemoryType,
    MemoryImportance,
    MemoryItem,
    MemorySearchResult,
    MemoryDecision,
    BaseMemoryService,
    GraphMemoryService,
    VectorMemoryService,
    MemoryOrchestrator,
    MemoryDecisionEngine
)

from .config import (
    MemoryConfig,
    VectorMemoryConfig,
    GraphMemoryConfig,
    MemoryUpdateConfig,
    MemoryRetentionConfig,
    MemoryConfigManager
)

from .graph_memory_service import KuzuGraphMemoryService
from .vector_memory_service import KuzuVectorMemoryService
from .memory_manager import IntelligentMemoryManager
from .memory_tools import MemoryTools, create_memory_tools

# Version info
__version__ = "1.0.0"
__author__ = "Locrits Memory System"

# Main factory function
async def create_memory_system(locrit_name: str, config_path: str = None):
    """
    Create and initialize a complete memory system.

    Args:
        locrit_name: Name of the Locrit
        config_path: Path to memory configuration file

    Returns:
        Tuple of (memory_manager, memory_tools_dict)
    """
    # Initialize memory manager
    memory_manager = IntelligentMemoryManager(locrit_name, config_path)

    # Initialize services
    success = await memory_manager.initialize()
    if not success:
        raise Exception(f"Failed to initialize memory system for {locrit_name}")

    # Create LLM tools
    memory_tools = create_memory_tools(memory_manager)

    return memory_manager, memory_tools

async def create_memory_manager(locrit_name: str, config_path: str = None):
    """
    Create and initialize just the memory manager.

    Args:
        locrit_name: Name of the Locrit
        config_path: Path to memory configuration file

    Returns:
        Initialized IntelligentMemoryManager
    """
    memory_manager = IntelligentMemoryManager(locrit_name, config_path)
    success = await memory_manager.initialize()

    if not success:
        raise Exception(f"Failed to initialize memory manager for {locrit_name}")

    return memory_manager

def create_default_config(path: str = "config/memory.yaml"):
    """
    Create a default memory configuration file.

    Args:
        path: Where to save the configuration file
    """
    config_manager = MemoryConfigManager()
    config_manager.save_default_config(path)
    print(f"Default memory configuration created at: {path}")

def validate_config(config_path: str = None):
    """
    Validate memory configuration and return any issues.

    Args:
        config_path: Path to configuration file

    Returns:
        List of validation issues (empty if valid)
    """
    config_manager = MemoryConfigManager(config_path)
    config = config_manager.load_config()
    return config_manager.validate_config(config)

# Convenience imports for common patterns
from .interfaces import MemoryType as MT, MemoryImportance as MI

# Export all public interfaces
__all__ = [
    # Main factory functions
    'create_memory_system',
    'create_memory_manager',
    'create_default_config',
    'validate_config',

    # Core classes
    'IntelligentMemoryManager',
    'KuzuGraphMemoryService',
    'KuzuVectorMemoryService',
    'MemoryTools',
    'create_memory_tools',

    # Configuration
    'MemoryConfig',
    'VectorMemoryConfig',
    'GraphMemoryConfig',
    'MemoryUpdateConfig',
    'MemoryRetentionConfig',
    'MemoryConfigManager',

    # Interfaces and types
    'MemoryType',
    'MemoryImportance',
    'MemoryItem',
    'MemorySearchResult',
    'MemoryDecision',
    'BaseMemoryService',
    'GraphMemoryService',
    'VectorMemoryService',
    'MemoryOrchestrator',
    'MemoryDecisionEngine',

    # Convenience aliases
    'MT',
    'MI',

    # Version
    '__version__'
]