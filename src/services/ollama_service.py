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
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        """
        Initialise le service Ollama.
        
        Args:
            host: Adresse du serveur Ollama
            port: Port du serveur Ollama
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
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


# Instance globale du service Ollama (sera initialisée avec la config)
ollama_service = None

def get_ollama_service():
    """Récupère ou crée l'instance du service Ollama avec la configuration actuelle"""
    global ollama_service

    if ollama_service is None:
        # Charger la configuration
        try:
            from .config_service import config_service
            ollama_config = config_service.get_ollama_config()

            # Parser l'URL pour extraire host et port
            import urllib.parse
            parsed = urllib.parse.urlparse(ollama_config['base_url'])
            host = parsed.hostname or 'localhost'
            port = parsed.port or 11434

            ollama_service = OllamaService(host=host, port=port)
        except Exception:
            # Valeurs par défaut si erreur de config
            ollama_service = OllamaService()

    return ollama_service

# Créer l'instance par défaut
ollama_service = get_ollama_service()
