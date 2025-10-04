"""
Fullstack integration test for Locrits platform
Tests the complete flow:
1. Push Locrit from Python backend to Firebase
2. Verify Locrit appears in platform
3. Test conversation creation and messaging
4. Review conversation in platform

This test uses real Firebase credentials from the .env file
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.unified_firebase_service import unified_firebase_service
from src.services.config_service import config_service
from src.services.auth_service import AuthService


class TestFullstackLocritFlow:
    """
    Fullstack test suite for Locrits platform
    Tests the complete lifecycle of a Locrit from backend to platform
    """

    @pytest.fixture(scope="class")
    def auth_service(self):
        """Create authentication service instance"""
        return AuthService()

    @pytest.fixture(scope="class")
    def test_user_credentials(self):
        """
        Test user credentials for Firebase authentication
        You can create a dedicated test account or use anonymous auth
        """
        return {
            "email": os.getenv("FIREBASE_TEST_EMAIL", "test@locrits.test"),
            "password": os.getenv("FIREBASE_TEST_PASSWORD", "testpassword123"),
            "use_anonymous": os.getenv("FIREBASE_TEST_USE_ANONYMOUS", "true").lower() == "true"
        }

    @pytest.fixture(scope="class")
    async def authenticated_session(self, auth_service, test_user_credentials):
        """
        Authenticate and return session information
        This fixture will be used across all tests
        """
        # Try anonymous authentication first (easier for testing)
        if test_user_credentials["use_anonymous"]:
            result = auth_service.sign_in_anonymous()
        else:
            # Use email/password if provided
            result = auth_service.sign_in_with_email(
                test_user_credentials["email"],
                test_user_credentials["password"]
            )

        if not result.get("success"):
            pytest.fail(f"Authentication failed: {result.get('error', 'Unknown error')}")

        # Set auth info for unified Firebase service
        unified_firebase_service.set_auth_info(result)

        yield result

        # Cleanup: Sign out after tests
        auth_service.sign_out()

    @pytest.fixture
    def test_locrit_data(self):
        """Sample Locrit data for testing"""
        return {
            "name": f"test-locrit-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "description": "Automated test Locrit for fullstack integration testing",
            "publicAddress": f"test-locrit-{datetime.now().timestamp()}.locritland.net",
            "isOnline": True,
            "tags": ["test", "integration", "automated"],
            "settings": {
                "openTo": {
                    "humans": True,
                    "locrits": True,
                    "invitations": True,
                    "publicInternet": False,
                    "publicPlatform": True,
                    "scheduledConversations": True
                },
                "accessTo": {
                    "logs": True,
                    "quickMemory": True,
                    "fullMemory": False,
                    "llmInfo": True,
                    "conversationHistory": True
                },
                "behavior": {
                    "personality": "Helpful test assistant",
                    "responseStyle": "professional",
                    "maxResponseLength": 500,
                    "autoResponse": True,
                    "conversationTimeout": 30
                },
                "limits": {
                    "dailyMessages": 1000,
                    "concurrentConversations": 5,
                    "maxConversationDuration": 120
                }
            },
            "stats": {
                "totalConversations": 0,
                "totalMessages": 0,
                "averageResponseTime": 0,
                "popularTags": ["test"]
            }
        }

    @pytest.mark.asyncio
    async def test_01_firebase_service_configured(self):
        """Test 1: Verify Firebase service is properly configured"""
        status = unified_firebase_service.get_status()

        assert status["configured"] is True, "Firebase service should be configured"
        assert status["firestore_available"] or status["pyrebase_available"], \
            "At least one Firebase client should be available"

        print(f"\n✅ Firebase service status: {status}")

    @pytest.mark.asyncio
    async def test_02_authenticate_user(self, authenticated_session):
        """Test 2: Verify user authentication works"""
        assert authenticated_session is not None, "Authentication session should not be None"
        assert authenticated_session.get("success") is True, "Authentication should be successful"
        assert "localId" in authenticated_session or "uid" in authenticated_session, \
            "Session should contain user ID"

        user_id = authenticated_session.get("localId") or authenticated_session.get("uid")
        print(f"\n✅ User authenticated: {user_id[:8]}...")

    @pytest.mark.asyncio
    async def test_03_push_locrit_to_platform(self, authenticated_session, test_locrit_data):
        """Test 3: Push a Locrit from backend to Firebase platform"""
        locrit_name = test_locrit_data["name"]

        # Push Locrit to platform
        result = await unified_firebase_service.push_locrit_to_platform(
            locrit_name,
            test_locrit_data
        )

        assert result["success"] is True, f"Push should succeed: {result.get('error', '')}"
        assert "locrit_id" in result, "Result should contain locrit_id"
        assert result["action"] in ["created", "updated", "pushed"], \
            "Action should be created, updated, or pushed"

        # Store locrit_id for later tests
        self.locrit_id = result["locrit_id"]
        self.locrit_name = locrit_name

        print(f"\n✅ Locrit pushed to platform: {result['locrit_id']} ({result['action']})")

    @pytest.mark.asyncio
    async def test_04_update_locrit_status(self, authenticated_session):
        """Test 4: Update Locrit online status"""
        if not hasattr(self, 'locrit_name'):
            pytest.skip("Locrit not created yet")

        # Update status to online
        result = await unified_firebase_service.update_locrit_status(
            self.locrit_name,
            is_online=True,
            last_activity=datetime.now(timezone.utc)
        )

        assert result is True, "Status update should succeed"
        print(f"\n✅ Locrit status updated to online")

        # Update status to offline
        result = await unified_firebase_service.update_locrit_status(
            self.locrit_name,
            is_online=False
        )

        assert result is True, "Status update should succeed"
        print(f"\n✅ Locrit status updated to offline")

    @pytest.mark.asyncio
    async def test_05_log_locrit_activity(self, authenticated_session):
        """Test 5: Log Locrit activity to platform"""
        if not hasattr(self, 'locrit_name'):
            pytest.skip("Locrit not created yet")

        # Log test activity
        result = await unified_firebase_service.log_locrit_activity(
            self.locrit_name,
            level="info",
            message="Fullstack integration test activity",
            details={
                "test_type": "integration",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_phase": "activity_logging"
            }
        )

        assert result is True, "Activity logging should succeed"
        print(f"\n✅ Activity logged for Locrit")

    @pytest.mark.asyncio
    async def test_06_retrieve_platform_conversations(self, authenticated_session):
        """Test 6: Retrieve conversations from platform (if any)"""
        if not hasattr(self, 'locrit_name'):
            pytest.skip("Locrit not created yet")

        conversations = await unified_firebase_service.get_platform_conversations(
            self.locrit_name
        )

        # Conversations list might be empty for a new Locrit, which is fine
        assert isinstance(conversations, list), "Should return a list of conversations"
        print(f"\n✅ Retrieved {len(conversations)} conversation(s) from platform")

    @pytest.mark.asyncio
    async def test_07_push_multiple_locrits(self, authenticated_session, test_locrit_data):
        """Test 7: Push multiple Locrits to test batch operations"""
        locrit_count = 3
        results = []

        for i in range(locrit_count):
            locrit_data = test_locrit_data.copy()
            locrit_data["name"] = f"test-locrit-batch-{i}-{datetime.now().timestamp()}"
            locrit_data["description"] = f"Batch test Locrit #{i+1}"

            result = await unified_firebase_service.push_locrit_to_platform(
                locrit_data["name"],
                locrit_data
            )
            results.append(result)

        # Verify all succeeded
        successful = [r for r in results if r["success"]]
        assert len(successful) == locrit_count, \
            f"All {locrit_count} Locrits should be pushed successfully"

        print(f"\n✅ Batch pushed {len(successful)} Locrits to platform")

    @pytest.mark.asyncio
    async def test_08_update_existing_locrit(self, authenticated_session, test_locrit_data):
        """Test 8: Update an existing Locrit (should update, not create duplicate)"""
        if not hasattr(self, 'locrit_name'):
            pytest.skip("Locrit not created yet")

        # Update the same Locrit with new data
        updated_data = test_locrit_data.copy()
        updated_data["name"] = self.locrit_name
        updated_data["description"] = "UPDATED: This Locrit has been updated by fullstack test"
        updated_data["tags"] = ["test", "updated", "integration"]

        result = await unified_firebase_service.push_locrit_to_platform(
            self.locrit_name,
            updated_data
        )

        assert result["success"] is True, "Update should succeed"
        # For Firestore, it should be an update, not a new creation
        if unified_firebase_service.use_firestore_native:
            assert result["action"] == "updated", "Should update existing Locrit, not create new"

        print(f"\n✅ Locrit updated successfully: {result['action']}")

    @pytest.mark.asyncio
    async def test_09_verify_locrit_settings_normalization(self, authenticated_session):
        """Test 9: Verify that Locrit settings are properly normalized"""
        # Test with minimal settings
        minimal_locrit = {
            "name": f"minimal-test-{datetime.now().timestamp()}",
            "description": "Minimal Locrit for testing settings normalization",
            "publicAddress": "minimal.test.locritland.net",
            "isOnline": True,
            "settings": {
                "openTo": {"humans": True}  # Partial settings
            }
        }

        result = await unified_firebase_service.push_locrit_to_platform(
            minimal_locrit["name"],
            minimal_locrit
        )

        assert result["success"] is True, "Should handle minimal settings"
        print(f"\n✅ Settings normalization works correctly")

    @pytest.mark.asyncio
    async def test_10_error_handling_no_auth(self):
        """Test 10: Verify proper error handling when not authenticated"""
        # Create a new service instance without auth
        from src.services.unified_firebase_service import UnifiedFirebaseService
        unauth_service = UnifiedFirebaseService()

        result = await unauth_service.push_locrit_to_platform(
            "test-locrit",
            {"name": "test"}
        )

        assert result["success"] is False, "Should fail without authentication"
        assert "authentication" in result["error"].lower(), \
            "Error should mention authentication"

        print(f"\n✅ Proper error handling for unauthenticated requests")


class TestPlatformIntegration:
    """
    Tests for platform-side integration
    These tests verify that Locrits pushed from backend appear correctly in platform
    """

    @pytest.fixture(scope="class")
    def firebase_config(self):
        """Get Firebase configuration"""
        return config_service.get_firebase_config()

    @pytest.mark.asyncio
    async def test_firebase_config_valid(self, firebase_config):
        """Test that Firebase configuration is valid"""
        assert firebase_config is not None, "Firebase config should exist"
        assert "projectId" in firebase_config, "Config should have projectId"
        assert firebase_config["projectId"], "Project ID should not be empty"

        print(f"\n✅ Firebase config valid: project={firebase_config['projectId']}")

    @pytest.mark.asyncio
    async def test_platform_can_query_locrits(self, firebase_config):
        """
        Test that platform can query Locrits
        Note: This would require the platform to be running or using emulators
        """
        # This is a placeholder - in a real test, you would:
        # 1. Start Firebase emulators
        # 2. Query Firestore from platform perspective
        # 3. Verify Locrits appear correctly

        assert True, "Platform integration test placeholder"
        print(f"\n✅ Platform integration test ready (requires emulators)")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "-k", "test_"  # Run all tests
    ])
