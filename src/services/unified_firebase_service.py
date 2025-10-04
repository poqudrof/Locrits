"""
Unified Firebase Service for Locrits Platform
Consolidates all Firebase operations and provides a single interface for
synchronizing data between the backend server and the platform.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import os

try:
    from google.cloud import firestore
    from google.cloud.firestore import DocumentReference, DocumentSnapshot
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

try:
    import pyrebase
    PYREBASE_AVAILABLE = True
except ImportError:
    PYREBASE_AVAILABLE = False

from .config_service import config_service


class UnifiedFirebaseService:
    """
    Unified Firebase service that handles all platform synchronization.
    Automatically chooses between google-cloud-firestore (preferred) or pyrebase
    based on availability and configuration.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = None
        self.firebase_app = None
        self.user_id = None
        self.auth_token = None
        self.use_firestore_native = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase connection with fallback options"""
        firebase_config = config_service.get_firebase_config()

        if not firebase_config or not firebase_config.get('projectId'):
            self.logger.warning("⚠️ Firebase configuration missing")
            return

        # Try native Firestore first (preferred)
        if FIRESTORE_AVAILABLE:
            try:
                project_id = firebase_config['projectId']
                self.db = firestore.Client(project=project_id)
                self.use_firestore_native = True
                self.logger.info("🔥 Native Firestore client initialized")
                return
            except Exception as e:
                self.logger.warning(f"⚠️ Native Firestore init failed: {e}")

        # Fallback to pyrebase
        if PYREBASE_AVAILABLE:
            try:
                self.firebase_app = pyrebase.initialize_app(firebase_config)
                self.db = self.firebase_app.database()
                self.use_firestore_native = False
                self.logger.info("🔥 Pyrebase client initialized")
                return
            except Exception as e:
                self.logger.warning(f"⚠️ Pyrebase init failed: {e}")

        self.logger.error("❌ No Firebase client could be initialized")

    def set_auth_info(self, auth_info: Dict[str, Any]):
        """Set authentication information"""
        self.user_id = auth_info.get('localId') or auth_info.get('uid')
        self.auth_token = auth_info.get('idToken')
        if self.user_id:
            self.logger.info(f"🔑 Auth set for user: {self.user_id[:8]}...")

    async def push_locrit_to_platform(self, locrit_name: str, locrit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push a Locrit from the server to the platform.
        Creates or updates the Locrit in the global locrits collection.
        """
        if not self.is_configured():
            return {"success": False, "error": "Firebase not configured"}

        if not self.user_id:
            return {"success": False, "error": "User authentication required"}

        try:
            # Prepare Locrit data for platform
            platform_locrit = {
                "name": locrit_name,
                "description": locrit_data.get('description', f"Locrit: {locrit_name}"),
                "publicAddress": locrit_data.get('publicAddress', f"{locrit_name}.locritland.net"),
                "ownerId": self.user_id,
                "isOnline": locrit_data.get('isOnline', True),
                "lastSeen": datetime.now(timezone.utc),
                "settings": self._extract_locrit_settings(locrit_data),
                "stats": self._extract_locrit_stats(locrit_data),
                "tags": locrit_data.get('tags', []),
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }

            if self.use_firestore_native:
                return await self._push_locrit_firestore(locrit_name, platform_locrit)
            else:
                return await self._push_locrit_pyrebase(locrit_name, platform_locrit)

        except Exception as e:
            self.logger.error(f"❌ Error pushing Locrit {locrit_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _push_locrit_firestore(self, locrit_name: str, locrit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Push Locrit using native Firestore client"""
        try:
            # Check if Locrit already exists
            locrits_ref = self.db.collection('locrits')
            query = locrits_ref.where('name', '==', locrit_name).where('ownerId', '==', self.user_id)
            existing = list(query.stream())

            if existing:
                # Update existing Locrit
                doc_ref = existing[0].reference
                doc_ref.update({
                    **locrit_data,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                })
                locrit_id = existing[0].id
                self.logger.info(f"✅ Updated Locrit {locrit_name} in platform")
            else:
                # Create new Locrit
                doc_ref = locrits_ref.add({
                    **locrit_data,
                    "createdAt": firestore.SERVER_TIMESTAMP,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                })[1]
                locrit_id = doc_ref.id
                self.logger.info(f"✅ Created Locrit {locrit_name} in platform")

            # Also update user's local locrits collection
            await self._sync_to_user_locrits(locrit_name, locrit_data)

            return {
                "success": True,
                "locrit_id": locrit_id,
                "action": "updated" if existing else "created"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _push_locrit_pyrebase(self, locrit_name: str, locrit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Push Locrit using pyrebase (fallback)"""
        try:
            # Convert datetime objects to ISO strings for pyrebase
            locrit_data_serialized = self._serialize_for_pyrebase(locrit_data)

            # For pyrebase, we'll use a deterministic path based on user and locrit name
            locrit_path = f"locrits/{self.user_id}_{locrit_name}"

            # Push to Firebase Realtime Database
            self.db.child(locrit_path).set(locrit_data_serialized, self.auth_token)

            # Also update user's locrits collection
            user_locrit_path = f"users/{self.user_id}/locrits/{locrit_name}"
            self.db.child(user_locrit_path).set(locrit_data_serialized, self.auth_token)

            self.logger.info(f"✅ Pushed Locrit {locrit_name} via pyrebase")
            return {"success": True, "locrit_id": f"{self.user_id}_{locrit_name}", "action": "pushed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_to_user_locrits(self, locrit_name: str, locrit_data: Dict[str, Any]):
        """Sync Locrit to user's personal locrits subcollection"""
        try:
            if self.use_firestore_native:
                user_locrit_ref = self.db.collection('users').document(self.user_id).collection('locrits').document(locrit_name)
                user_locrit_ref.set({
                    "name": locrit_name,
                    "settings": locrit_data.get('settings', {}),
                    "lastModified": firestore.SERVER_TIMESTAMP,
                    "syncStatus": "synced",
                    "source": "server"
                })
            else:
                # Pyrebase version handled in _push_locrit_pyrebase
                pass

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to sync to user locrits: {e}")

    async def update_locrit_status(self, locrit_name: str, is_online: bool, last_activity: Optional[datetime] = None):
        """Update Locrit online status and last activity"""
        if not self.is_configured() or not self.user_id:
            return False

        try:
            update_data = {
                "isOnline": is_online,
                "lastSeen": last_activity or datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }

            if self.use_firestore_native:
                locrits_ref = self.db.collection('locrits')
                query = locrits_ref.where('name', '==', locrit_name).where('ownerId', '==', self.user_id)
                docs = list(query.stream())

                for doc in docs:
                    doc.reference.update({
                        **update_data,
                        "lastSeen": firestore.SERVER_TIMESTAMP,
                        "updatedAt": firestore.SERVER_TIMESTAMP
                    })
            else:
                # Pyrebase update
                locrit_path = f"locrits/{self.user_id}_{locrit_name}"
                self.db.child(locrit_path).update(
                    self._serialize_for_pyrebase(update_data),
                    self.auth_token
                )

            self.logger.info(f"📡 Updated {locrit_name} status: {'online' if is_online else 'offline'}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to update Locrit status: {e}")
            return False

    async def log_locrit_activity(self, locrit_name: str, level: str, message: str, details: Optional[Dict] = None):
        """Log Locrit activity to the platform"""
        if not self.is_configured() or not self.user_id:
            return False

        try:
            log_data = {
                "locritId": f"{self.user_id}_{locrit_name}",
                "timestamp": datetime.now(timezone.utc),
                "level": level,
                "category": "server",
                "message": message,
                "details": details or {},
                "userId": self.user_id
            }

            if self.use_firestore_native:
                self.db.collection('locrit_logs').add({
                    **log_data,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
            else:
                # Pyrebase logging
                log_path = f"locrit_logs/{self.user_id}_{locrit_name}"
                self.db.child(log_path).push(
                    self._serialize_for_pyrebase(log_data),
                    self.auth_token
                )

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to log activity: {e}")
            return False

    async def get_platform_conversations(self, locrit_name: str) -> List[Dict[str, Any]]:
        """Get conversations from the platform involving this Locrit"""
        if not self.is_configured():
            return []

        try:
            locrit_id = f"{self.user_id}_{locrit_name}"

            if self.use_firestore_native:
                conversations_ref = self.db.collection('conversations')
                query = conversations_ref.where('participants.id', 'array_contains', locrit_id)
                docs = query.stream()

                conversations = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    conversations.append(data)

                return conversations
            else:
                # Pyrebase implementation would go here
                return []

        except Exception as e:
            self.logger.error(f"❌ Failed to get conversations: {e}")
            return []

    def _extract_locrit_settings(self, locrit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize Locrit settings"""
        settings = locrit_data.get('settings', {})

        # Ensure all required settings exist with defaults
        return {
            "openTo": {
                "humans": settings.get('openTo', {}).get('humans', True),
                "locrits": settings.get('openTo', {}).get('locrits', True),
                "invitations": settings.get('openTo', {}).get('invitations', True),
                "publicInternet": settings.get('openTo', {}).get('publicInternet', False),
                "publicPlatform": settings.get('openTo', {}).get('publicPlatform', True),
                "scheduledConversations": settings.get('openTo', {}).get('scheduledConversations', True)
            },
            "accessTo": {
                "logs": settings.get('accessTo', {}).get('logs', True),
                "quickMemory": settings.get('accessTo', {}).get('quickMemory', True),
                "fullMemory": settings.get('accessTo', {}).get('fullMemory', False),
                "llmInfo": settings.get('accessTo', {}).get('llmInfo', True),
                "conversationHistory": settings.get('accessTo', {}).get('conversationHistory', True)
            },
            "behavior": {
                "personality": settings.get('behavior', {}).get('personality', "Helpful and friendly"),
                "responseStyle": settings.get('behavior', {}).get('responseStyle', "casual"),
                "maxResponseLength": settings.get('behavior', {}).get('maxResponseLength', 500),
                "autoResponse": settings.get('behavior', {}).get('autoResponse', True),
                "conversationTimeout": settings.get('behavior', {}).get('conversationTimeout', 30)
            },
            "limits": {
                "dailyMessages": settings.get('limits', {}).get('dailyMessages', 1000),
                "concurrentConversations": settings.get('limits', {}).get('concurrentConversations', 5),
                "maxConversationDuration": settings.get('limits', {}).get('maxConversationDuration', 120)
            }
        }

    def _extract_locrit_stats(self, locrit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize Locrit statistics"""
        stats = locrit_data.get('stats', {})

        return {
            "totalConversations": stats.get('totalConversations', 0),
            "totalMessages": stats.get('totalMessages', 0),
            "averageResponseTime": stats.get('averageResponseTime', 0),
            "lastActiveDate": datetime.now(timezone.utc),
            "popularTags": stats.get('popularTags', [])
        }

    def _serialize_for_pyrebase(self, data: Any) -> Any:
        """Convert data for pyrebase compatibility (no datetime objects)"""
        if isinstance(data, dict):
            return {k: self._serialize_for_pyrebase(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_pyrebase(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def is_configured(self) -> bool:
        """Check if Firebase is properly configured"""
        return self.db is not None

    def get_status(self) -> Dict[str, Any]:
        """Get Firebase service status"""
        return {
            "configured": self.is_configured(),
            "client_type": "firestore" if self.use_firestore_native else "pyrebase",
            "authenticated": self.user_id is not None,
            "user_id": self.user_id[:8] + "..." if self.user_id else None,
            "firestore_available": FIRESTORE_AVAILABLE,
            "pyrebase_available": PYREBASE_AVAILABLE
        }


# Global instance
unified_firebase_service = UnifiedFirebaseService()