"""
Tests for the config service
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, mock_open
from pathlib import Path

from src.services.config_service import ConfigService


class TestConfigService:
    """Test cases for ConfigService"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"🗂️  TEMP DIR CREATED: {temp_dir}")
            yield temp_dir
            print(f"🗂️  TEMP DIR CLEANED UP: {temp_dir}")

    @pytest.fixture
    def config_service(self, temp_config_dir):
        """Create a ConfigService instance with temporary directory"""
        service = ConfigService()
        service.config_file = os.path.join(temp_config_dir, 'config.json')
        service.config_dir = temp_config_dir
        return service

    def test_init_creates_default_config(self, config_service):
        """Test that initialization creates default config"""
        # Should create default config
        assert hasattr(config_service, 'config')
        assert 'locrits' in config_service.config
        assert 'firebase' in config_service.config
        assert 'auth' in config_service.config

    def test_load_config_file_not_exists(self, config_service):
        """Test loading config when file doesn't exist"""
        # Should load defaults
        config_service.load_config()
        assert config_service.config is not None
        assert 'locrits' in config_service.config

    def test_load_config_file_exists(self, config_service, temp_config_dir):
        """Test loading config from existing file"""
        # Create config file
        config_data = {
            'locrits': {'test_locrit': {'name': 'Test Locrit'}},
            'firebase': {'projectId': 'test-project'},
            'auth': {'user_id': 'test-user'}
        }

        config_file = os.path.join(temp_config_dir, 'config.json')
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config_service.load_config()

        assert config_service.config['locrits']['test_locrit']['name'] == 'Test Locrit'
        assert config_service.config['firebase']['projectId'] == 'test-project'

    def test_load_config_invalid_json(self, config_service, temp_config_dir):
        """Test loading config with invalid JSON"""
        # Create invalid JSON file
        config_file = os.path.join(temp_config_dir, 'config.json')
        with open(config_file, 'w') as f:
            f.write('invalid json content')

        # Should fall back to defaults
        config_service.load_config()
        assert config_service.config is not None
        assert 'locrits' in config_service.config

    def test_save_config(self, config_service, temp_config_dir):
        """Test saving configuration to file"""
        config_service.config['test_key'] = 'test_value'
        config_service.save_config()

        # Verify file was created and contains correct data
        config_file = os.path.join(temp_config_dir, 'config.json')
        assert os.path.exists(config_file)

        with open(config_file, 'r') as f:
            saved_config = json.load(f)

        assert saved_config['test_key'] == 'test_value'

    def test_save_config_directory_creation(self, temp_config_dir):
        """Test that save_config creates directory if it doesn't exist"""
        nested_dir = os.path.join(temp_config_dir, 'nested', 'config')
        config_service = ConfigService()
        config_service.config_file = os.path.join(nested_dir, 'config.json')
        config_service.config_dir = nested_dir

        config_service.save_config()

        assert os.path.exists(nested_dir)
        assert os.path.exists(config_service.config_file)

    def test_get_locrit_settings_exists(self, config_service):
        """Test getting settings for existing Locrit"""
        config_service.config['locrits']['test_locrit'] = {
            'name': 'Test Locrit',
            'settings': {'key': 'value'}
        }

        settings = config_service.get_locrit_settings('test_locrit')
        assert settings is not None
        assert settings['name'] == 'Test Locrit'
        assert settings['settings']['key'] == 'value'

    def test_get_locrit_settings_not_exists(self, config_service):
        """Test getting settings for non-existing Locrit"""
        settings = config_service.get_locrit_settings('nonexistent')
        assert settings is None

    def test_update_locrit_settings_new(self, config_service):
        """Test updating settings for new Locrit"""
        new_settings = {
            'name': 'New Locrit',
            'description': 'A new test Locrit'
        }

        config_service.update_locrit_settings('new_locrit', new_settings)

        assert 'new_locrit' in config_service.config['locrits']
        assert config_service.config['locrits']['new_locrit']['name'] == 'New Locrit'

    def test_update_locrit_settings_existing(self, config_service):
        """Test updating settings for existing Locrit"""
        # Set initial config
        config_service.config['locrits']['existing_locrit'] = {
            'name': 'Original Name',
            'description': 'Original Description'
        }

        # Update settings
        updated_settings = {
            'name': 'Updated Name',
            'new_field': 'new_value'
        }

        config_service.update_locrit_settings('existing_locrit', updated_settings)

        locrit_config = config_service.config['locrits']['existing_locrit']
        assert locrit_config['name'] == 'Updated Name'
        assert locrit_config['new_field'] == 'new_value'
        # Should preserve existing fields not in update
        assert locrit_config['description'] == 'Original Description'

    def test_delete_locrit(self, config_service):
        """Test deleting a Locrit"""
        # Add Locrit first
        config_service.config['locrits']['to_delete'] = {'name': 'Delete Me'}

        assert 'to_delete' in config_service.config['locrits']

        config_service.delete_locrit('to_delete')

        assert 'to_delete' not in config_service.config['locrits']

    def test_delete_locrit_not_exists(self, config_service):
        """Test deleting non-existing Locrit (should not raise error)"""
        initial_locrits = dict(config_service.config['locrits'])

        config_service.delete_locrit('nonexistent')

        # Should not change anything
        assert config_service.config['locrits'] == initial_locrits

    def test_list_locrits_empty(self, config_service):
        """Test listing Locrits when none exist"""
        config_service.config['locrits'] = {}
        locrits = config_service.list_locrits()
        assert locrits == []

    def test_list_locrits_with_data(self, config_service):
        """Test listing Locrits with data"""
        config_service.config['locrits'] = {
            'locrit1': {'name': 'Locrit 1'},
            'locrit2': {'name': 'Locrit 2'},
            'locrit3': {'name': 'Locrit 3'}
        }

        locrits = config_service.list_locrits()

        assert len(locrits) == 3
        assert 'locrit1' in locrits
        assert 'locrit2' in locrits
        assert 'locrit3' in locrits

    def test_get_firebase_config_complete(self, config_service):
        """Test getting complete Firebase config"""
        config_service.config['firebase'] = {
            'projectId': 'test-project',
            'apiKey': 'test-api-key',
            'authDomain': 'test.firebaseapp.com',
            'storageBucket': 'test.appspot.com'
        }

        firebase_config = config_service.get_firebase_config()

        assert firebase_config['projectId'] == 'test-project'
        assert firebase_config['apiKey'] == 'test-api-key'
        assert firebase_config['authDomain'] == 'test.firebaseapp.com'
        assert firebase_config['storageBucket'] == 'test.appspot.com'

    def test_get_firebase_config_from_env(self, config_service):
        """Test getting Firebase config from environment variables"""
        with patch.dict(os.environ, {
            'FIREBASE_PROJECT_ID': 'env-project',
            'FIREBASE_API_KEY': 'env-api-key',
            'FIREBASE_AUTH_DOMAIN': 'env.firebaseapp.com',
            'FIREBASE_STORAGE_BUCKET': 'env.appspot.com'
        }):
            firebase_config = config_service.get_firebase_config()

            assert firebase_config['projectId'] == 'env-project'
            assert firebase_config['apiKey'] == 'env-api-key'
            assert firebase_config['authDomain'] == 'env.firebaseapp.com'
            assert firebase_config['storageBucket'] == 'env.appspot.com'

    def test_get_firebase_config_mixed_sources(self, config_service):
        """Test Firebase config from mixed sources (env overrides config)"""
        # Set config file values
        config_service.config['firebase'] = {
            'projectId': 'config-project',
            'apiKey': 'config-api-key'
        }

        # Set some env values
        with patch.dict(os.environ, {
            'FIREBASE_PROJECT_ID': 'env-project',
            'FIREBASE_STORAGE_BUCKET': 'env.appspot.com'
        }):
            firebase_config = config_service.get_firebase_config()

            # Env should override config
            assert firebase_config['projectId'] == 'env-project'
            # Config should be used when env not set
            assert firebase_config['apiKey'] == 'config-api-key'
            # Env should be used
            assert firebase_config['storageBucket'] == 'env.appspot.com'

    def test_update_firebase_config(self, config_service):
        """Test updating Firebase configuration"""
        new_firebase_config = {
            'projectId': 'updated-project',
            'apiKey': 'updated-api-key'
        }

        config_service.update_firebase_config(new_firebase_config)

        assert config_service.config['firebase']['projectId'] == 'updated-project'
        assert config_service.config['firebase']['apiKey'] == 'updated-api-key'

    def test_get_auth_config(self, config_service):
        """Test getting authentication configuration"""
        config_service.config['auth'] = {
            'user_id': 'test-user',
            'email': 'test@example.com'
        }

        auth_config = config_service.get_auth_config()

        assert auth_config['user_id'] == 'test-user'
        assert auth_config['email'] == 'test@example.com'

    def test_update_auth_config(self, config_service):
        """Test updating authentication configuration"""
        new_auth_config = {
            'user_id': 'new-user',
            'email': 'new@example.com',
            'token': 'new-token'
        }

        config_service.update_auth_config(new_auth_config)

        assert config_service.config['auth']['user_id'] == 'new-user'
        assert config_service.config['auth']['email'] == 'new@example.com'
        assert config_service.config['auth']['token'] == 'new-token'

    def test_clear_auth_config(self, config_service):
        """Test clearing authentication configuration"""
        config_service.config['auth'] = {
            'user_id': 'test-user',
            'email': 'test@example.com',
            'token': 'test-token'
        }

        config_service.clear_auth_config()

        assert config_service.config['auth'] == {}

    def test_get_app_config(self, config_service):
        """Test getting application-wide configuration"""
        config_service.config['app'] = {
            'debug': True,
            'log_level': 'INFO'
        }

        app_config = config_service.get_app_config()

        assert app_config['debug'] is True
        assert app_config['log_level'] == 'INFO'

    def test_update_app_config(self, config_service):
        """Test updating application configuration"""
        new_app_config = {
            'debug': False,
            'theme': 'dark'
        }

        config_service.update_app_config(new_app_config)

        assert config_service.config['app']['debug'] is False
        assert config_service.config['app']['theme'] == 'dark'

    def test_config_file_permissions(self, config_service, temp_config_dir):
        """Test that config file is created with appropriate permissions"""
        config_service.save_config()

        config_file = os.path.join(temp_config_dir, 'config.json')
        file_stat = os.stat(config_file)

        # File should be readable and writable by owner
        assert file_stat.st_mode & 0o600

    def test_backup_and_restore_config(self, config_service, temp_config_dir):
        """Test configuration backup and restore functionality"""
        # Set some initial config
        config_service.config['test_data'] = 'original_value'
        config_service.save_config()

        # Create backup
        backup_file = os.path.join(temp_config_dir, 'config_backup.json')
        with open(config_service.config_file, 'r') as src:
            with open(backup_file, 'w') as dst:
                dst.write(src.read())

        # Modify config
        config_service.config['test_data'] = 'modified_value'
        config_service.save_config()

        # Restore from backup
        with open(backup_file, 'r') as src:
            with open(config_service.config_file, 'w') as dst:
                dst.write(src.read())

        # Reload config
        config_service.load_config()

        assert config_service.config['test_data'] == 'original_value'

    def test_config_validation(self, config_service):
        """Test configuration validation"""
        # Valid config should pass
        valid_config = {
            'locrits': {},
            'firebase': {'projectId': 'test'},
            'auth': {}
        }

        # This should not raise an exception
        config_service.config = valid_config
        config_service.save_config()

    def test_concurrent_config_access(self, config_service):
        """Test thread-safe configuration access"""
        import threading
        import time

        results = []
        errors = []

        def update_config(thread_id):
            try:
                for i in range(10):
                    config_service.update_locrit_settings(f'locrit_{thread_id}_{i}', {
                        'name': f'Locrit {thread_id}-{i}',
                        'thread_id': thread_id,
                        'iteration': i
                    })
                    time.sleep(0.001)  # Small delay to encourage race conditions
                results.append(f'Thread {thread_id} completed')
            except Exception as e:
                errors.append(f'Thread {thread_id} error: {e}')

        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=update_config, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 3

        # Should have all Locrits created
        assert len(config_service.list_locrits()) == 30  # 3 threads * 10 iterations


class TestConfigServiceIntegration:
    """Integration tests for ConfigService"""

    def test_full_locrit_lifecycle(self, temp_config_dir):
        """Test complete Locrit lifecycle through config service"""
        config_service = ConfigService()
        config_service.config_file = os.path.join(temp_config_dir, 'config.json')
        config_service.config_dir = temp_config_dir

        # Create Locrit
        locrit_settings = {
            'name': 'Integration Test Locrit',
            'description': 'A Locrit for integration testing',
            'settings': {
                'openTo': {'humans': True, 'locrits': True},
                'accessTo': {'logs': True, 'memory': False}
            }
        }

        config_service.update_locrit_settings('integration_locrit', locrit_settings)

        # Verify creation
        assert 'integration_locrit' in config_service.list_locrits()
        retrieved_settings = config_service.get_locrit_settings('integration_locrit')
        assert retrieved_settings['name'] == 'Integration Test Locrit'

        # Update Locrit
        updated_settings = {
            'name': 'Updated Integration Test Locrit',
            'new_field': 'new_value'
        }
        config_service.update_locrit_settings('integration_locrit', updated_settings)

        # Verify update
        retrieved_settings = config_service.get_locrit_settings('integration_locrit')
        assert retrieved_settings['name'] == 'Updated Integration Test Locrit'
        assert retrieved_settings['new_field'] == 'new_value'
        # Should preserve existing nested settings
        assert retrieved_settings['settings']['openTo']['humans'] is True

        # Save and reload
        config_service.save_config()

        new_service = ConfigService()
        new_service.config_file = config_service.config_file
        new_service.load_config()

        # Verify persistence
        assert 'integration_locrit' in new_service.list_locrits()
        persisted_settings = new_service.get_locrit_settings('integration_locrit')
        assert persisted_settings['name'] == 'Updated Integration Test Locrit'

        # Delete Locrit
        new_service.delete_locrit('integration_locrit')
        assert 'integration_locrit' not in new_service.list_locrits()


if __name__ == '__main__':
    pytest.main([__file__])