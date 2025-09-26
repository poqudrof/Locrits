"""
Service de génération d'embeddings pour la mémoire vectorielle.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional, Dict, Any
import pickle
import os
from pathlib import Path


class EmbeddingService:
    """Service pour générer et gérer les embeddings vectoriels."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "data/vector_index"):
        """
        Initialise le service d'embeddings.
        
        Args:
            model_name: Nom du modèle Sentence Transformers
            index_path: Chemin vers l'index FAISS
        """
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(exist_ok=True)
        
        self.model = None
        self.index = None
        self.dimension = 384  # Dimension du modèle all-MiniLM-L6-v2
        self.text_store = []  # Stockage des textes correspondants aux vecteurs
        self.metadata_store = []  # Stockage des métadonnées
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialise le modèle et l'index FAISS.
        
        Returns:
            True si l'initialisation réussit
        """
        try:
            # Charger le modèle Sentence Transformers
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # Charger ou créer l'index FAISS
            await self._load_or_create_index()
            
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation des embeddings : {e}")
            return False
    
    async def _load_or_create_index(self) -> None:
        """Charge l'index existant ou en crée un nouveau."""
        index_file = self.index_path / "faiss.index"
        text_file = self.index_path / "texts.pkl"
        metadata_file = self.index_path / "metadata.pkl"
        
        if index_file.exists() and text_file.exists():
            # Charger l'index existant
            self.index = faiss.read_index(str(index_file))
            
            with open(text_file, 'rb') as f:
                self.text_store = pickle.load(f)
            
            if metadata_file.exists():
                with open(metadata_file, 'rb') as f:
                    self.metadata_store = pickle.load(f)
            else:
                self.metadata_store = [{}] * len(self.text_store)
        else:
            # Créer un nouvel index
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)
            self.text_store = []
            self.metadata_store = []
    
    async def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Ajoute un texte à l'index vectoriel.
        
        Args:
            text: Texte à ajouter
            metadata: Métadonnées associées
            
        Returns:
            ID du vecteur ajouté
        """
        if not self.is_initialized:
            raise Exception("Service d'embeddings non initialisé")
        
        # Générer l'embedding
        embedding = self.model.encode([text])
        embedding = embedding.astype('float32')
        
        # Normaliser pour la similarité cosinus
        faiss.normalize_L2(embedding)
        
        # Ajouter à l'index
        self.index.add(embedding)
        
        # Stocker le texte et métadonnées
        self.text_store.append(text)
        self.metadata_store.append(metadata or {})
        
        # Sauvegarder
        await self._save_index()
        
        return len(self.text_store) - 1
    
    async def search_similar(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recherche les textes les plus similaires à la requête.
        
        Args:
            query: Texte de requête
            k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des résultats avec scores et métadonnées
        """
        if not self.is_initialized or self.index.ntotal == 0:
            return []
        
        # Générer l'embedding de la requête
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding.astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Rechercher dans l'index
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and 0 <= idx < len(self.text_store):
                results.append({
                    'text': self.text_store[idx],
                    'score': float(score),
                    'metadata': self.metadata_store[idx],
                    'index': int(idx)
                })
        
        return results
    
    async def _save_index(self) -> None:
        """Sauvegarde l'index et les données associées."""
        try:
            index_file = self.index_path / "faiss.index"
            text_file = self.index_path / "texts.pkl"
            metadata_file = self.index_path / "metadata.pkl"
            
            # Sauvegarder l'index FAISS
            faiss.write_index(self.index, str(index_file))
            
            # Sauvegarder les textes
            with open(text_file, 'wb') as f:
                pickle.dump(self.text_store, f)
            
            # Sauvegarder les métadonnées
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata_store, f)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'index : {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de l'index vectoriel.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            "initialized": self.is_initialized,
            "model": self.model_name,
            "dimension": self.dimension,
            "total_vectors": self.index.ntotal if self.index else 0,
            "texts_count": len(self.text_store)
        }
    
    async def close(self) -> None:
        """Ferme le service et sauvegarde."""
        if self.is_initialized:
            await self._save_index()
            self.is_initialized = False
