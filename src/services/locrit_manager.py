"""
Gestionnaire principal pour coordonner tous les services de Locrit.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from .ollama_service import OllamaService
from .search_service import SearchService
from .memory_service import MemoryService
from .api_service import APIService
from .tunneling_service import TunnelingService
from .central_server_service import CentralServerService


class LocritManager:
    """Gestionnaire principal qui coordonne tous les services."""
    
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434):
        """
        Initialise le gestionnaire avec tous les services.
        
        Args:
            ollama_host: Adresse du serveur Ollama
            ollama_port: Port du serveur Ollama
        """
        self.ollama = OllamaService(ollama_host, ollama_port)
        self.search = SearchService()
        self.memory = MemoryService()
        self.api = APIService(locrit_manager=self)
        self.tunneling = TunnelingService()
        self.central_server = CentralServerService()
        
        self.identity = {
            "name": "Locrit",
            "description": "Un assistant intelligent avec mémoire et capacités de recherche",
            "personality": "Utile, curieux et capable d'apprendre"
        }
        
        self.current_session_id = None
        self.is_initialized = False
        self.server_mode = False
        self.auth_info = None
    
    async def initialize(self) -> Dict[str, bool]:
        """
        Initialise tous les services.
        
        Returns:
            Dictionnaire avec le statut d'initialisation de chaque service
        """
        results = {}
        
        # Initialiser la mémoire
        results["memory"] = await self.memory.initialize()
        
        # Connecter à Ollama
        results["ollama"] = await self.ollama.connect()
        
        # Le service de recherche n'a pas besoin d'initialisation spéciale
        results["search"] = True
        
        self.is_initialized = all(results.values())
        results["overall"] = self.is_initialized
        
        return results
    
    def set_auth_info(self, auth_info: Dict[str, Any]):
        """
        Définit les informations d'authentification Firebase.
        
        Args:
            auth_info: Dictionnaire contenant user_id, email, auth_type, token
        """
        self.auth_info = auth_info
        
        # Mettre à jour l'identité avec les infos utilisateur
        if auth_info:
            user_identifier = auth_info.get('email', 'anonyme')
            self.identity.update({
                "user_id": auth_info.get('user_id'),
                "user_email": user_identifier,
                "auth_type": auth_info.get('auth_type', 'unknown')
            })
    
    def get_auth_info(self) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations d'authentification actuelles.
        
        Returns:
            Dictionnaire avec les infos d'auth ou None si non connecté
        """
        return self.auth_info
    
    async def get_status(self) -> dict:
        """
        Retourne le statut détaillé de tous les services.
        
        Returns:
            Dictionnaire avec le statut de chaque service
        """
        ollama_status = await self.ollama.check_connection()
        memory_stats = await self.memory.get_stats()
        
        return {
            "ollama": {
                "connected": ollama_status["connected"],
                "model": ollama_status.get("model", "Aucun"),
                "version": ollama_status.get("version", "Inconnue")
            },
            "memory": {
                "messages": memory_stats["message_count"],
                "sessions": memory_stats["session_count"],
                "embeddings": memory_stats.get("embedding_count", 0)
            },
            "search": {
                "available": True,
                "provider": "DuckDuckGo"
            },
            "api": {
                "running": self.api.is_running if hasattr(self.api, 'is_running') else False,
                "port": self.api.port if hasattr(self.api, 'port') else None
            },
            "tunneling": {
                "active": self.tunneling.is_active() if hasattr(self.tunneling, 'is_active') else False,
                "url": self.tunneling.get_public_url() if hasattr(self.tunneling, 'get_public_url') else None
            },
            "identity": self.identity,
            "server_mode": self.server_mode,
            "session_id": self.current_session_id
        }
    
    async def chat(self, message: str, use_memory: bool = True) -> str:
        """
        Traite un message de chat avec le Locrit.
        
        Args:
            message: Message de l'utilisateur
            use_memory: Utiliser la mémoire pour le contexte
            
        Returns:
            Réponse du Locrit
        """
        if not self.is_initialized:
            return "❌ Locrit n'est pas encore initialisé. Veuillez vérifier la connexion."
        
        try:
            # Sauvegarder le message utilisateur
            if use_memory and self.memory.is_initialized:
                await self.memory.save_message(
                    role="user", 
                    content=message, 
                    session_id=self.current_session_id
                )
            
            # Construire le prompt système avec l'identité
            system_prompt = f"""Tu es {self.identity['name']}, {self.identity['description']}.
Tu es {self.identity['personality']}.

Tu as accès à :
- Une mémoire persistante pour retenir les conversations
- Des capacités de recherche web via DuckDuckGo
- Des modèles de langage via Ollama

Réponds de manière utile et engageante."""
            
            # Obtenir la réponse d'Ollama
            response = await self.ollama.chat(message, system_prompt)
            
            # Sauvegarder la réponse
            if use_memory and self.memory.is_initialized:
                await self.memory.save_message(
                    role="assistant", 
                    content=response, 
                    session_id=self.current_session_id
                )
            
            return response
            
        except Exception as e:
            return f"❌ Erreur lors du chat : {str(e)}"
    
    async def search_and_analyze(self, query: str, search_type: str = "web") -> str:
        """
        Effectue une recherche et l'analyse avec le LLM.
        
        Args:
            query: Requête de recherche
            search_type: Type de recherche (web, news, images)
            
        Returns:
            Analyse des résultats de recherche
        """
        if not self.is_initialized:
            return "❌ Locrit n'est pas encore initialisé."
        
        try:
            # Effectuer la recherche
            if search_type == "web":
                results = await self.search.search_web(query, max_results=5)
            elif search_type == "news":
                results = await self.search.search_news(query, max_results=5)
            elif search_type == "images":
                results = await self.search.search_images(query, max_results=5)
            else:
                return f"❌ Type de recherche non supporté : {search_type}"
            
            # Sauvegarder les résultats
            if self.memory.is_initialized:
                await self.memory.save_search_results(query, search_type, results)
            
            if not results:
                return f"🔍 Aucun résultat trouvé pour : {query}"
            
            # Formater les résultats pour l'analyse
            formatted_results = self.search.format_results_for_display(results, search_type)
            
            # Analyser avec le LLM
            analysis_prompt = f"""Analyse les résultats de recherche suivants pour la requête "{query}" :

{formatted_results}

Fournis un résumé utile et des insights pertinents."""
            
            analysis = await self.ollama.chat(analysis_prompt)
            
            return f"🔍 Résultats pour '{query}':\n\n{formatted_results}\n\n🤖 Analyse:\n{analysis}"
            
        except Exception as e:
            return f"❌ Erreur lors de la recherche : {str(e)}"
    
    async def remember(self, query: str, limit: int = 5, use_semantic: bool = True) -> str:
        """
        Recherche dans la mémoire du Locrit.
        
        Args:
            query: Terme à rechercher
            limit: Nombre maximum de résultats
            use_semantic: Utiliser la recherche sémantique si disponible
            
        Returns:
            Résultats de la recherche en mémoire
        """
        if not self.memory.is_initialized:
            return "❌ Mémoire non initialisée."
        
        try:
            # Essayer la recherche sémantique d'abord
            if use_semantic and self.memory.embedding_service.is_initialized:
                conversations = await self.memory.search_semantic(query, limit=limit)
                search_type = "sémantique"
            else:
                # Fallback sur la recherche textuelle
                conversations = await self.memory.search_conversations(query, limit=limit)
                search_type = "textuelle"
            
            if not conversations:
                return f"🧠 Aucun souvenir trouvé pour : {query}"
            
            results = []
            for conv in conversations:
                score_info = ""
                if 'similarity_score' in conv:
                    score_info = f" (score: {conv['similarity_score']:.2f})"
                results.append(f"📝 {conv['role']}: {conv['content'][:100]}...{score_info}")
            
            return f"🧠 Souvenirs ({search_type}) pour '{query}':\n\n" + "\n".join(results)
            
        except Exception as e:
            return f"❌ Erreur lors de la recherche en mémoire : {str(e)}"
    
    def start_new_session(self) -> str:
        """
        Démarre une nouvelle session de conversation.
        
        Returns:
            ID de la nouvelle session
        """
        from datetime import datetime
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.current_session_id
    
    async def shutdown(self) -> None:
        """Ferme proprement tous les services."""
        # Désenregistrer du serveur central
        if self.central_server.is_registered:
            await self.central_server.unregister()
        
        # Arrêter le serveur API si actif
        if self.server_mode:
            await self.stop_server_mode()
        
        # Fermer le tunnel si actif
        try:
            if hasattr(self.tunneling, 'is_active'):
                if callable(self.tunneling.is_active):
                    tunnel_active = self.tunneling.is_active()
                else:
                    tunnel_active = self.tunneling.is_active
                
                if tunnel_active:
                    await self.close_tunnel()
        except Exception as e:
            print(f"Erreur fermeture tunnel: {e}")
        
        # Fermer les services de base
        await self.ollama.disconnect()
        await self.memory.close()
    
    async def start_server_mode(self, port: int = 8000) -> dict:
        """
        Démarre le mode serveur avec API REST et WebSocket.
        
        Args:
            port: Port pour le serveur API
            
        Returns:
            Statut du démarrage
        """
        try:
            if not self.server_mode:
                await self.api.start_server(port)
                self.server_mode = True
                return {
                    "success": True,
                    "message": f"Serveur démarré sur le port {port}",
                    "port": port
                }
            else:
                return {
                    "success": False,
                    "message": "Le serveur est déjà en cours d'exécution"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors du démarrage du serveur: {e}"
            }
    
    async def stop_server_mode(self) -> dict:
        """
        Arrête le mode serveur.
        
        Returns:
            Statut de l'arrêt
        """
        try:
            if self.server_mode:
                await self.api.stop_server()
                self.server_mode = False
                return {
                    "success": True,
                    "message": "Serveur arrêté"
                }
            else:
                return {
                    "success": False,
                    "message": "Le serveur n'est pas en cours d'exécution"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors de l'arrêt du serveur: {e}"
            }
    
    async def create_tunnel(self, provider: str = "localhost.run") -> dict:
        """
        Crée un tunnel SSH pour l'accès distant.
        
        Args:
            provider: Fournisseur de tunnel (localhost.run ou pinggy.io)
            
        Returns:
            Informations du tunnel
        """
        try:
            if not self.server_mode:
                return {
                    "success": False,
                    "message": "Le serveur doit être démarré avant de créer un tunnel"
                }
            
            tunnel_info = await self.tunneling.create_tunnel(
                local_port=self.api.port,
                provider=provider
            )
            
            return {
                "success": True,
                "message": "Tunnel créé avec succès",
                "url": tunnel_info.get("public_url"),
                "provider": provider
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors de la création du tunnel: {e}"
            }
    
    async def close_tunnel(self) -> dict:
        """
        Ferme le tunnel SSH actuel.
        
        Returns:
            Statut de la fermeture
        """
        try:
            await self.tunneling.close_tunnel()
            return {
                "success": True,
                "message": "Tunnel fermé"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors de la fermeture du tunnel: {e}"
            }
    
    # === Mode Client pour communication inter-locrits ===
    
    async def connect_to_locrit(self, url: str, locrit_name: str = None) -> dict:
        """
        Se connecte à un autre locrit via son API.
        
        Args:
            url: URL de l'API du locrit distant
            locrit_name: Nom du locrit pour mémorisation
            
        Returns:
            Statut de la connexion
        """
        import httpx
        
        try:
            # Tester la connexion
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/status")
                if response.status_code == 200:
                    remote_status = response.json()
                    
                    # Mémoriser cette connexion
                    if locrit_name and self.memory.is_initialized:
                        connection_info = {
                            "type": "locrit_connection",
                            "url": url,
                            "name": locrit_name,
                            "remote_identity": remote_status.get("identity", {}),
                            "connected_at": datetime.now().isoformat()
                        }
                        await self.memory.save_message(
                            role="system",
                            content=f"Connexion établie avec le locrit {locrit_name} via {url}",
                            session_id=self.current_session_id,
                            metadata=connection_info
                        )
                    
                    return {
                        "success": True,
                        "message": f"Connecté au locrit {locrit_name or 'distant'}",
                        "remote_status": remote_status
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Impossible de se connecter: HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur de connexion: {e}"
            }
    
    async def chat_with_locrit(self, url: str, message: str, user_id: str = None) -> dict:
        """
        Envoie un message à un autre locrit.
        
        Args:
            url: URL de l'API du locrit distant
            message: Message à envoyer
            user_id: Identifiant de l'utilisateur
            
        Returns:
            Réponse du locrit distant
        """
        import httpx
        
        try:
            payload = {
                "message": message,
                "user_id": user_id or f"locrit_{self.identity['name']}",
                "session_id": self.current_session_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{url}/chat", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Mémoriser l'échange
                    if self.memory.is_initialized:
                        await self.memory.save_message(
                            role="user",
                            content=f"[À {url}] {message}",
                            session_id=self.current_session_id
                        )
                        await self.memory.save_message(
                            role="assistant",
                            content=f"[De {url}] {result.get('response', '')}",
                            session_id=self.current_session_id
                        )
                    
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "remote_url": url
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors de l'envoi: {e}"
            }
    
    async def list_known_locrits(self) -> List[Dict[str, Any]]:
        """
        Liste les locrits connus depuis la mémoire.
        
        Returns:
            Liste des locrits mémorisés
        """
        if not self.memory.is_initialized:
            return []
        
        try:
            # Rechercher les connexions mémorisées
            conversations = await self.memory.search_conversations("locrit_connection", limit=20)
            
            known_locrits = []
            for conv in conversations:
                if conv.get('metadata', {}).get('type') == 'locrit_connection':
                    known_locrits.append({
                        "name": conv['metadata'].get('name'),
                        "url": conv['metadata'].get('url'),
                        "last_contact": conv.get('timestamp'),
                        "identity": conv['metadata'].get('remote_identity', {})
                    })
            
            return known_locrits
            
        except Exception as e:
            print(f"Erreur lors de la récupération des locrits connus: {e}")
            return []
    
    # === Serveur central ===
    
    async def register_with_central_server(self, public_url: str = None) -> dict:
        """
        Enregistre ce locrit auprès du serveur central.
        
        Args:
            public_url: URL publique si tunnel actif
            
        Returns:
            Résultat de l'enregistrement
        """
        try:
            result = await self.central_server.register_locrit(self.identity, public_url)
            
            if result['success'] and self.memory.is_initialized:
                # Mémoriser l'enregistrement
                await self.memory.save_message(
                    role="system",
                    content=f"Enregistré auprès du serveur central avec ID: {result.get('locrit_id')}",
                    session_id=self.current_session_id,
                    metadata={"type": "central_server_registration", "result": result}
                )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'enregistrement: {e}"
            }
    
    async def discover_locrits_from_central(self, search_query: str = None) -> List[Dict[str, Any]]:
        """
        Découvre des locrits via le serveur central.
        
        Args:
            search_query: Critère de recherche optionnel
            
        Returns:
            Liste des locrits disponibles
        """
        try:
            discovered = await self.central_server.discover_locrits(search_query)
            
            # Mémoriser les nouveaux locrits découverts
            if self.memory.is_initialized:
                for locrit in discovered:
                    await self.memory.save_message(
                        role="system",
                        content=f"Locrit découvert via serveur central: {locrit.get('identity', {}).get('name')}",
                        session_id=self.current_session_id,
                        metadata={
                            "type": "locrit_discovery",
                            "discovery_method": "central_server",
                            "locrit_info": locrit
                        }
                    )
            
            return discovered
            
        except Exception as e:
            print(f"Erreur découverte centrale: {e}")
            return []
    
    async def send_heartbeat_to_central(self) -> bool:
        """
        Envoie un heartbeat au serveur central.
        
        Returns:
            Succès du heartbeat
        """
        try:
            status = await self.get_status()
            return await self.central_server.send_heartbeat(status)
        except Exception as e:
            print(f"Erreur heartbeat central: {e}")
            return False
