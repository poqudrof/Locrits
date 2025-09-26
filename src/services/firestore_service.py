"""
Service de synchronisation Firestore natif pour les Locrits
Utilise google-cloud-firestore directement pour plus de simplicité
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import os
from google.cloud import firestore
from .config_service import config_service


class FirestoreService:
    """Service de synchronisation des Locrits avec Firestore natif"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = None
        self.user_id = None
        self.auth_token = None
        self._initialize_firestore()
        
    def _initialize_firestore(self):
        """Initialise la connexion Firestore"""
        try:
            # Configuration Firebase depuis .env
            firebase_config = config_service.get_firebase_config()
            
            # Vérifier que la config Firebase est complète
            required_keys = ['projectId']
            missing_keys = [key for key in required_keys if not firebase_config.get(key)]
            if missing_keys:
                self.logger.warning(f"⚠️ Configuration Firebase incomplète - Clés manquantes: {missing_keys}")
                return
            
            project_id = firebase_config['projectId']
            
            # Créer le client Firestore directement
            # Pour le développement, on utilise les credentials par défaut ou l'émulateur
            self.db = firestore.Client(project=project_id)
            self.logger.info("🔥 Firestore initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Firestore: {str(e)}")
            self.logger.info("💡 Vérifiez la configuration Firebase ou utilisez l'émulateur Firestore")
            self.db = None

    def set_auth_info(self, auth_info: dict):
        """Configure l'authentification pour Firestore"""
        self.user_id = auth_info.get('localId') or auth_info.get('uid')
        self.auth_token = auth_info.get('idToken')
        self.logger.info(f"🔑 Auth configurée pour Firestore - User: {self.user_id[:8]}...")

    async def sync_all_locrits(self) -> Dict[str, str]:
        """Synchronise tous les Locrits avec Firestore"""
        if not self.db:
            self.logger.warning("⚠️ Firestore non initialisé")
            return {"status": "firestore_not_initialized", "message": "Configuration Firestore requise"}
            
        if not self.user_id:
            self.logger.warning("⚠️ Pas d'authentification pour Firestore")
            return {"status": "no_auth", "message": "Authentification requise"}
            
        results = {
            "uploaded": [],
            "downloaded": [],
            "conflicts_resolved": [],
            "errors": [],
            "status": "success"
        }
        
        try:
            # 1. Uploader les Locrits locaux vers Firestore
            local_locrits = config_service.list_locrits()
            self.logger.info(f"📤 Upload de {len(local_locrits)} Locrit(s) vers Firestore")
            
            for locrit_name in local_locrits:
                try:
                    result = await self._upload_locrit_to_firestore(locrit_name)
                    if result["success"]:
                        results["uploaded"].append(locrit_name)
                        self.logger.info(f"✅ {locrit_name} uploadé vers Firestore")
                    else:
                        results["errors"].append(f"{locrit_name}: {result['error']}")
                        self.logger.error(f"❌ Échec upload {locrit_name}: {result['error']}")
                        
                except Exception as e:
                    error_msg = f"Upload {locrit_name}: {str(e)}"
                    results["errors"].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            
            # 2. Télécharger les Locrits depuis Firestore (si il y en a d'autres)
            try:
                firestore_locrits = await self._get_locrits_from_firestore()
                for locrit_name, locrit_data in firestore_locrits.items():
                    if locrit_name not in local_locrits:
                        # Nouveau Locrit depuis Firestore
                        await self._download_locrit_from_firestore(locrit_name, locrit_data)
                        results["downloaded"].append(locrit_name)
                        self.logger.info(f"📥 {locrit_name} téléchargé depuis Firestore")
                        
            except Exception as e:
                error_msg = f"Download depuis Firestore: {str(e)}"
                results["errors"].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
                
            self.logger.info(f"🔄 Sync terminée - Up: {len(results['uploaded'])}, Down: {len(results['downloaded'])}, Erreurs: {len(results['errors'])}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Erreur générale de synchronisation: {str(e)}")
            return {"status": "error", "message": str(e), "errors": [str(e)]}

    async def _upload_locrit_to_firestore(self, locrit_name: str) -> Dict[str, any]:
        """Upload un Locrit vers Firestore"""
        try:
            # Récupérer les données du Locrit local
            locrit_settings = config_service.get_locrit_settings(locrit_name)
            if not locrit_settings:
                return {"success": False, "error": "Locrit introuvable en local"}
            
            # Préparer les données pour Firestore
            firestore_data = {
                "name": locrit_name,
                "settings": locrit_settings,
                "user_id": self.user_id,
                "last_modified": datetime.now(timezone.utc),
                "created_at": locrit_settings.get('created_at', datetime.now(timezone.utc).isoformat())
            }
            
            # Chemin dans Firestore: users/{user_id}/locrits/{locrit_name}
            doc_ref = self.db.collection('users').document(self.user_id).collection('locrits').document(locrit_name)
            
            # Uploader vers Firestore
            doc_ref.set(firestore_data)
            
            self.logger.info(f"📤 {locrit_name} uploadé vers Firestore")
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_locrits_from_firestore(self) -> Dict[str, dict]:
        """Récupère tous les Locrits de l'utilisateur depuis Firestore"""
        try:
            # Référence à la collection des Locrits de l'utilisateur
            locrits_ref = self.db.collection('users').document(self.user_id).collection('locrits')
            
            # Récupérer tous les documents
            docs = locrits_ref.stream()
            
            locrits_data = {}
            for doc in docs:
                if doc.exists:
                    locrits_data[doc.id] = doc.to_dict()
                    
            return locrits_data
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lecture Firestore: {str(e)}")
            return {}

    async def _download_locrit_from_firestore(self, locrit_name: str, locrit_data: dict):
        """Télécharge un Locrit depuis Firestore vers local"""
        try:
            settings = locrit_data.get('settings', {})
            
            # Sauvegarder en local
            config_service.update_locrit_settings(locrit_name, settings)
            config_service.save_config()
            
            self.logger.info(f"📥 {locrit_name} téléchargé et sauvé en local")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur download {locrit_name}: {str(e)}")

    async def delete_locrit_from_firestore(self, locrit_name: str) -> bool:
        """Supprime un Locrit de Firestore"""
        try:
            if not self.db or not self.user_id:
                return False
                
            doc_ref = self.db.collection('users').document(self.user_id).collection('locrits').document(locrit_name)
            doc_ref.delete()
            
            self.logger.info(f"🗑️ {locrit_name} supprimé de Firestore")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur suppression Firestore {locrit_name}: {str(e)}")
            return False

    def is_configured(self) -> bool:
        """Vérifie si Firestore est correctement configuré"""
        return self.db is not None

    def get_status(self) -> Dict[str, any]:
        """Retourne le statut de la synchronisation Firestore"""
        return {
            "firestore_connected": self.db is not None,
            "authenticated": self.user_id is not None and self.auth_token is not None,
            "user_id": self.user_id[:8] + "..." if self.user_id else None
        }


# Instance globale
firestore_service = FirestoreService()
