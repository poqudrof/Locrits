"""
Service de mémoire hybride pour Locrit - Updated to use Kuzu per-Locrit memory.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from .memory_manager_service import memory_manager


class MemoryService:
    """Service de mémoire hybride pour stocker et récupérer les conversations et données."""

    def __init__(self, locrit_name: str = None):
        """
        Initialise le service de mémoire.

        Args:
            locrit_name: Nom du Locrit pour lequel gérer la mémoire
        """
        self.locrit_name = locrit_name
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialise le service de mémoire.

        Returns:
            True si l'initialisation réussit
        """
        try:
            # Initialiser le gestionnaire de mémoire global
            await memory_manager.initialize()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la mémoire : {e}")
            return False
    
    def set_locrit_name(self, locrit_name: str) -> None:
        """
        Définit le nom du Locrit pour ce service de mémoire.

        Args:
            locrit_name: Nom du Locrit
        """
        self.locrit_name = locrit_name
    
    async def save_message(self, role: str, content: str, session_id: Optional[str] = None,
                          metadata: Optional[Dict] = None, user_id: str = "default") -> str:
        """
        Sauvegarde un message dans la mémoire du Locrit.

        Args:
            role: Rôle (user, assistant, system)
            content: Contenu du message
            session_id: ID de session optionnel
            metadata: Métadonnées optionnelles
            user_id: ID de l'utilisateur

        Returns:
            ID du message généré
        """
        if not self.is_initialized:
            raise Exception("Service de mémoire non initialisé")

        if not self.locrit_name:
            raise Exception("Nom du Locrit non défini")

        # Déléguer au gestionnaire de mémoire
        return await memory_manager.save_message(
            locrit_name=self.locrit_name,
            role=role,
            content=content,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
    
    async def save_search_results(self, query: str, search_type: str, results: List[Dict],
                                 user_id: str = "default") -> int:
        """
        Sauvegarde les résultats d'une recherche.

        Args:
            query: Requête de recherche
            search_type: Type de recherche (web, news, images)
            results: Résultats de la recherche
            user_id: ID de l'utilisateur

        Returns:
            ID de la recherche
        """
        # Note: Search results could be saved as special messages if needed
        # For now, just return a dummy ID
        return 1
    
    async def get_recent_conversations(self, limit: int = 50, session_id: Optional[str] = None,
                                     user_id: str = "default") -> List[Dict]:
        """
        Récupère les conversations récentes.

        Args:
            limit: Nombre maximum de messages
            session_id: Filtrer par session
            user_id: ID de l'utilisateur

        Returns:
            Liste des messages
        """
        if not self.is_initialized:
            raise Exception("Service de mémoire non initialisé")

        if not self.locrit_name:
            return []

        if session_id:
            return await memory_manager.get_conversation_history(self.locrit_name, session_id, limit)
        else:
            # For all conversations, we would need to search across all sessions
            # For now, return empty list
            return []
    
    async def search_conversations(self, query: str, user_id: str = "default",
                                 limit: int = 20) -> List[Dict]:
        """
        Recherche dans les conversations par texte.

        Args:
            query: Terme de recherche
            user_id: ID de l'utilisateur
            limit: Nombre maximum de résultats

        Returns:
            Liste des messages correspondants
        """
        if not self.is_initialized:
            raise Exception("Service de mémoire non initialisé")

        if not self.locrit_name:
            return []

        return await memory_manager.search_memories(self.locrit_name, query, limit)
    
    async def search_semantic(self, query: str, user_id: str = "default",
                            limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """
        Recherche sémantique dans les conversations.

        Args:
            query: Terme de recherche
            user_id: ID de l'utilisateur
            limit: Nombre maximum de résultats
            threshold: Seuil de similarité minimum

        Returns:
            Liste des messages correspondants avec scores de similarité
        """
        if not self.is_initialized:
            return []

        if not self.locrit_name:
            return []

        # For now, use text search as semantic search placeholder
        return await memory_manager.search_memories(self.locrit_name, query, limit)
    
    async def get_stats(self) -> Dict[str, int]:
        """
        Retourne des statistiques sur la mémoire.

        Returns:
            Dictionnaire avec les statistiques
        """
        if not self.is_initialized:
            return {"error": "Service non initialisé"}

        if not self.locrit_name:
            return {"error": "Nom du Locrit non défini"}

        # Récupérer les statistiques depuis le gestionnaire de mémoire
        summary = await memory_manager.get_full_memory_summary(self.locrit_name)

        if "statistics" in summary:
            return summary["statistics"]
        else:
            return {"error": summary.get("error", "Erreur inconnue")}
    
    async def get_contextual_memory(self, query: str, include_graph: bool = True) -> str:
        """
        Récupère un contexte mémoire enrichi pour une requête.

        Args:
            query: Requête de l'utilisateur
            include_graph: Inclure le contexte du graphe de mémoire

        Returns:
            Contexte textuel enrichi
        """
        if not self.locrit_name:
            return ""

        try:
            # Rechercher dans la mémoire du Locrit
            memories = await memory_manager.search_memories(self.locrit_name, query, limit=3)

            if not memories:
                return ""

            context_parts = ["Contexte de conversations pertinentes :"]
            for memory in memories:
                context_parts.append(f"- {memory['role']}: {memory['content'][:100]}...")

            return "\n".join(context_parts)

        except Exception as e:
            print(f"Erreur récupération contexte : {e}")
            return ""
    
    async def close(self) -> None:
        """Ferme la connexion à la base de données."""
        try:
            if self.locrit_name:
                await memory_manager.close_locrit_memory(self.locrit_name)
            self.is_initialized = False
        except Exception as e:
            print(f"Erreur fermeture mémoire: {e}")

    async def get_full_memory_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé complet de la mémoire du Locrit.

        Returns:
            Dictionnaire avec le résumé de la mémoire
        """
        if not self.is_initialized:
            return {"error": "Service de mémoire non initialisé"}

        if not self.locrit_name:
            return {"error": "Nom du Locrit non défini"}

        return await memory_manager.get_full_memory_summary(self.locrit_name)
