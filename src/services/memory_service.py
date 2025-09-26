"""
Service de mémoire hybride pour Locrit.
"""

import sqlite3
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from .embedding_service import EmbeddingService
from .graph_memory_service import GraphMemoryService

import sqlite3
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from pathlib import Path
from .embedding_service import EmbeddingService


class MemoryService:
    """Service de mémoire hybride pour stocker et récupérer les conversations et données."""
    
    def __init__(self, db_path: str = "data/locrit_memory.db"):
        """
        Initialise le service de mémoire.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self.conn = None  # Initialiser à None
        self.is_initialized = False
        self.embedding_service = EmbeddingService()
        self.graph_memory = GraphMemoryService()
    
    async def initialize(self) -> bool:
        """
        Initialise la base de données et les tables.
        
        Returns:
            True si l'initialisation réussit
        """
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Créer les tables
            await self._create_tables()
            
                        # Initialiser le service d'embeddings
            await self.embedding_service.initialize()
            
            # Initialiser la mémoire graphe
            await self.graph_memory.initialize()
            
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la mémoire : {e}")
            return False
    
    async def _create_tables(self) -> None:
        """Crée les tables nécessaires."""
        cursor = self.conn.cursor()
        
        # Table des conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT DEFAULT 'default',
                session_id TEXT,
                content_hash TEXT
            )
        ''')
        
        # Table des recherches
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL,
                results TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT DEFAULT 'default'
            )
        ''')
        
        # Table des embeddings (pour plus tard avec FAISS)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                vector_index INTEGER,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table de configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index pour les recherches rapides
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
            ON conversations(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conversations_user_session 
            ON conversations(user_id, session_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_searches_timestamp 
            ON searches(timestamp)
        ''')
        
        self.conn.commit()
    
    def _generate_content_hash(self, content: str) -> str:
        """Génère un hash pour le contenu."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def save_message(self, role: str, content: str, session_id: Optional[str] = None, 
                          metadata: Optional[Dict] = None, user_id: str = "default") -> str:
        """
        Sauvegarde un message dans la mémoire.
        
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
        
        content_hash = self._generate_content_hash(content)
        message_id = f"{role}_{content_hash[:16]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO conversations 
            (message_id, role, content, metadata, user_id, session_id, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (message_id, role, content, json.dumps(metadata) if metadata else None, 
              user_id, session_id, content_hash))
        
        self.conn.commit()
        
        # Ajouter à l'index vectoriel pour la recherche sémantique
        if self.embedding_service.is_initialized:
            try:
                vector_index = await self.embedding_service.add_text(
                    content, 
                    {
                        'message_id': message_id,
                        'role': role,
                        'timestamp': datetime.now().isoformat(),
                        'user_id': user_id,
                        'session_id': session_id
                    }
                )
                
                # Sauvegarder le lien avec l'index vectoriel
                cursor.execute('''
                    INSERT OR REPLACE INTO embeddings 
                    (content_hash, vector_index, metadata)
                    VALUES (?, ?, ?)
                ''', (content_hash, vector_index, json.dumps({'message_id': message_id})))
                self.conn.commit()
                
            except Exception as e:
                print(f"Erreur lors de l'ajout à l'index vectoriel : {e}")
        
        # Apprendre des relations dans le graphe de mémoire si c'est une conversation
        if role in ["user", "assistant"] and self.graph_memory.is_initialized:
            try:
                # Récupérer le message précédent pour l'apprentissage
                previous_messages = await self.search_conversations("", limit=2, session_id=session_id)
                if len(previous_messages) >= 2:
                    prev_msg = previous_messages[1]  # Message précédent
                    if prev_msg['role'] != role:  # Pair user/assistant
                        if role == "assistant":
                            await self.graph_memory.learn_from_conversation(prev_msg['content'], content)
                        else:
                            await self.graph_memory.learn_from_conversation(content, prev_msg['content'])
            except Exception as e:
                print(f"Erreur lors de l'apprentissage graphe : {e}")
        
        return message_id
    
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
        if not self.is_initialized:
            raise Exception("Service de mémoire non initialisé")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO searches (query, search_type, results, user_id)
            VALUES (?, ?, ?, ?)
        ''', (query, search_type, json.dumps(results), user_id))
        
        self.conn.commit()
        return cursor.lastrowid
    
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
        
        cursor = self.conn.cursor()
        query = '''
            SELECT * FROM conversations 
            WHERE user_id = ?
        '''
        params = [user_id]
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [{
            'id': row['id'],
            'message_id': row['message_id'],
            'role': row['role'],
            'content': row['content'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
            'timestamp': row['timestamp'],
            'session_id': row['session_id']
        } for row in rows]
    
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
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM conversations 
            WHERE user_id = ? AND content LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, f"%{query}%", limit))
        
        rows = cursor.fetchall()
        return [{
            'id': row['id'],
            'message_id': row['message_id'],
            'role': row['role'],
            'content': row['content'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
            'timestamp': row['timestamp'],
            'session_id': row['session_id']
        } for row in rows]
    
    async def search_semantic(self, query: str, user_id: str = "default", 
                            limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """
        Recherche sémantique dans les conversations via embeddings.
        
        Args:
            query: Terme de recherche
            user_id: ID de l'utilisateur
            limit: Nombre maximum de résultats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des messages correspondants avec scores de similarité
        """
        if not self.is_initialized or not self.embedding_service.is_initialized:
            return []
        
        try:
            # Recherche vectorielle
            vector_results = await self.embedding_service.search_similar(
                query, k=limit, threshold=threshold
            )
            
            # Récupérer les messages correspondants depuis SQLite
            results = []
            for vector_result in vector_results:
                message_id = vector_result['metadata'].get('message_id')
                if message_id:
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        SELECT * FROM conversations 
                        WHERE message_id = ? AND user_id = ?
                    ''', (message_id, user_id))
                    
                    row = cursor.fetchone()
                    if row:
                        result = {
                            'id': row['id'],
                            'message_id': row['message_id'],
                            'role': row['role'],
                            'content': row['content'],
                            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                            'timestamp': row['timestamp'],
                            'session_id': row['session_id'],
                            'similarity_score': vector_result['score']
                        }
                        results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche sémantique : {e}")
            return []
    
    async def get_stats(self) -> Dict[str, int]:
        """
        Retourne des statistiques sur la mémoire.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        if not self.is_initialized:
            return {"error": "Service non initialisé"}
        
        cursor = self.conn.cursor()
        
        # Compter les conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversations_count = cursor.fetchone()[0]
        
        # Compter les recherches
        cursor.execute("SELECT COUNT(*) FROM searches")
        searches_count = cursor.fetchone()[0]
        
        # Statistiques des embeddings
        embedding_stats = self.embedding_service.get_stats() if self.embedding_service else {}
        
        # Statistiques du graphe de mémoire
        graph_stats = await self.graph_memory.get_stats() if self.graph_memory.is_initialized else {}
        
        return {
            "message_count": conversations_count,
            "search_count": searches_count,
            "session_count": len(await self.get_all_sessions()),
            "embedding_count": embedding_stats.get("total_vectors", 0),
            "graph_nodes": graph_stats.get("nodes", 0),
            "graph_edges": graph_stats.get("edges", 0)
        }
    
    async def get_contextual_memory(self, query: str, include_graph: bool = True) -> str:
        """
        Récupère un contexte mémoire enrichi pour une requête.
        
        Args:
            query: Requête de l'utilisateur
            include_graph: Inclure le contexte du graphe de mémoire
            
        Returns:
            Contexte textuel enrichi
        """
        context_parts = []
        
        try:
            # Recherche sémantique standard
            if self.embedding_service.is_initialized:
                semantic_results = await self.search_semantic(query, limit=3)
                if semantic_results:
                    context_parts.append("Contexte de conversations pertinentes :")
                    for result in semantic_results:
                        context_parts.append(f"- {result['role']}: {result['content'][:100]}...")
            
            # Contexte du graphe de mémoire
            if include_graph and self.graph_memory.is_initialized:
                graph_context = await self.graph_memory.get_context_for_query(query)
                if graph_context:
                    context_parts.append(graph_context)
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            print(f"Erreur récupération contexte : {e}")
            return ""
    
    async def close(self) -> None:
        """Ferme la connexion à la base de données."""
        try:
            if hasattr(self, 'embedding_service') and self.embedding_service:
                await self.embedding_service.close()
        except Exception as e:
            print(f"Erreur fermeture embedding_service: {e}")
            
        try:
            if hasattr(self, 'graph_memory') and self.graph_memory:
                await self.graph_memory.close()
        except Exception as e:
            print(f"Erreur fermeture graph_memory: {e}")
            
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
                self.is_initialized = False
        except Exception as e:
            print(f"Erreur fermeture connexion DB: {e}")
