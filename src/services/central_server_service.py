"""
Service de serveur central pour la découverte et coordination des locrits.
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class CentralServerService:
    """Service pour communiquer avec un serveur central de coordination des locrits."""
    
    def __init__(self, server_url: str = "https://locrit-central.example.com"):
        """
        Initialise le service de serveur central.
        
        Args:
            server_url: URL du serveur central
        """
        self.server_url = server_url.rstrip('/')
        self.locrit_id = None
        self.registration_token = None
        self.last_heartbeat = None
        self.is_registered = False
    
    async def register_locrit(self, identity: Dict[str, Any], public_url: str = None) -> dict:
        """
        Enregistre ce locrit auprès du serveur central.
        
        Args:
            identity: Identité du locrit
            public_url: URL publique (si tunneling actif)
            
        Returns:
            Résultat de l'enregistrement
        """
        try:
            registration_data = {
                "identity": identity,
                "public_url": public_url,
                "capabilities": [
                    "chat",
                    "search", 
                    "memory",
                    "api"
                ],
                "registered_at": datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/register",
                    json=registration_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.locrit_id = result.get("locrit_id")
                    self.registration_token = result.get("token")
                    self.is_registered = True
                    
                    return {
                        "success": True,
                        "message": "Enregistrement réussi",
                        "locrit_id": self.locrit_id
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur serveur: {response.status_code}"
                    }
                    
        except httpx.RequestError as e:
            return {
                "success": False,
                "message": f"Serveur central non disponible: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'enregistrement: {e}"
            }
    
    async def discover_locrits(self, search_query: str = None) -> List[Dict[str, Any]]:
        """
        Découvre des locrits disponibles via le serveur central.
        
        Args:
            search_query: Critère de recherche optionnel
            
        Returns:
            Liste des locrits disponibles
        """
        if not self.is_registered:
            return []
        
        try:
            params = {}
            if search_query:
                params["q"] = search_query
            
            headers = {"Authorization": f"Bearer {self.registration_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/discover",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json().get("locrits", [])
                else:
                    print(f"Erreur découverte: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Erreur lors de la découverte: {e}")
            return []
    
    async def send_heartbeat(self, status: Dict[str, Any]) -> bool:
        """
        Envoie un signal de vie au serveur central.
        
        Args:
            status: Statut actuel du locrit
            
        Returns:
            Succès du heartbeat
        """
        if not self.is_registered:
            return False
        
        try:
            heartbeat_data = {
                "locrit_id": self.locrit_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {"Authorization": f"Bearer {self.registration_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/heartbeat",
                    json=heartbeat_data,
                    headers=headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    self.last_heartbeat = datetime.now()
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Erreur heartbeat: {e}")
            return False
    
    async def unregister(self) -> bool:
        """
        Désenregistre ce locrit du serveur central.
        
        Returns:
            Succès du désenregistrement
        """
        if not self.is_registered:
            return True
        
        try:
            headers = {"Authorization": f"Bearer {self.registration_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.server_url}/unregister",
                    headers=headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    self.is_registered = False
                    self.locrit_id = None
                    self.registration_token = None
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Erreur désenregistrement: {e}")
            return False
    
    def should_send_heartbeat(self, interval_minutes: int = 5) -> bool:
        """
        Vérifie s'il faut envoyer un heartbeat.
        
        Args:
            interval_minutes: Intervalle en minutes
            
        Returns:
            True si un heartbeat est nécessaire
        """
        if not self.is_registered or not self.last_heartbeat:
            return True
        
        elapsed = datetime.now() - self.last_heartbeat
        return elapsed > timedelta(minutes=interval_minutes)
