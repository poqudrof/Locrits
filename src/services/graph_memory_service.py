"""
Service de mémoire en graphe pour représenter les relations entre concepts.
"""

import sqlite3
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class GraphMemoryService:
    """Service de mémoire sous forme de graphe pour les relations conceptuelles."""
    
    def __init__(self, db_path: str = "data/locrit_graph_memory.db"):
        """
        Initialise le service de mémoire graphe.
        
        Args:
            db_path: Chemin vers la base de données
        """
        self.db_path = db_path
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialise la base de données graphe.
        
        Returns:
            Succès de l'initialisation
        """
        try:
            # Créer les tables pour le graphe
            async with asyncio.to_thread(sqlite3.connect, self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table des nœuds (concepts)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS nodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        concept TEXT UNIQUE NOT NULL,
                        type TEXT NOT NULL,
                        properties TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table des relations (arêtes)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS edges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id INTEGER NOT NULL,
                        target_id INTEGER NOT NULL,
                        relation_type TEXT NOT NULL,
                        weight REAL DEFAULT 1.0,
                        properties TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_id) REFERENCES nodes (id),
                        FOREIGN KEY (target_id) REFERENCES nodes (id),
                        UNIQUE(source_id, target_id, relation_type)
                    )
                """)
                
                # Index pour les performances
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_concept ON nodes(concept)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")
                
                conn.commit()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Erreur initialisation mémoire graphe: {e}")
            return False
    
    async def add_concept(self, concept: str, concept_type: str = "general", properties: Dict[str, Any] = None) -> int:
        """
        Ajoute un concept au graphe.
        
        Args:
            concept: Nom du concept
            concept_type: Type du concept
            properties: Propriétés additionnelles
            
        Returns:
            ID du nœud créé
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            properties_json = json.dumps(properties or {})
            
            async with asyncio.to_thread(sqlite3.connect, self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou récupérer le concept existant
                cursor.execute("""
                    INSERT OR IGNORE INTO nodes (concept, type, properties)
                    VALUES (?, ?, ?)
                """, (concept, concept_type, properties_json))
                
                # Récupérer l'ID
                cursor.execute("SELECT id FROM nodes WHERE concept = ?", (concept,))
                node_id = cursor.fetchone()[0]
                
                conn.commit()
                return node_id
                
        except Exception as e:
            print(f"Erreur ajout concept: {e}")
            return None
    
    async def add_relation(self, source_concept: str, target_concept: str, relation_type: str, weight: float = 1.0, properties: Dict[str, Any] = None) -> bool:
        """
        Ajoute une relation entre deux concepts.
        
        Args:
            source_concept: Concept source
            target_concept: Concept cible
            relation_type: Type de relation
            weight: Poids de la relation
            properties: Propriétés additionnelles
            
        Returns:
            Succès de l'ajout
        """
        try:
            # S'assurer que les concepts existent
            source_id = await self.add_concept(source_concept)
            target_id = await self.add_concept(target_concept)
            
            if not source_id or not target_id:
                return False
            
            properties_json = json.dumps(properties or {})
            
            async with asyncio.to_thread(sqlite3.connect, self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour la relation
                cursor.execute("""
                    INSERT OR REPLACE INTO edges 
                    (source_id, target_id, relation_type, weight, properties)
                    VALUES (?, ?, ?, ?, ?)
                """, (source_id, target_id, relation_type, weight, properties_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Erreur ajout relation: {e}")
            return False
    
    async def get_related_concepts(self, concept: str, relation_types: List[str] = None, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Récupère les concepts liés à un concept donné.
        
        Args:
            concept: Concept de départ
            relation_types: Types de relations à considérer
            max_depth: Profondeur maximale de recherche
            
        Returns:
            Liste des concepts liés
        """
        if not self.is_initialized:
            return []
        
        try:
            async with asyncio.to_thread(sqlite3.connect, self.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupérer l'ID du concept de départ
                cursor.execute("SELECT id FROM nodes WHERE concept = ?", (concept,))
                result = cursor.fetchone()
                if not result:
                    return []
                
                start_id = result[0]
                visited = set()
                related = []
                
                # Recherche en largeur
                current_level = {start_id}
                for depth in range(max_depth):
                    next_level = set()
                    
                    for node_id in current_level:
                        if node_id in visited:
                            continue
                        visited.add(node_id)
                        
                        # Relations sortantes
                        query = """
                            SELECT n.concept, n.type, e.relation_type, e.weight, n.properties
                            FROM edges e
                            JOIN nodes n ON e.target_id = n.id
                            WHERE e.source_id = ?
                        """
                        params = [node_id]
                        
                        if relation_types:
                            placeholders = ','.join(['?' for _ in relation_types])
                            query += f" AND e.relation_type IN ({placeholders})"
                            params.extend(relation_types)
                        
                        cursor.execute(query, params)
                        for row in cursor.fetchall():
                            concept_name, concept_type, rel_type, weight, props = row
                            related.append({
                                "concept": concept_name,
                                "type": concept_type,
                                "relation_type": rel_type,
                                "weight": weight,
                                "properties": json.loads(props or "{}"),
                                "depth": depth + 1
                            })
                            
                            # Ajouter au niveau suivant
                            cursor.execute("SELECT id FROM nodes WHERE concept = ?", (concept_name,))
                            next_level.add(cursor.fetchone()[0])
                    
                    current_level = next_level
                
                return related
                
        except Exception as e:
            print(f"Erreur récupération concepts liés: {e}")
            return []
    
    async def analyze_text_for_concepts(self, text: str) -> List[str]:
        """
        This function is deprecated.
        Concept extraction is now handled by the LLM through the new modular memory system.

        Returns:
            Empty list - LLM decides memory storage through memory tools
        """
        # Concept extraction is now LLM-driven through the modular memory system
        return []
    
    async def learn_from_conversation(self, user_message: str, assistant_response: str) -> bool:
        """
        Apprend des relations à partir d'une conversation.
        
        Args:
            user_message: Message de l'utilisateur
            assistant_response: Réponse de l'assistant
            
        Returns:
            Succès de l'apprentissage
        """
        try:
            # Extraire les concepts
            user_concepts = await self.analyze_text_for_concepts(user_message)
            assistant_concepts = await self.analyze_text_for_concepts(assistant_response)
            
            # Créer des relations entre concepts de la question et de la réponse
            for user_concept in user_concepts:
                await self.add_concept(user_concept, "user_topic")
                
                for assistant_concept in assistant_concepts:
                    await self.add_concept(assistant_concept, "response_topic")
                    
                    # Relation "discuss_together"
                    await self.add_relation(
                        user_concept, 
                        assistant_concept, 
                        "discusses",
                        weight=0.8,
                        properties={"context": "conversation"}
                    )
            
            # Relations entre concepts d'une même réponse
            for i, concept1 in enumerate(assistant_concepts):
                for concept2 in assistant_concepts[i+1:]:
                    await self.add_relation(
                        concept1,
                        concept2,
                        "mentioned_together",
                        weight=0.6,
                        properties={"context": "same_response"}
                    )
            
            return True
            
        except Exception as e:
            print(f"Erreur apprentissage conversation: {e}")
            return False
    
    async def get_context_for_query(self, query: str, max_concepts: int = 10) -> str:
        """
        Génère un contexte pour une requête basé sur le graphe de mémoire.
        
        Args:
            query: Requête de l'utilisateur
            max_concepts: Nombre maximum de concepts liés à inclure
            
        Returns:
            Contexte textuel généré
        """
        try:
            # Extraire les concepts de la requête
            query_concepts = await self.analyze_text_for_concepts(query)
            
            if not query_concepts:
                return ""
            
            all_related = []
            
            # Pour chaque concept de la requête, récupérer les concepts liés
            for concept in query_concepts:
                related = await self.get_related_concepts(concept, max_depth=2)
                all_related.extend(related)
            
            # Trier par poids et limiter
            all_related.sort(key=lambda x: x['weight'], reverse=True)
            top_related = all_related[:max_concepts]
            
            if not top_related:
                return ""
            
            # Générer le contexte
            context_parts = []
            context_parts.append("Contexte mémorisé pertinent :")
            
            for rel in top_related:
                context_parts.append(
                    f"- {rel['concept']} ({rel['relation_type']}, poids: {rel['weight']:.1f})"
                )
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"Erreur génération contexte: {e}")
            return ""
    
    async def get_stats(self) -> Dict[str, int]:
        """
        Récupère les statistiques de la mémoire graphe.
        
        Returns:
            Statistiques
        """
        if not self.is_initialized:
            return {"nodes": 0, "edges": 0}
        
        try:
            async with asyncio.to_thread(sqlite3.connect, self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM nodes")
                node_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM edges")
                edge_count = cursor.fetchone()[0]
                
                return {
                    "nodes": node_count,
                    "edges": edge_count
                }
                
        except Exception as e:
            print(f"Erreur stats mémoire graphe: {e}")
            return {"nodes": 0, "edges": 0}
    
    async def close(self):
        """Ferme les connexions du service de mémoire graphe."""
        # Le GraphMemoryService utilise des connexions temporaires via asyncio.to_thread
        # donc pas de connexion persistante à fermer
        self.is_initialized = False
        print("🔒 GraphMemoryService fermé")
