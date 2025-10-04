"""
Tests for the unified Firebase service
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import json

from src.services.unified_firebase_service import UnifiedFirebaseService
from src.services.config_service import config_service


class TestUnifiedFirebaseService:
    """Test cases for UnifiedFirebaseService"""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing"""
        with patch('src.services.unified_firebase_service.config_service') as mock_config:
            mock_config.get_firebase_config.return_value = {
                'projectId': 'test-project',
                'apiKey': 'test-api-key',
                'authDomain': 'test.firebaseapp.com',
                'storageBucket': 'test.appspot.com'
            }
            service = UnifiedFirebaseService()
            return service

    @pytest.fixture
    def mock_firestore_client(self):
        """Mock Firestore client"""
        with patch('src.services.unified_firebase_service.firestore') as mock_firestore:
            mock_client = Mock()
            mock_firestore.Client.return_value = mock_client
            mock_firestore.SERVER_TIMESTAMP = 'server_timestamp'
            yield mock_client

    @pytest.fixture
    def mock_pyrebase_app(self):
        """Mock pyrebase app"""
        with patch('src.services.unified_firebase_service.pyrebase') as mock_pyrebase:
            mock_app = Mock()
            mock_db = Mock()
            mock_app.database.return_value = mock_db
            mock_pyrebase.initialize_app.return_value = mock_app
            yield mock_app, mock_db

    def test_init_with_firestore_native(self, mock_firestore_client):
        """Test initialization with native Firestore client"""
        with patch('src.services.unified_firebase_service.FIRESTORE_AVAILABLE', True):
            with patch('src.services.unified_firebase_service.config_service') as mock_config:
                mock_config.get_firebase_config.return_value = {
                    'projectId': 'test-project'
                }

                service = UnifiedFirebaseService()

                assert service.use_firestore_native is True
                assert service.db is not None

    def test_init_with_pyrebase_fallback(self, mock_pyrebase_app):
        """Test initialization with pyrebase fallback"""
        mock_app, mock_db = mock_pyrebase_app

        with patch('src.services.unified_firebase_service.FIRESTORE_AVAILABLE', False):
            with patch('src.services.unified_firebase_service.PYREBASE_AVAILABLE', True):
                with patch('src.services.unified_firebase_service.config_service') as mock_config:
                    mock_config.get_firebase_config.return_value = {
                        'projectId': 'test-project'
                    }

                    service = UnifiedFirebaseService()

                    assert service.use_firestore_native is False
                    assert service.db is not None

    def test_init_no_firebase_available(self):
        """Test initialization when no Firebase client is available"""
        with patch('src.services.unified_firebase_service.FIRESTORE_AVAILABLE', False):
            with patch('src.services.unified_firebase_service.PYREBASE_AVAILABLE', False):
                with patch('src.services.unified_firebase_service.config_service') as mock_config:
                    mock_config.get_firebase_config.return_value = {
                        'projectId': 'test-project'
                    }

                    service = UnifiedFirebaseService()

                    assert service.db is None

    def test_set_auth_info(self, service):
        """Test setting authentication information"""
        auth_info = {
            'localId': 'test-user-id',
            'idToken': 'test-id-token'
        }

        service.set_auth_info(auth_info)

        assert service.user_id == 'test-user-id'
        assert service.auth_token == 'test-id-token'

    @pytest.mark.asyncio
    async def test_push_locrit_to_platform_firestore(self, service, mock_firestore_client):
        """Test pushing Locrit to platform using Firestore"""
        service.use_firestore_native = True
        service.db = mock_firestore_client
        service.user_id = 'test-user-id'

        # Mock Firestore operations
        mock_collection = Mock()
        mock_query = Mock()
        mock_firestore_client.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.stream.return_value = []  # No existing Locrit

        mock_doc_ref = Mock()
        mock_doc_ref.id = 'new-locrit-id'
        mock_collection.add.return_value = (None, mock_doc_ref)

        locrit_data = {
            'name': 'Test Locrit',
            'description': 'A test Locrit',
            'isOnline': True,
            'settings': {
                'openTo': {'humans': True, 'locrits': True}
            }
        }

        result = await service.push_locrit_to_platform('test-locrit', locrit_data)

        assert result['success'] is True
        assert result['locrit_id'] == 'new-locrit-id'
        assert result['action'] == 'created'

    @pytest.mark.asyncio
    async def test_push_locrit_to_platform_pyrebase(self, service, mock_pyrebase_app):
        """Test pushing Locrit to platform using pyrebase"""
        mock_app, mock_db = mock_pyrebase_app
        service.use_firestore_native = False
        service.db = mock_db
        service.user_id = 'test-user-id'
        service.auth_token = 'test-token'

        locrit_data = {
            'name': 'Test Locrit',
            'description': 'A test Locrit',
            'isOnline': True
        }

        result = await service.push_locrit_to_platform('test-locrit', locrit_data)

        assert result['success'] is True
        assert result['locrit_id'] == 'test-user-id_test-locrit'
        assert result['action'] == 'pushed'

        # Verify pyrebase calls
        mock_db.child.assert_called()
        mock_db.child.return_value.set.assert_called()

    @pytest.mark.asyncio
    async def test_push_locrit_no_auth(self, service):
        """Test pushing Locrit without authentication"""
        service.db = Mock()
        service.user_id = None

        result = await service.push_locrit_to_platform('test-locrit', {})

        assert result['success'] is False
        assert 'authentication' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_push_locrit_no_db(self, service):
        """Test pushing Locrit without database connection"""
        service.db = None

        result = await service.push_locrit_to_platform('test-locrit', {})

        assert result['success'] is False
        assert 'not configured' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_update_locrit_status_firestore(self, service, mock_firestore_client):
        """Test updating Locrit status using Firestore"""
        service.use_firestore_native = True
        service.db = mock_firestore_client
        service.user_id = 'test-user-id'

        # Mock Firestore query
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.reference = Mock()

        mock_firestore_client.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]

        result = await service.update_locrit_status(
            'test-locrit',
            True,
            datetime.now(timezone.utc)
        )

        assert result is True
        mock_doc.reference.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_locrit_status_pyrebase(self, service, mock_pyrebase_app):
        """Test updating Locrit status using pyrebase"""
        mock_app, mock_db = mock_pyrebase_app
        service.use_firestore_native = False
        service.db = mock_db
        service.user_id = 'test-user-id'
        service.auth_token = 'test-token'

        result = await service.update_locrit_status('test-locrit', False)

        assert result is True
        mock_db.child.assert_called()
        mock_db.child.return_value.update.assert_called()

    @pytest.mark.asyncio
    async def test_log_locrit_activity_firestore(self, service, mock_firestore_client):
        """Test logging Locrit activity using Firestore"""
        service.use_firestore_native = True
        service.db = mock_firestore_client
        service.user_id = 'test-user-id'

        mock_collection = Mock()
        mock_firestore_client.collection.return_value = mock_collection

        result = await service.log_locrit_activity(
            'test-locrit',
            'info',
            'Test log message',
            {'key': 'value'}
        )

        assert result is True
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_locrit_activity_pyrebase(self, service, mock_pyrebase_app):
        """Test logging Locrit activity using pyrebase"""
        mock_app, mock_db = mock_pyrebase_app
        service.use_firestore_native = False
        service.db = mock_db
        service.user_id = 'test-user-id'
        service.auth_token = 'test-token'

        result = await service.log_locrit_activity(
            'test-locrit',
            'warning',
            'Test warning message'
        )

        assert result is True
        mock_db.child.assert_called()
        mock_db.child.return_value.push.assert_called()

    @pytest.mark.asyncio
    async def test_get_platform_conversations_firestore(self, service, mock_firestore_client):
        """Test getting platform conversations using Firestore"""
        service.use_firestore_native = True
        service.db = mock_firestore_client
        service.user_id = 'test-user-id'

        # Mock conversation document
        mock_doc = Mock()
        mock_doc.id = 'conv-1'
        mock_doc.to_dict.return_value = {
            'title': 'Test Conversation',
            'participants': [{'id': 'test-user-id_test-locrit', 'name': 'Test Locrit'}]
        }

        mock_collection = Mock()
        mock_query = Mock()
        mock_firestore_client.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]

        result = await service.get_platform_conversations('test-locrit')

        assert len(result) == 1
        assert result[0]['id'] == 'conv-1'
        assert result[0]['title'] == 'Test Conversation'

    def test_extract_locrit_settings(self, service):
        """Test extracting and normalizing Locrit settings"""
        input_settings = {
            'openTo': {'humans': True},
            'accessTo': {'logs': False},
            'behavior': {'personality': 'Friendly'}
        }

        result = service._extract_locrit_settings({'settings': input_settings})

        # Should have all required keys with defaults
        assert 'openTo' in result
        assert 'accessTo' in result
        assert 'behavior' in result
        assert 'limits' in result

        # Should preserve provided values
        assert result['openTo']['humans'] is True
        assert result['accessTo']['logs'] is False
        assert result['behavior']['personality'] == 'Friendly'

        # Should provide defaults for missing values
        assert result['openTo']['locrits'] is True  # Default
        assert result['limits']['dailyMessages'] == 1000  # Default

    def test_extract_locrit_stats(self, service):
        """Test extracting Locrit statistics"""
        input_stats = {
            'totalConversations': 5,
            'totalMessages': 150
        }

        result = service._extract_locrit_stats({'stats': input_stats})

        assert result['totalConversations'] == 5
        assert result['totalMessages'] == 150
        assert result['averageResponseTime'] == 0  # Default
        assert 'lastActiveDate' in result
        assert isinstance(result['popularTags'], list)

    def test_serialize_for_pyrebase(self, service):
        """Test data serialization for pyrebase compatibility"""
        test_data = {
            'string': 'test',
            'number': 42,
            'boolean': True,
            'datetime': datetime.now(timezone.utc),
            'list': [1, 2, datetime.now(timezone.utc)],
            'dict': {
                'nested_datetime': datetime.now(timezone.utc),
                'nested_string': 'test'
            }
        }

        result = service._serialize_for_pyrebase(test_data)

        assert result['string'] == 'test'
        assert result['number'] == 42
        assert result['boolean'] is True
        assert isinstance(result['datetime'], str)
        assert isinstance(result['list'][2], str)
        assert isinstance(result['dict']['nested_datetime'], str)
        assert result['dict']['nested_string'] == 'test'

    def test_is_configured(self, service):
        """Test configuration check"""
        # Not configured
        service.db = None
        assert service.is_configured() is False

        # Configured
        service.db = Mock()
        assert service.is_configured() is True

    def test_get_status(self, service):
        """Test getting service status"""
        service.db = Mock()
        service.use_firestore_native = True
        service.user_id = 'test-user-id'

        status = service.get_status()

        assert status['configured'] is True
        assert status['client_type'] == 'firestore'
        assert status['authenticated'] is True
        assert 'test-user' in status['user_id']

    @pytest.mark.asyncio
    async def test_error_handling_in_push_locrit(self, service, mock_firestore_client):
        """Test error handling in push_locrit_to_platform"""
        service.use_firestore_native = True
        service.db = mock_firestore_client
        service.user_id = 'test-user-id'

        # Mock Firestore to raise exception
        mock_firestore_client.collection.side_effect = Exception("Firestore error")

        result = await service.push_locrit_to_platform('test-locrit', {})

        assert result['success'] is False
        assert 'Firestore error' in result['error']

    @pytest.mark.asyncio
    async def test_error_handling_in_update_status(self, service):
        """Test error handling in update_locrit_status"""
        service.use_firestore_native = True
        service.db = Mock()
        service.user_id = 'test-user-id'

        # Mock to raise exception
        service.db.collection.side_effect = Exception("Database error")

        result = await service.update_locrit_status('test-locrit', True)

        assert result is False

    @pytest.mark.asyncio
    async def test_error_handling_in_log_activity(self, service):
        """Test error handling in log_locrit_activity"""
        service.use_firestore_native = True
        service.db = Mock()
        service.user_id = 'test-user-id'

        # Mock to raise exception
        service.db.collection.side_effect = Exception("Logging error")

        result = await service.log_locrit_activity('test-locrit', 'error', 'Test')

        assert result is False


@pytest.fixture
def mock_config_service():
    """Mock config service for testing"""
    with patch('src.services.unified_firebase_service.config_service') as mock:
        mock.get_firebase_config.return_value = {
            'projectId': 'test-project',
            'apiKey': 'test-api-key'
        }
        yield mock


class TestUnifiedFirebaseServiceIntegration:
    """Integration tests for UnifiedFirebaseService"""

    @pytest.mark.asyncio
    async def test_full_locrit_lifecycle_firestore(self, mock_config_service):
        """Test complete Locrit lifecycle with Firestore"""
        with patch('src.services.unified_firebase_service.FIRESTORE_AVAILABLE', True):
            with patch('src.services.unified_firebase_service.firestore') as mock_firestore:
                # Setup mocks
                mock_client = Mock()
                mock_firestore.Client.return_value = mock_client
                mock_firestore.SERVER_TIMESTAMP = 'server_timestamp'

                service = UnifiedFirebaseService()
                service.set_auth_info({'localId': 'test-user', 'idToken': 'token'})

                # Mock Firestore operations for creation
                mock_collection = Mock()
                mock_query = Mock()
                mock_client.collection.return_value = mock_collection
                mock_collection.where.return_value = mock_query
                mock_query.where.return_value = mock_query
                mock_query.stream.return_value = []  # No existing

                mock_doc_ref = Mock()
                mock_doc_ref.id = 'new-locrit-id'
                mock_collection.add.return_value = (None, mock_doc_ref)

                # Create Locrit
                locrit_data = {
                    'name': 'Integration Test Locrit',
                    'description': 'Test Locrit for integration testing',
                    'isOnline': True
                }

                create_result = await service.push_locrit_to_platform('test-locrit', locrit_data)
                assert create_result['success'] is True

                # Update status
                mock_doc = Mock()
                mock_doc.reference = Mock()
                mock_query.stream.return_value = [mock_doc]

                update_result = await service.update_locrit_status('test-locrit', False)
                assert update_result is True

                # Log activity
                log_result = await service.log_locrit_activity(
                    'test-locrit', 'info', 'Integration test completed'
                )
                assert log_result is True

    @pytest.mark.asyncio
    async def test_full_locrit_lifecycle_pyrebase(self, mock_config_service):
        """Test complete Locrit lifecycle with pyrebase"""
        with patch('src.services.unified_firebase_service.FIRESTORE_AVAILABLE', False):
            with patch('src.services.unified_firebase_service.PYREBASE_AVAILABLE', True):
                with patch('src.services.unified_firebase_service.pyrebase') as mock_pyrebase:
                    # Setup mocks
                    mock_app = Mock()
                    mock_db = Mock()
                    mock_app.database.return_value = mock_db
                    mock_pyrebase.initialize_app.return_value = mock_app

                    service = UnifiedFirebaseService()
                    service.set_auth_info({'localId': 'test-user', 'idToken': 'token'})

                    # Create Locrit
                    locrit_data = {
                        'name': 'Integration Test Locrit',
                        'description': 'Test Locrit for integration testing',
                        'isOnline': True
                    }

                    create_result = await service.push_locrit_to_platform('test-locrit', locrit_data)
                    assert create_result['success'] is True

                    # Update status
                    update_result = await service.update_locrit_status('test-locrit', False)
                    assert update_result is True

                    # Log activity
                    log_result = await service.log_locrit_activity(
                        'test-locrit', 'info', 'Integration test completed'
                    )
                    assert log_result is True

                    # Verify pyrebase calls were made
                    assert mock_db.child.call_count >= 3  # At least 3 operations


if __name__ == '__main__':
    pytest.main([__file__])