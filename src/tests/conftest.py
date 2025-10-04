"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Configure asyncio for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"🗂️  TEMP DIR CREATED: {temp_dir}")
        yield temp_dir
        print(f"🗂️  TEMP DIR CLEANED UP: {temp_dir}")


@pytest.fixture
def mock_firebase_config():
    """Mock Firebase configuration"""
    return {
        'projectId': 'test-locrit-project',
        'apiKey': 'test-api-key-123',
        'authDomain': 'test-locrit-project.firebaseapp.com',
        'storageBucket': 'test-locrit-project.appspot.com',
        'messagingSenderId': '123456789',
        'appId': '1:123456789:web:abcdef123456'
    }


@pytest.fixture
def mock_user_auth():
    """Mock user authentication data"""
    return {
        'localId': 'test-user-id-123',
        'email': 'test@example.com',
        'displayName': 'Test User',
        'idToken': 'mock-id-token-123',
        'refreshToken': 'mock-refresh-token-123',
        'expiresIn': '3600'
    }


@pytest.fixture
def mock_locrit_data():
    """Mock Locrit data for testing"""
    return {
        'name': 'Test Locrit',
        'description': 'A Locrit for testing purposes',
        'isOnline': True,
        'publicAddress': 'test-locrit.locritland.net',
        'settings': {
            'openTo': {
                'humans': True,
                'locrits': True,
                'invitations': True,
                'publicInternet': False,
                'publicPlatform': True
            },
            'accessTo': {
                'logs': True,
                'quickMemory': True,
                'fullMemory': False,
                'llmInfo': True
            },
            'behavior': {
                'personality': 'Helpful and friendly',
                'responseStyle': 'casual',
                'maxResponseLength': 500,
                'autoResponse': True,
                'conversationTimeout': 30
            },
            'limits': {
                'dailyMessages': 1000,
                'concurrentConversations': 5,
                'maxConversationDuration': 120
            }
        },
        'stats': {
            'totalConversations': 42,
            'totalMessages': 1337,
            'averageResponseTime': 2.5,
            'popularTags': ['helpful', 'friendly', 'testing']
        },
        'tags': ['testing', 'ai', 'assistant']
    }


@pytest.fixture
def mock_conversation_data():
    """Mock conversation data for testing"""
    return {
        'id': 'test-conversation-id',
        'title': 'Test Conversation',
        'type': 'user-locrit',
        'participants': [
            {
                'id': 'test-user-id',
                'name': 'Test User',
                'type': 'user'
            },
            {
                'id': 'test-locrit-id',
                'name': 'Test Locrit',
                'type': 'locrit'
            }
        ],
        'topic': 'Testing conversation functionality',
        'duration': 120,
        'status': 'active',
        'isActive': True,
        'isScheduled': False,
        'createdBy': 'test-user-id',
        'metadata': {
            'messageCount': 10,
            'averageResponseTime': 2.0,
            'topics': ['testing', 'ai'],
            'sentiment': 'positive',
            'language': 'en'
        }
    }


@pytest.fixture
def mock_message_data():
    """Mock message data for testing"""
    return {
        'id': 'test-message-id',
        'conversationId': 'test-conversation-id',
        'content': 'Hello, this is a test message!',
        'sender': 'user',
        'senderName': 'Test User',
        'senderId': 'test-user-id',
        'isRead': False,
        'messageType': 'text',
        'metadata': {
            'emotion': 'neutral',
            'context': 'testing',
            'processingTime': 150
        }
    }


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client"""
    client = Mock()

    # Mock collection and document methods
    client.collection.return_value = Mock()
    client.collection.return_value.document.return_value = Mock()
    client.collection.return_value.add.return_value = (None, Mock(id='mock-doc-id'))

    # Mock query methods
    client.collection.return_value.where.return_value = Mock()
    client.collection.return_value.where.return_value.where.return_value = Mock()
    client.collection.return_value.where.return_value.order_by.return_value = Mock()
    client.collection.return_value.where.return_value.limit.return_value = Mock()

    return client


@pytest.fixture
def mock_pyrebase_app():
    """Mock pyrebase app and database"""
    app = Mock()
    db = Mock()
    app.database.return_value = db

    # Mock database operations
    db.child.return_value = Mock()
    db.child.return_value.set.return_value = None
    db.child.return_value.update.return_value = None
    db.child.return_value.push.return_value = {'name': 'mock-push-id'}
    db.child.return_value.get.return_value = Mock(val=lambda: {})

    return app, db


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'FIREBASE_PROJECT_ID': 'test-project',
        'FIREBASE_API_KEY': 'test-api-key',
        'FIREBASE_AUTH_DOMAIN': 'test.firebaseapp.com',
        'FIREBASE_STORAGE_BUCKET': 'test.appspot.com',
        'FIREBASE_MESSAGING_SENDER_ID': '123456789',
        'FIREBASE_APP_ID': '1:123456789:web:abc123'
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_config_file(temp_directory):
    """Create a mock config file for testing"""
    config_data = {
        'locrits': {
            'test_locrit': {
                'name': 'Test Locrit',
                'description': 'A test Locrit',
                'settings': {
                    'openTo': {'humans': True},
                    'accessTo': {'logs': True}
                }
            }
        },
        'firebase': {
            'projectId': 'test-project',
            'apiKey': 'test-api-key'
        },
        'auth': {
            'user_id': 'test-user',
            'email': 'test@example.com'
        },
        'app': {
            'debug': True,
            'log_level': 'DEBUG'
        }
    }

    config_file = os.path.join(temp_directory, 'config.json')
    with open(config_file, 'w') as f:
        import json
        json.dump(config_data, f, indent=2)

    return config_file


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests"""
    import logging

    # Reduce logging noise during tests
    logging.getLogger('src').setLevel(logging.WARNING)
    logging.getLogger('firebase').setLevel(logging.ERROR)
    logging.getLogger('google').setLevel(logging.ERROR)

    yield

    # Reset logging after tests
    logging.getLogger('src').setLevel(logging.INFO)


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing"""
    from datetime import datetime, timezone

    fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    with patch('src.services.unified_firebase_service.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield fixed_time


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "firebase: mark test as requiring Firebase"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add unit marker to all tests in test_* files unless marked otherwise
        if 'test_' in item.nodeid and not any(
            marker.name in ['integration', 'slow', 'firebase']
            for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)

        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid.lower() for keyword in ['integration', 'e2e', 'full']):
            item.add_marker(pytest.mark.slow)


# Custom assertions
class CustomAssertions:
    """Custom assertion helpers for testing"""

    @staticmethod
    def assert_firebase_config_valid(config):
        """Assert that Firebase config has required fields"""
        required_fields = ['projectId', 'apiKey', 'authDomain', 'storageBucket']
        for field in required_fields:
            assert field in config, f"Missing required Firebase config field: {field}"
            assert config[field], f"Firebase config field {field} is empty"

    @staticmethod
    def assert_locrit_data_valid(locrit_data):
        """Assert that Locrit data has required structure"""
        required_fields = ['name', 'description', 'settings']
        for field in required_fields:
            assert field in locrit_data, f"Missing required Locrit field: {field}"

        # Check settings structure
        settings = locrit_data['settings']
        assert 'openTo' in settings, "Missing openTo settings"
        assert 'accessTo' in settings, "Missing accessTo settings"

    @staticmethod
    def assert_conversation_data_valid(conversation_data):
        """Assert that conversation data has required structure"""
        required_fields = ['title', 'type', 'participants', 'status']
        for field in required_fields:
            assert field in conversation_data, f"Missing required conversation field: {field}"

        # Check participants structure
        participants = conversation_data['participants']
        assert isinstance(participants, list), "Participants must be a list"
        assert len(participants) > 0, "Conversation must have participants"


@pytest.fixture
def assert_helpers():
    """Provide custom assertion helpers"""
    return CustomAssertions


# Error simulation helpers
@pytest.fixture
def firebase_error_simulator():
    """Helper to simulate Firebase errors"""
    class FirebaseErrorSimulator:
        @staticmethod
        def permission_denied():
            from google.cloud.exceptions import PermissionDenied
            return PermissionDenied("Permission denied")

        @staticmethod
        def not_found():
            from google.cloud.exceptions import NotFound
            return NotFound("Document not found")

        @staticmethod
        def network_error():
            import requests
            return requests.exceptions.ConnectionError("Network error")

        @staticmethod
        def quota_exceeded():
            from google.cloud.exceptions import ResourceExhausted
            return ResourceExhausted("Quota exceeded")

    return FirebaseErrorSimulator


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Helper for performance testing"""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            return self.elapsed()

        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_under(self, max_seconds):
            elapsed = self.elapsed()
            assert elapsed is not None, "Timer not properly started/stopped"
            assert elapsed < max_seconds, f"Operation took {elapsed:.3f}s, expected under {max_seconds}s"

    return PerformanceTimer()