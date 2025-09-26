"""
Service de synchronisation des Locrits entre local et serveur
Gestion bidirectionnelle avec résolution de conflits par timestamp
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import httpx
from .config_service import config_service


class SyncService:
    """Service de synchronisation des Locrits local ↔ serveur"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.central_server_url = config_service.get('central_server.url', 'https://central.locrit.com')
        self.sync_enabled = config_service.get('central_server.enabled', True)
        self.auto_sync_interval = config_service.get('central_server.discovery_interval', 300)
        self.user_id = None
        self.auth_token = None
        
    def set_auth_info(self, auth_info: dict):
        """Configure l'authentification pour la sync"""
        self.user_id = auth_info.get('localId') or auth_info.get('uid')
        self.auth_token = auth_info.get('idToken')
        self.logger.info(f"🔑 Auth configurée pour sync - User: {self.user_id[:8]}...")

    async def sync_all_locrits(self) -> Dict[str, str]:
        """Synchronise tous les Locrits (montée + descente)"""
        if not self.sync_enabled:
            self.logger.info("📴 Synchronisation désactivée")
            return {"status": "disabled"}
            
        if not self.user_id:
            self.logger.warning("⚠️ Pas d'authentification pour la sync")
            return {"status": "no_auth"}
            
        results = {
            "upload_results": [],
            "download_results": [],
            "conflicts_resolved": [],
            "errors": []
        }
        
        try:
            # 1. Uploader les Locrits locaux vers le serveur
            self.logger.info("⬆️ Upload des Locrits locaux...")
            upload_results = await self._upload_local_locrits()
            results["upload_results"] = upload_results
            
            # 2. Télécharger les Locrits du serveur
            self.logger.info("⬇️ Download des Locrits serveur...")
            download_results = await self._download_server_locrits()
            results["download_results"] = download_results
            
            # 3. Résoudre les conflits
            self.logger.info("🔀 Résolution des conflits...")
            conflicts = await self._resolve_conflicts()
            results["conflicts_resolved"] = conflicts
            
            # 4. Sauvegarder la configuration locale
            config_service.save_config()
            
            self.logger.info("✅ Synchronisation terminée avec succès")
            return {"status": "success", **results}
            
        except Exception as e:
            error_msg = f"❌ Erreur de synchronisation: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            return {"status": "error", **results}

    async def _upload_local_locrits(self) -> List[Dict]:
        """Upload les Locrits locaux vers le serveur"""
        local_locrits = config_service.list_locrits()
        upload_results = []
        
        for locrit_name in local_locrits:
            try:
                locrit_config = config_service.get_locrit_settings(locrit_name)
                
                # Préparer les données pour l'API
                sync_data = {
                    "name": locrit_name,
                    "config": locrit_config,
                    "user_id": self.user_id,
                    "last_modified": locrit_config.get('updated_at', locrit_config.get('created_at')),
                    "action": "upsert"
                }
                
                # Envoyer au serveur
                result = await self._send_to_server("/api/locrits/sync", sync_data)
                
                if result.get("success"):
                    self.logger.info(f"⬆️ ✅ {locrit_name} uploadé")
                    upload_results.append({"name": locrit_name, "status": "uploaded"})
                    
                    # Mettre à jour le timestamp de sync local
                    locrit_config['last_synced'] = self._get_current_timestamp()
                    config_service.update_locrit_settings(locrit_name, locrit_config)
                else:
                    error_msg = f"⬆️ ❌ {locrit_name}: {result.get('error', 'Erreur inconnue')}"
                    self.logger.warning(error_msg)
                    upload_results.append({"name": locrit_name, "status": "error", "error": error_msg})
                    
            except Exception as e:
                error_msg = f"⬆️ ❌ {locrit_name}: {str(e)}"
                self.logger.error(error_msg)
                upload_results.append({"name": locrit_name, "status": "error", "error": error_msg})
                
        return upload_results

    async def _download_server_locrits(self) -> List[Dict]:
        """Download les Locrits du serveur"""
        download_results = []
        
        try:
            # Récupérer la liste des Locrits du serveur pour cet utilisateur
            server_data = await self._get_from_server(f"/api/locrits/user/{self.user_id}")
            
            if not server_data.get("success"):
                return [{"status": "error", "error": "Impossible de récupérer les Locrits serveur"}]
                
            server_locrits = server_data.get("locrits", [])
            
            for server_locrit in server_locrits:
                try:
                    locrit_name = server_locrit["name"]
                    server_config = server_locrit["config"]
                    server_timestamp = server_locrit.get("last_modified")
                    
                    # Vérifier si le Locrit existe localement
                    local_config = config_service.get_locrit_settings(locrit_name)
                    
                    if local_config is None:
                        # Nouveau Locrit du serveur -> Ajouter localement
                        self.logger.info(f"⬇️ 🆕 Nouveau Locrit: {locrit_name}")
                        config_service.update_locrit_settings(locrit_name, server_config)
                        download_results.append({"name": locrit_name, "status": "downloaded_new"})
                        
                    else:
                        # Locrit existe -> Vérifier les timestamps pour conflit
                        local_timestamp = local_config.get('updated_at', local_config.get('created_at'))
                        
                        if self._is_server_newer(server_timestamp, local_timestamp):
                            self.logger.info(f"⬇️ 🔄 Mise à jour depuis serveur: {locrit_name}")
                            config_service.update_locrit_settings(locrit_name, server_config)
                            download_results.append({"name": locrit_name, "status": "updated_from_server"})
                        else:
                            self.logger.info(f"⬇️ ⏭️ Version locale plus récente: {locrit_name}")
                            download_results.append({"name": locrit_name, "status": "local_newer"})
                            
                except Exception as e:
                    error_msg = f"⬇️ ❌ {locrit_name}: {str(e)}"
                    self.logger.error(error_msg)
                    download_results.append({"name": locrit_name, "status": "error", "error": error_msg})
                    
        except Exception as e:
            error_msg = f"⬇️ ❌ Erreur générale de download: {str(e)}"
            self.logger.error(error_msg)
            download_results.append({"status": "error", "error": error_msg})
            
        return download_results

    async def _resolve_conflicts(self) -> List[Dict]:
        """Résout les conflits en utilisant le timestamp le plus récent"""
        # Pour l'instant, la résolution est déjà faite dans download/upload
        # Cette méthode peut être étendue pour des conflits plus complexes
        return []

    def _is_server_newer(self, server_timestamp: str, local_timestamp: str) -> bool:
        """Compare les timestamps pour déterminer si le serveur est plus récent"""
        try:
            if not server_timestamp or not local_timestamp:
                return False
                
            server_dt = datetime.fromisoformat(server_timestamp.replace('Z', '+00:00'))
            local_dt = datetime.fromisoformat(local_timestamp.replace('Z', '+00:00'))
            
            return server_dt > local_dt
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur de comparaison timestamp: {e}")
            return False

    async def _send_to_server(self, endpoint: str, data: dict) -> dict:
        """Envoie des données au serveur central"""
        try:
            url = f"{self.central_server_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}" if self.auth_token else None
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_from_server(self, endpoint: str) -> dict:
        """Récupère des données du serveur central"""
        try:
            url = f"{self.central_server_url}{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.auth_token}" if self.auth_token else None
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO avec timezone"""
        return datetime.now(timezone.utc).isoformat()

    async def auto_sync_loop(self):
        """Boucle de synchronisation automatique"""
        if not self.sync_enabled:
            return
            
        self.logger.info(f"🔄 Synchronisation automatique démarrée (intervalle: {self.auto_sync_interval}s)")
        
        while self.sync_enabled:
            try:
                await asyncio.sleep(self.auto_sync_interval)
                
                if self.user_id:  # Synchroniser seulement si authentifié
                    self.logger.info("🔄 Synchronisation automatique...")
                    await self.sync_all_locrits()
                    
            except asyncio.CancelledError:
                self.logger.info("🔄 Synchronisation automatique arrêtée")
                break
            except Exception as e:
                self.logger.error(f"🔄 ❌ Erreur sync auto: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute avant de réessayer

    def start_auto_sync(self):
        """Démarre la synchronisation automatique en arrière-plan"""
        if self.sync_enabled and self.user_id:
            asyncio.create_task(self.auto_sync_loop())

    def stop_auto_sync(self):
        """Arrête la synchronisation automatique"""
        self.sync_enabled = False


# Instance globale du service de synchronisation
sync_service = SyncService()
