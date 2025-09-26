"""
Service de recherche web utilisant DuckDuckGo.
"""

from typing import List, Dict, Any
from duckduckgo_search import DDGS


class SearchService:
    """Service pour effectuer des recherches web avec DuckDuckGo."""
    
    def __init__(self):
        """Initialise le service de recherche."""
        self.ddgs = DDGS()
    
    def search_web(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Effectue une recherche web.
        
        Args:
            query: Terme de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            results = []
            for result in self.ddgs.text(query, max_results=max_results):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                })
            return results
        except Exception as e:
            print(f"Erreur lors de la recherche : {e}")
            return []
    
    def format_results_for_display(self, results: List[Dict[str, Any]]) -> str:
        """
        Formate les résultats pour l'affichage.
        
        Args:
            results: Liste des résultats
            
        Returns:
            Texte formaté pour affichage
        """
        if not results:
            return "Aucun résultat trouvé."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            formatted.append(f"   🔗 {result['url']}")
            formatted.append(f"   📝 {result['snippet'][:200]}...")
            formatted.append("")
        
        return "\n".join(formatted)
