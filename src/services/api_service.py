"""
Service API pour le mode serveur de Locrit.
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
from datetime import datetime
import threading


# Modèles de données pour l'API
class ChatMessage(BaseModel):
    message: str
    user_id: str = "api_user"
    session_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    search_type: str = "web"
    max_results: int = 10
    user_id: str = "api_user"

class MemoryRequest(BaseModel):
    query: str
    limit: int = 5
    use_semantic: bool = True
    user_id: str = "api_user"


class APIService:
    """Service API pour communication inter-locrits et accès distant."""
    
    def __init__(self, locrit_manager=None, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialise le service API.
        
        Args:
            locrit_manager: Instance du gestionnaire Locrit
            host: Adresse d'écoute
            port: Port d'écoute
        """
        self.locrit_manager = locrit_manager
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Locrit API",
            description="API pour communication avec un Locrit autonome",
            version="1.0.0"
        )
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.websocket_connections: List[WebSocket] = []
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Configure les middlewares."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Configure les routes de l'API."""
        
        @self.app.get("/")
        async def root():
            """Point d'entrée de l'API."""
            return {
                "service": "Locrit API",
                "status": "active",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/status")
        async def get_status():
            """Retourne le statut du Locrit."""
            if not self.locrit_manager:
                raise HTTPException(status_code=503, detail="Locrit non initialisé")
            
            try:
                status = await self.locrit_manager.get_status()
                return status
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/chat")
        async def chat(request: ChatMessage):
            """Envoie un message au Locrit."""
            if not self.locrit_manager:
                raise HTTPException(status_code=503, detail="Locrit non initialisé")
            
            try:
                response = await self.locrit_manager.chat(request.message)
                return {
                    "response": response,
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/search")
        async def search(request: SearchRequest):
            """Effectue une recherche via le Locrit."""
            if not self.locrit_manager:
                raise HTTPException(status_code=503, detail="Locrit non initialisé")
            
            try:
                result = await self.locrit_manager.search_and_analyze(
                    request.query, request.search_type
                )
                return {
                    "result": result,
                    "query": request.query,
                    "search_type": request.search_type,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory")
        async def search_memory(request: MemoryRequest):
            """Recherche dans la mémoire du Locrit."""
            if not self.locrit_manager:
                raise HTTPException(status_code=503, detail="Locrit non initialisé")
            
            try:
                result = await self.locrit_manager.remember(
                    request.query, request.limit, request.use_semantic
                )
                return {
                    "result": result,
                    "query": request.query,
                    "use_semantic": request.use_semantic,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket pour communication en temps réel."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Recevoir un message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "chat":
                        if self.locrit_manager:
                            response = await self.locrit_manager.chat(message_data.get("message", ""))
                            await websocket.send_text(json.dumps({
                                "type": "chat_response",
                                "response": response,
                                "timestamp": datetime.now().isoformat()
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "Locrit non initialisé"
                            }))
                    
                    elif message_data.get("type") == "status":
                        if self.locrit_manager:
                            status = await self.locrit_manager.get_status()
                            await websocket.send_text(json.dumps({
                                "type": "status_response",
                                "status": status,
                                "timestamp": datetime.now().isoformat()
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "Locrit non initialisé"
                            }))
            
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                print(f"Erreur WebSocket : {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Diffuse un message à toutes les connexions WebSocket."""
        if self.websocket_connections:
            message_str = json.dumps(message)
            for websocket in self.websocket_connections.copy():
                try:
                    await websocket.send_text(message_str)
                except:
                    # Connexion fermée, la supprimer
                    if websocket in self.websocket_connections:
                        self.websocket_connections.remove(websocket)
    
    def start_server(self) -> bool:
        """
        Démarre le serveur API dans un thread séparé.
        
        Returns:
            True si le serveur démarre avec succès
        """
        if self.is_running:
            return True
        
        try:
            def run_server():
                uvicorn.run(
                    self.app,
                    host=self.host,
                    port=self.port,
                    log_level="info"
                )
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"Erreur lors du démarrage du serveur : {e}")
            return False
    
    def stop_server(self):
        """Arrête le serveur API."""
        self.is_running = False
        if self.server_thread and self.server_thread.is_alive():
            # Note: uvicorn ne peut pas être arrêté proprement depuis un thread
            # En production, il faudrait une solution plus sophistiquée
            pass
    
    def get_server_info(self) -> Dict[str, Any]:
        """Retourne les informations du serveur."""
        return {
            "running": self.is_running,
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}",
            "websocket_url": f"ws://{self.host}:{self.port}/ws",
            "connected_clients": len(self.websocket_connections)
        }
