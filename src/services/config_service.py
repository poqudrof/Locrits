"""
Service de configuration centralisé pour Locrit
Gère la configuration YAML, les variables d'environnement et les sauvegardes
"""

import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

import os
import yaml
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigService:
    """Service de gestion des configurations de l'application"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config_data: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._load_config()
    
    def _setup_logging(self):
        """Configure le logging pour le service de configuration"""
        # Créer le dossier logs s'il n'existe pas
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configurer le logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "config.log"),
                logging.StreamHandler()
            ]
        )
    
    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier YAML"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config_data = yaml.safe_load(file) or {}
            else:
                # Créer le fichier de config par défaut s'il n'existe pas
                self._create_default_config()
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            self.config_data = {}
    
    def _create_default_config(self) -> None:
        """Crée un fichier de configuration par défaut"""
        default_config = {
            'ollama': {
                'host': 'localhost',
                'port': 11434,
                'base_url': 'http://localhost:11434',
                'default_model': 'llama3.2',
                'timeout': 30
            },
            'auth': {
                'auto_login': False,
                'remember_user': True,
                'session_timeout': 3600
            },
            'network': {
                'api_server': {
                    'host': '0.0.0.0',
                    'port': 8000,
                    'auto_start': False
                },
                'tunnel': {
                    'enabled': False,
                    'provider': 'localhost.run',
                    'auto_start': False
                }
            },
            'memory': {
                'database_path': 'data/locrit_memory.db',
                'max_messages': 10000,
                'embedding_model': 'all-MiniLM-L6-v2'
            },
            'ui': {
                'theme': 'dark',
                'auto_refresh': True,
                'refresh_interval': 5
            }
        }
        
        self.config_data = default_config
        self.save_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration en utilisant un chemin pointé
        Exemple: get('ollama.host') retourne localhost
        """
        keys = key_path.split('.')
        value = self.config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Définit une valeur de configuration en utilisant un chemin pointé
        Exemple: set('ollama.host', 'remote-server')
        """
        keys = key_path.split('.')
        config = self.config_data
        
        # Navigue jusqu'à l'avant-dernier niveau
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Définit la valeur finale
        config[keys[-1]] = value
    
    def save_config(self) -> bool:
        """Sauvegarde la configuration dans le fichier YAML"""
        try:
            # Créer le répertoire parent si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config_data, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Retourne la configuration complète d'Ollama depuis .env et config.yaml"""
        # Priorité au fichier de config pour l'interface web, fallback vers variables d'environnement
        config = {
            'host': 'localhost',
            'port': 11434,
            'base_url': self.get('ollama.base_url') or os.getenv('OLLAMA_HOST') or 'http://localhost:11434',
            'default_model': self.get('ollama.default_model') or os.getenv('OLLAMA_DEFAULT_MODEL') or 'llama3.2',
            'timeout': self.get('ollama.timeout', 30)
        }
        
        # Extraire host et port depuis base_url si fourni
        if config['base_url']:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(config['base_url'])
                config['host'] = parsed.hostname or 'localhost'
                config['port'] = parsed.port or 11434
            except:
                logger.warning("⚠️ Erreur parsing OLLAMA_HOST, utilisation des valeurs par défaut")
                
        logger.info(f"🤖 Configuration Ollama: {config['base_url']} | Modèle: {config['default_model']}")
        return config
        
    def get_firebase_config(self) -> Dict[str, str]:
        """Récupère la configuration Firebase depuis les variables d'environnement"""
        firebase_config = {
            'apiKey': os.getenv('FIREBASE_API_KEY', ''),
            'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN', ''),
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL', ''),
            'projectId': os.getenv('FIREBASE_PROJECT_ID', ''),
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', ''),
            'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId': os.getenv('FIREBASE_APP_ID', ''),
            'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID', '')
        }
        
        # Log des clés manquantes pour debug
        missing_keys = [key for key, value in firebase_config.items() if not value]
        if missing_keys:
            logger.warning(f"⚠️ Clés Firebase manquantes dans .env: {missing_keys}")
        else:
            logger.info("🔥 Configuration Firebase chargée depuis .env")
            
        return firebase_config
    
    def get_ollama_url(self) -> str:
        """Retourne l'URL complète du serveur Ollama"""
        return self.get('ollama.base_url', 'http://localhost:11434')
    
    def set_ollama_url(self, url: str) -> None:
        """Définit l'URL du serveur Ollama"""
        self.set('ollama.base_url', url)
        # Mettre à jour aussi host et port si possible
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.hostname:
                self.set('ollama.host', parsed.hostname)
            if parsed.port:
                self.set('ollama.port', parsed.port)
        except:
            pass
    
    def get_network_config(self) -> Dict[str, Any]:
        """Retourne la configuration réseau"""
        return self.get('network', {})
    
    def get_api_server_config(self) -> Dict[str, Any]:
        """Retourne la configuration du serveur API"""
        return self.get('network.api_server', {})
    
    def get_tunnel_config(self) -> Dict[str, Any]:
        """Retourne la configuration du tunnel"""
        return self.get('network.tunnel', {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Retourne la configuration de la mémoire"""
        return self.get('memory', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Retourne la configuration de l'interface"""
        return self.get('ui', {})
    
    def get_locrits_default_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres par défaut pour un nouveau Locrit"""
        return self.get('locrits.default_settings', {
            'open_to': {
                'humans': True,
                'locrits': True,
                'invitations': True,
                'internet': False,
                'platform': False
            },
            'access_to': {
                'logs': True,
                'quick_memory': True,
                'full_memory': False,
                'llm_info': True
            }
        })
    
    def update_locrit_settings(self, locrit_name: str, settings: Dict[str, Any]) -> None:
        """Met à jour les paramètres d'un Locrit spécifique avec logs détaillés"""
        # Ajouter/mettre à jour le timestamp de modification
        settings['updated_at'] = self._get_current_timestamp()
        
        # Vérifier si c'est une création ou une mise à jour
        existing_settings = self.get(f'locrits.instances.{locrit_name}')
        is_new = existing_settings is None
        
        if is_new:
            self.logger.info(f"🆕 Création nouveau Locrit: {locrit_name}")
            self.logger.info(f"   📝 Description: {settings.get('description', 'N/A')}")
            self.logger.info(f"   🌐 Adresse: {settings.get('public_address', 'N/A')}")
            if 'created_at' not in settings:
                settings['created_at'] = settings['updated_at']
        else:
            self.logger.info(f"🔄 Mise à jour Locrit: {locrit_name}")
            
            # Log des changements spécifiques
            self._log_locrit_changes(locrit_name, existing_settings, settings)
        
        key_path = f'locrits.instances.{locrit_name}'
        self.set(key_path, settings)
        
        self.logger.info(f"💾 Locrit {locrit_name} sauvegardé en local")

    def _log_locrit_changes(self, locrit_name: str, old_settings: Dict, new_settings: Dict):
        """Log les changements spécifiques d'un Locrit"""
        changes = []
        
        # Vérifier les changements principaux
        for key in ['description', 'public_address', 'active', 'ollama_model']:
            old_val = old_settings.get(key)
            new_val = new_settings.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
        
        # Vérifier les changements dans open_to
        old_open = old_settings.get('open_to', {})
        new_open = new_settings.get('open_to', {})
        for key in old_open.keys() | new_open.keys():
            if old_open.get(key) != new_open.get(key):
                changes.append(f"open_to.{key}: {old_open.get(key)} → {new_open.get(key)}")
        
        # Vérifier les changements dans access_to
        old_access = old_settings.get('access_to', {})
        new_access = new_settings.get('access_to', {})
        for key in old_access.keys() | new_access.keys():
            if old_access.get(key) != new_access.get(key):
                changes.append(f"access_to.{key}: {old_access.get(key)} → {new_access.get(key)}")
        
        if changes:
            self.logger.info(f"   🔧 Changements: {', '.join(changes)}")
        else:
            self.logger.info(f"   ✨ Mise à jour timestamp seulement")
    
    def get_locrit_settings(self, locrit_name: str) -> Dict[str, Any]:
        """Récupère les paramètres d'un Locrit spécifique"""
        settings = self.get(f'locrits.instances.{locrit_name}')
        if settings is None:
            self.logger.warning(f"⚠️ Locrit {locrit_name} non trouvé, utilisation des paramètres par défaut")
            return None
        
        self.logger.debug(f"📖 Lecture Locrit: {locrit_name}")
        return settings
    
    def list_locrits(self) -> list[str]:
        """Liste tous les Locrits configurés"""
        instances = self.get('locrits.instances', {})
        locrit_names = list(instances.keys())
        self.logger.info(f"📋 Locrits locaux trouvés: {len(locrit_names)} - {locrit_names}")
        return locrit_names
    
    def delete_locrit(self, locrit_name: str) -> bool:
        """Supprime un Locrit de la configuration"""
        instances = self.get('locrits.instances', {})
        if locrit_name in instances:
            del instances[locrit_name]
            self.set('locrits.instances', instances)
            self.logger.info(f"🗑️ Locrit supprimé: {locrit_name}")
            return True
        else:
            self.logger.warning(f"⚠️ Tentative de suppression d'un Locrit inexistant: {locrit_name}")
            return False

    def save_config(self) -> bool:
        """Sauvegarde la configuration avec logs détaillés"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(self.config_data, file, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"💾 Configuration sauvegardée: {self.config_path}")
            
            # Log du nombre de Locrits
            locrits_count = len(self.get('locrits.instances', {}))
            self.logger.info(f"📊 Nombre total de Locrits: {locrits_count}")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return False

    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO avec timezone"""
        return datetime.now(timezone.utc).isoformat()
    
    def reload_config(self) -> None:
        """Recharge la configuration depuis le fichier"""
        self._load_config()


# Instance globale du service de configuration
config_service = ConfigService()
