"""
Service de connexion et communication avec Ollama.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
import ollama
from ollama import AsyncClient
from .comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory


class OllamaService:
    """Service pour gérer la connexion et communication avec Ollama."""

    def __init__(self, base_url: str):
        """
        Initialise le service Ollama.

        Args:
            base_url: URL complète du serveur Ollama (ex: http://server.example.com:11434)

        Raises:
            ValueError: Si base_url n'est pas fourni
        """
        if not base_url:
            raise ValueError("base_url est obligatoire. Chaque Locrit doit avoir son propre serveur Ollama configuré.")

        self.base_url = base_url.rstrip('/')

        # Extract host and port for logging
        import urllib.parse
        parsed = urllib.parse.urlparse(self.base_url)
        self.host = parsed.hostname or 'unknown'
        self.port = parsed.port or 11434

        self.client = AsyncClient(host=self.base_url)
        self.is_connected = False
        self.available_models = []
        self.current_model = None
    
    async def connect(self) -> bool:
        """
        Teste la connexion au serveur Ollama.
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            # Test de connexion en listant les modèles
            response = await self.client.list()
            self.available_models = [model['name'] for model in response['models']]
            self.is_connected = True

            # Sélectionner un modèle par défaut si disponible
            if self.available_models and not self.current_model:
                self.current_model = self.available_models[0]

            # Log successful connection
            comprehensive_logger.log_system_event(
                "ollama_connection_success",
                f"Connected to Ollama at {self.host}:{self.port}, found {len(self.available_models)} models"
            )

            return True
        except Exception as e:
            self.is_connected = False
            self.available_models = []
            print(f"Erreur de connexion Ollama : {e}")

            # Log connection failure
            comprehensive_logger.log_error(
                error=e,
                context="Ollama connection test",
                additional_data={"host": self.host, "port": self.port}
            )

            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion Ollama."""
        self.is_connected = False
        self.current_model = None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de la connexion Ollama.
        
        Returns:
            Dictionnaire avec les informations de statut
        """
        return {
            "connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "current_model": self.current_model,
            "available_models": self.available_models
        }
    
    async def chat(self, message: str, system_prompt: Optional[str] = None, locrit_name: Optional[str] = None) -> str:
        """
        Envoie un message au modèle et retourne la réponse.
        
        Args:
            message: Message de l'utilisateur
            system_prompt: Prompt système optionnel
            
        Returns:
            Réponse du modèle
            
        Raises:
            Exception: Si pas de connexion ou modèle sélectionné
        """
        if not self.is_connected:
            raise Exception("Pas de connexion à Ollama")
        
        if not self.current_model:
            raise Exception("Aucun modèle sélectionné")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        try:
            # Start operation tracking
            operation_id = comprehensive_logger.start_operation("ollama_chat_request")

            # Log the request
            comprehensive_logger.log_ollama_request(
                model=self.current_model,
                messages=messages,
                locrit_name=locrit_name or "system",
                stream=False
            )

            response = await self.client.chat(
                model=self.current_model,
                messages=messages
            )

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log the response
            comprehensive_logger.log_ollama_response(
                model=self.current_model,
                response=response['message']['content'],
                locrit_name=locrit_name or "system",
                duration_ms=duration_ms
            )

            return response['message']['content']
        except Exception as e:
            # End operation tracking for failed request
            if 'operation_id' in locals():
                duration_ms = comprehensive_logger.end_operation(operation_id)
                comprehensive_logger.log_ollama_response(
                    model=self.current_model,
                    response="",
                    locrit_name=locrit_name or "system",
                    duration_ms=duration_ms,
                    error=str(e)
                )

            raise Exception(f"Erreur lors du chat : {e}")
    
    async def chat_stream(self, message: str, system_prompt: Optional[str] = None, locrit_name: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Envoie un message et retourne un stream de réponse.
        
        Args:
            message: Message de l'utilisateur
            system_prompt: Prompt système optionnel
            
        Yields:
            Chunks de la réponse du modèle
        """
        if not self.is_connected:
            raise Exception("Pas de connexion à Ollama")
        
        if not self.current_model:
            raise Exception("Aucun modèle sélectionné")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        try:
            # Start operation tracking
            operation_id = comprehensive_logger.start_operation("ollama_chat_stream_request")

            # Log the request
            comprehensive_logger.log_ollama_request(
                model=self.current_model,
                messages=messages,
                locrit_name=locrit_name or "system",
                stream=True
            )

            async for chunk in await self.client.chat(
                model=self.current_model,
                messages=messages,
                stream=True
            ):
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

            # End operation tracking
            duration_ms = comprehensive_logger.end_operation(operation_id)

            # Log successful streaming completion
            comprehensive_logger.log_ollama_response(
                model=self.current_model,
                response="[STREAM_COMPLETED]",
                locrit_name=locrit_name or "system",
                duration_ms=duration_ms
            )

        except Exception as e:
            # End operation tracking for failed request
            if 'operation_id' in locals():
                duration_ms = comprehensive_logger.end_operation(operation_id)
                comprehensive_logger.log_ollama_response(
                    model=self.current_model,
                    response="",
                    locrit_name=locrit_name or "system",
                    duration_ms=duration_ms,
                    error=str(e)
                )

            raise Exception(f"Erreur lors du chat stream : {e}")
    
    async def set_model(self, model_name: str) -> bool:
        """
        Change le modèle utilisé.
        
        Args:
            model_name: Nom du modèle à utiliser
            
        Returns:
            True si le changement réussit
        """
        if model_name in self.available_models:
            self.current_model = model_name
            return True
        return False
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Télécharge un nouveau modèle.
        
        Args:
            model_name: Nom du modèle à télécharger
            
        Returns:
            True si le téléchargement réussit
        """
        try:
            await self.client.pull(model_name)
            # Rafraîchir la liste des modèles
            await self.connect()
            return True
        except Exception as e:
            print(f"Erreur lors du téléchargement du modèle : {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Test synchrone de la connexion Ollama pour l'interface web.

        Returns:
            Dictionnaire avec le statut de la connexion et les modèles
        """
        try:
            # Utiliser le client synchrone pour un test rapide
            import requests

            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            data = response.json()
            models = [model['name'] for model in data.get('models', [])]

            return {
                'success': True,
                'models': models,
                'base_url': self.base_url
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erreur de connexion: {str(e)}',
                'base_url': self.base_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur inattendue: {str(e)}',
                'base_url': self.base_url
            }


def get_ollama_service_for_locrit(locrit_name: str) -> Optional[OllamaService]:
    """
    Récupère l'instance du service Ollama pour un Locrit spécifique.

    Args:
        locrit_name: Nom du Locrit

    Returns:
        OllamaService configuré pour ce Locrit ou None si pas de configuration

    Raises:
        ValueError: Si le Locrit n'a pas de base_url configuré
    """
    try:
        from .config_service import config_service

        # Récupérer les paramètres du Locrit
        locrit_settings = config_service.get_locrit_settings(locrit_name)
        if not locrit_settings:
            comprehensive_logger.log_error(
                error=ValueError(f"Locrit '{locrit_name}' non trouvé"),
                context="get_ollama_service_for_locrit"
            )
            return None

        # Chaque Locrit doit avoir son propre ollama_url
        ollama_url = locrit_settings.get('ollama_url')
        if not ollama_url:
            error_msg = f"Locrit '{locrit_name}' n'a pas de 'ollama_url' configuré"
            comprehensive_logger.log_error(
                error=ValueError(error_msg),
                context="get_ollama_service_for_locrit"
            )
            raise ValueError(error_msg)

        # Créer le service avec l'URL du Locrit
        return OllamaService(base_url=ollama_url)

    except Exception as e:
        comprehensive_logger.log_error(
            error=e,
            context="get_ollama_service_for_locrit",
            additional_data={"locrit_name": locrit_name}
        )
        raise
