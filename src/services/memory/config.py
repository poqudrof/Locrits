"""
Configuration management for the modular memory system.

Handles loading and validation of memory-related configuration from YAML files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class VectorMemoryConfig:
    """Configuration for vector memory service."""
    enabled: bool = True
    model: str = "nomic-embed-text"
    dimension: int = 768
    inference_mode: str = "ollama"  # remote, local, dynamic, ollama
    similarity_threshold: float = 0.7
    max_memories: int = 10000
    cleanup_threshold: float = 0.3  # Delete memories below this similarity to anything important
    ollama_base_url: str = "http://localhost:11434"  # Ollama server URL


@dataclass
class GraphMemoryConfig:
    """Configuration for graph memory service."""
    enabled: bool = True
    max_concepts_per_message: int = 5
    concept_confidence_threshold: float = 0.7
    relationship_strength_threshold: float = 0.5
    max_relationship_depth: int = 3
    auto_create_relationships: bool = True


@dataclass
class MemoryUpdateConfig:
    """Configuration for memory update scheduling."""
    auto_update: bool = True
    update_interval: int = 10  # messages
    force_update_on_user_request: bool = True
    update_on_session_end: bool = True
    batch_update: bool = True
    max_batch_size: int = 50


@dataclass
class MemoryRetentionConfig:
    """Configuration for memory retention policies."""
    default_retention_days: int = 365
    critical_retention_days: int = -1  # -1 means never delete
    low_importance_retention_days: int = 30
    ephemeral_retention_hours: int = 24
    auto_cleanup: bool = True
    cleanup_interval_hours: int = 24


@dataclass
class MemoryConfig:
    """Complete memory system configuration."""
    vector: VectorMemoryConfig = field(default_factory=VectorMemoryConfig)
    graph: GraphMemoryConfig = field(default_factory=GraphMemoryConfig)
    updates: MemoryUpdateConfig = field(default_factory=MemoryUpdateConfig)
    retention: MemoryRetentionConfig = field(default_factory=MemoryRetentionConfig)
    base_path: str = "data/memory"
    debug: bool = False


class MemoryConfigManager:
    """Manages loading and validation of memory configuration."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[MemoryConfig] = None

    def _find_config_file(self) -> str:
        """Find the configuration file in standard locations."""
        possible_paths = [
            "config/memory.yaml",
            "memory.yaml",
            "config.yaml",
            "../config/memory.yaml",
            "../memory.yaml",
            "../config.yaml"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Return default path if none found
        return "config/memory.yaml"

    def load_config(self) -> MemoryConfig:
        """Load configuration from YAML file."""
        if self._config is not None:
            return self._config

        config_dict = {}

        # Load from file if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config and 'memory' in file_config:
                        config_dict = file_config['memory']
                    elif file_config:
                        config_dict = file_config
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")

        # Create config with defaults and overrides
        self._config = self._create_config_from_dict(config_dict)
        return self._config

    def _create_config_from_dict(self, config_dict: Dict[str, Any]) -> MemoryConfig:
        """Create MemoryConfig from dictionary, applying defaults."""

        # Vector config
        vector_config = VectorMemoryConfig()
        if 'vector' in config_dict:
            vector_dict = config_dict['vector']
            vector_config.enabled = vector_dict.get('enabled', vector_config.enabled)
            vector_config.model = vector_dict.get('model', vector_config.model)
            vector_config.dimension = vector_dict.get('dimension', vector_config.dimension)
            vector_config.inference_mode = vector_dict.get('inference_mode', vector_config.inference_mode)
            vector_config.similarity_threshold = vector_dict.get('similarity_threshold', vector_config.similarity_threshold)
            vector_config.max_memories = vector_dict.get('max_memories', vector_config.max_memories)
            vector_config.cleanup_threshold = vector_dict.get('cleanup_threshold', vector_config.cleanup_threshold)
            vector_config.ollama_base_url = vector_dict.get('ollama_base_url', vector_config.ollama_base_url)

        # Graph config
        graph_config = GraphMemoryConfig()
        if 'graph' in config_dict:
            graph_dict = config_dict['graph']
            graph_config.enabled = graph_dict.get('enabled', graph_config.enabled)
            graph_config.max_concepts_per_message = graph_dict.get('max_concepts_per_message', graph_config.max_concepts_per_message)
            graph_config.concept_confidence_threshold = graph_dict.get('concept_confidence_threshold', graph_config.concept_confidence_threshold)
            graph_config.relationship_strength_threshold = graph_dict.get('relationship_strength_threshold', graph_config.relationship_strength_threshold)
            graph_config.max_relationship_depth = graph_dict.get('max_relationship_depth', graph_config.max_relationship_depth)
            graph_config.auto_create_relationships = graph_dict.get('auto_create_relationships', graph_config.auto_create_relationships)

        # Update config
        update_config = MemoryUpdateConfig()
        if 'updates' in config_dict:
            update_dict = config_dict['updates']
            update_config.auto_update = update_dict.get('auto_update', update_config.auto_update)
            update_config.update_interval = update_dict.get('update_interval', update_config.update_interval)
            update_config.force_update_on_user_request = update_dict.get('force_update_on_user_request', update_config.force_update_on_user_request)
            update_config.update_on_session_end = update_dict.get('update_on_session_end', update_config.update_on_session_end)
            update_config.batch_update = update_dict.get('batch_update', update_config.batch_update)
            update_config.max_batch_size = update_dict.get('max_batch_size', update_config.max_batch_size)

        # Retention config
        retention_config = MemoryRetentionConfig()
        if 'retention' in config_dict:
            retention_dict = config_dict['retention']
            retention_config.default_retention_days = retention_dict.get('default_retention_days', retention_config.default_retention_days)
            retention_config.critical_retention_days = retention_dict.get('critical_retention_days', retention_config.critical_retention_days)
            retention_config.low_importance_retention_days = retention_dict.get('low_importance_retention_days', retention_config.low_importance_retention_days)
            retention_config.ephemeral_retention_hours = retention_dict.get('ephemeral_retention_hours', retention_config.ephemeral_retention_hours)
            retention_config.auto_cleanup = retention_dict.get('auto_cleanup', retention_config.auto_cleanup)
            retention_config.cleanup_interval_hours = retention_dict.get('cleanup_interval_hours', retention_config.cleanup_interval_hours)

        # Main config
        return MemoryConfig(
            vector=vector_config,
            graph=graph_config,
            updates=update_config,
            retention=retention_config,
            base_path=config_dict.get('base_path', "data/memory"),
            debug=config_dict.get('debug', False)
        )

    def save_default_config(self, path: Optional[str] = None) -> None:
        """Save a default configuration file."""
        save_path = path or self.config_path

        default_config = {
            'memory': {
                'base_path': 'data/memory',
                'debug': False,
                'vector': {
                    'enabled': True,
                    'model': 'nomic-embed-text',
                    'dimension': 768,
                    'inference_mode': 'ollama',
                    'ollama_base_url': 'http://localhost:11434',
                    'similarity_threshold': 0.7,
                    'max_memories': 10000,
                    'cleanup_threshold': 0.3
                },
                'graph': {
                    'enabled': True,
                    'max_concepts_per_message': 5,
                    'concept_confidence_threshold': 0.7,
                    'relationship_strength_threshold': 0.5,
                    'max_relationship_depth': 3,
                    'auto_create_relationships': True
                },
                'updates': {
                    'auto_update': True,
                    'update_interval': 10,
                    'force_update_on_user_request': True,
                    'update_on_session_end': True,
                    'batch_update': True,
                    'max_batch_size': 50
                },
                'retention': {
                    'default_retention_days': 365,
                    'critical_retention_days': -1,
                    'low_importance_retention_days': 30,
                    'ephemeral_retention_hours': 24,
                    'auto_cleanup': True,
                    'cleanup_interval_hours': 24
                }
            }
        }

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)

        print(f"Default memory configuration saved to: {save_path}")

    def get_config(self) -> MemoryConfig:
        """Get the current configuration, loading it if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config

    def reload_config(self) -> MemoryConfig:
        """Force reload the configuration from file."""
        self._config = None
        return self.load_config()

    def validate_config(self, config: MemoryConfig) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Vector config validation
        if config.vector.enabled:
            if config.vector.dimension < 1 or config.vector.dimension > 2048:
                issues.append("Vector dimension must be between 1 and 2048")

            if config.vector.similarity_threshold < 0 or config.vector.similarity_threshold > 1:
                issues.append("Vector similarity threshold must be between 0 and 1")

            if config.vector.inference_mode not in ['remote', 'local', 'dynamic', 'ollama']:
                issues.append("Vector inference mode must be 'remote', 'local', 'dynamic', or 'ollama'")

        # Graph config validation
        if config.graph.enabled:
            if config.graph.max_concepts_per_message < 1:
                issues.append("Max concepts per message must be at least 1")

            if config.graph.concept_confidence_threshold < 0 or config.graph.concept_confidence_threshold > 1:
                issues.append("Concept confidence threshold must be between 0 and 1")

        # Update config validation
        if config.updates.update_interval < 1:
            issues.append("Update interval must be at least 1")

        if config.updates.max_batch_size < 1:
            issues.append("Max batch size must be at least 1")

        # Retention config validation
        if config.retention.ephemeral_retention_hours < 1:
            issues.append("Ephemeral retention hours must be at least 1")

        return issues