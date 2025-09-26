"""
Service de tunneling pour accès distant via SSH.
"""

import subprocess
import asyncio
import re
import time
from typing import Optional, Dict, Any
import threading
import signal
import os


class TunnelingService:
    """Service pour créer des tunnels SSH pour accès distant."""
    
    def __init__(self, local_port: int = 8000):
        """
        Initialise le service de tunneling.
        
        Args:
            local_port: Port local à exposer
        """
        self.local_port = local_port
        self.tunnel_process = None
        self.public_url = None
        self.is_active = False
        self.service_type = None  # 'localhost.run' ou 'pinggy.io'
    
    async def start_tunnel(self, service: str = "auto") -> Optional[str]:
        """
        Démarre un tunnel SSH.
        
        Args:
            service: Service à utiliser ('localhost.run', 'pinggy.io', 'auto')
            
        Returns:
            URL publique du tunnel ou None en cas d'erreur
        """
        if self.is_active:
            return self.public_url
        
        if service == "auto":
            # Essayer localhost.run en premier, puis pinggy.io
            url = await self._start_localhost_run()
            if url:
                return url
            return await self._start_pinggy()
        elif service == "localhost.run":
            return await self._start_localhost_run()
        elif service == "pinggy.io":
            return await self._start_pinggy()
        else:
            raise ValueError(f"Service de tunnel non supporté : {service}")
    
    async def _start_localhost_run(self) -> Optional[str]:
        """Démarre un tunnel avec localhost.run."""
        try:
            cmd = [
                "ssh", "-R", f"80:localhost:{self.local_port}",
                "nokey@localhost.run",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR"
            ]
            
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Attendre l'URL
            for _ in range(30):  # Timeout de 30 secondes
                if self.tunnel_process.poll() is not None:
                    break
                
                await asyncio.sleep(1)
                
                # Lire stderr pour l'URL
                if self.tunnel_process.stderr:
                    line = self.tunnel_process.stderr.readline()
                    if line:
                        # Chercher l'URL dans la sortie
                        url_match = re.search(r'https?://[^\s]+\.localhost\.run', line)
                        if url_match:
                            self.public_url = url_match.group(0)
                            self.is_active = True
                            self.service_type = "localhost.run"
                            return self.public_url
            
            # Si on arrive ici, le tunnel a échoué
            if self.tunnel_process:
                self.tunnel_process.terminate()
                self.tunnel_process = None
            
            return None
            
        except Exception as e:
            print(f"Erreur avec localhost.run : {e}")
            return None
    
    async def _start_pinggy(self) -> Optional[str]:
        """Démarre un tunnel avec pinggy.io."""
        try:
            cmd = [
                "ssh", "-p", "443", "-R0:localhost:8000", "qr@a.pinggy.io",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR"
            ]
            
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Attendre l'URL
            for _ in range(30):  # Timeout de 30 secondes
                if self.tunnel_process.poll() is not None:
                    break
                
                await asyncio.sleep(1)
                
                # Lire stdout pour l'URL avec pinggy
                if self.tunnel_process.stdout:
                    line = self.tunnel_process.stdout.readline()
                    if line:
                        # Chercher l'URL dans la sortie
                        url_match = re.search(r'https?://[^\s]+\.pinggy\.online', line)
                        if url_match:
                            self.public_url = url_match.group(0)
                            self.is_active = True
                            self.service_type = "pinggy.io"
                            return self.public_url
            
            # Si on arrive ici, le tunnel a échoué
            if self.tunnel_process:
                self.tunnel_process.terminate()
                self.tunnel_process = None
            
            return None
            
        except Exception as e:
            print(f"Erreur avec pinggy.io : {e}")
            return None
    
    def stop_tunnel(self):
        """Arrête le tunnel SSH."""
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                # Attendre un peu puis forcer l'arrêt si nécessaire
                time.sleep(2)
                if self.tunnel_process.poll() is None:
                    self.tunnel_process.kill()
            except Exception as e:
                print(f"Erreur lors de l'arrêt du tunnel : {e}")
            finally:
                self.tunnel_process = None
        
        self.is_active = False
        self.public_url = None
        self.service_type = None
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du tunnel."""
        return {
            "active": self.is_active,
            "public_url": self.public_url,
            "local_port": self.local_port,
            "service": self.service_type,
            "process_alive": self.tunnel_process is not None and self.tunnel_process.poll() is None
        }
    
    async def check_ssh_available(self) -> bool:
        """Vérifie si SSH est disponible sur le système."""
        try:
            result = subprocess.run(
                ["ssh", "-V"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def __del__(self):
        """Nettoyage automatique."""
        self.stop_tunnel()
