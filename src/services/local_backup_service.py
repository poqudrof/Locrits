"""
Service de sauvegarde locale pour Locrit
Gère les sauvegardes des sessions, configs Ollama et données locales
"""

import os
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from .config_service import config_service

logger = logging.getLogger(__name__)


class LocalBackupService:
    """Service de gestion des sauvegardes locales"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path("data/backups")
        self.session_backup_dir = self.backup_dir / "sessions"
        self.config_backup_dir = self.backup_dir / "configs"
        self.locrits_backup_dir = self.backup_dir / "locrits"
        
        # Créer les dossiers de sauvegarde
        self._ensure_backup_directories()
    
    def _ensure_backup_directories(self):
        """Assure que les dossiers de sauvegarde existent"""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.session_backup_dir.mkdir(exist_ok=True)
            self.config_backup_dir.mkdir(exist_ok=True)
            self.locrits_backup_dir.mkdir(exist_ok=True)
            self.logger.info("📁 Dossiers de sauvegarde créés")
        except Exception as e:
            self.logger.error(f"❌ Erreur création dossiers sauvegarde: {e}")
    
    def backup_session(self, session_data: dict, user_id: str = None) -> bool:
        """Sauvegarde une session Firebase"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            user_suffix = f"_{user_id[:8]}" if user_id else ""
            filename = f"session_{timestamp}{user_suffix}.json"
            backup_path = self.session_backup_dir / filename
            
            # Ajouter métadonnées de sauvegarde
            backup_data = {
                "backup_timestamp": timestamp,
                "user_id": user_id,
                "session_data": session_data
            }
            
            print(f"📝 FILE WRITE: {backup_path} (mode: w, type: json)")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"✅ FILE WRITE: {backup_path} completed")

            self.logger.info(f"💾 Session sauvegardée: {filename}")
            
            # Nettoyer les anciennes sauvegardes (garder les 10 dernières)
            self._cleanup_old_backups(self.session_backup_dir, max_files=10)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde session: {e}")
            return False
    
    def restore_latest_session(self, user_id: str = None) -> Optional[dict]:
        """Restaure la dernière session sauvegardée"""
        try:
            # Chercher les fichiers de session
            session_files = list(self.session_backup_dir.glob("session_*.json"))
            
            if not session_files:
                self.logger.info("ℹ️ Aucune session sauvegardée trouvée")
                return None
            
            # Trier par date de modification (plus récent en premier)
            session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Si user_id spécifié, chercher une session pour cet utilisateur
            target_file = None
            if user_id:
                for file in session_files:
                    if user_id[:8] in file.name:
                        target_file = file
                        break
            
            # Sinon prendre le plus récent
            if not target_file:
                target_file = session_files[0]
            
            print(f"📖 FILE READ: {target_file} (mode: r, type: json)")
            with open(target_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            session_data = backup_data.get('session_data', {})
            self.logger.info(f"📥 Session restaurée: {target_file.name}")
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"❌ Erreur restauration session: {e}")
            return None
    
    def backup_ollama_config(self) -> bool:
        """Sauvegarde la configuration Ollama actuelle"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"ollama_config_{timestamp}.json"
            backup_path = self.config_backup_dir / filename
            
            # Récupérer la config Ollama complète
            ollama_config = config_service.get_ollama_config()
            
            backup_data = {
                "backup_timestamp": timestamp,
                "config_type": "ollama",
                "ollama_config": ollama_config
            }
            
            print(f"📝 FILE WRITE: {backup_path} (mode: w, type: json)")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"✅ FILE WRITE: {backup_path} completed")

            self.logger.info(f"💾 Config Ollama sauvegardée: {filename}")
            
            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups(self.config_backup_dir, max_files=5, pattern="ollama_config_*.json")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde config Ollama: {e}")
            return False
    
    def backup_locrits_data(self) -> bool:
        """Sauvegarde tous les Locrits locaux"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"locrits_backup_{timestamp}.json"
            backup_path = self.locrits_backup_dir / filename
            
            # Récupérer tous les Locrits
            locrits = config_service.list_locrits()
            locrits_data = {}
            
            for locrit_name in locrits:
                settings = config_service.get_locrit_settings(locrit_name)
                if settings:
                    locrits_data[locrit_name] = settings
            
            backup_data = {
                "backup_timestamp": timestamp,
                "config_type": "locrits",
                "locrits_count": len(locrits_data),
                "locrits_data": locrits_data
            }
            
            print(f"📝 FILE WRITE: {backup_path} (mode: w, type: json)")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"✅ FILE WRITE: {backup_path} completed")

            self.logger.info(f"💾 {len(locrits_data)} Locrits sauvegardés: {filename}")
            
            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups(self.locrits_backup_dir, max_files=5, pattern="locrits_backup_*.json")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde Locrits: {e}")
            return False
    
    def restore_locrits_data(self, backup_filename: str = None) -> bool:
        """Restaure les Locrits depuis une sauvegarde"""
        try:
            if backup_filename:
                backup_path = self.locrits_backup_dir / backup_filename
            else:
                # Prendre la sauvegarde la plus récente
                backup_files = list(self.locrits_backup_dir.glob("locrits_backup_*.json"))
                if not backup_files:
                    self.logger.warning("⚠️ Aucune sauvegarde de Locrits trouvée")
                    return False
                backup_path = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            print(f"📖 FILE READ: {backup_path} (mode: r, type: json)")
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            locrits_data = backup_data.get('locrits_data', {})
            
            # Restaurer chaque Locrit
            restored_count = 0
            for locrit_name, settings in locrits_data.items():
                config_service.update_locrit_settings(locrit_name, settings)
                restored_count += 1
            
            # Sauvegarder la configuration
            config_service.save_config()
            
            self.logger.info(f"📥 {restored_count} Locrits restaurés depuis: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur restauration Locrits: {e}")
            return False
    
    def _cleanup_old_backups(self, directory: Path, max_files: int = 10, pattern: str = "*.json"):
        """Nettoie les anciennes sauvegardes en gardant seulement les plus récentes"""
        try:
            backup_files = list(directory.glob(pattern))
            
            if len(backup_files) <= max_files:
                return
            
            # Trier par date de modification
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Supprimer les fichiers excédentaires
            files_to_delete = backup_files[max_files:]
            for file in files_to_delete:
                file.unlink()
                self.logger.debug(f"🗑️ Ancienne sauvegarde supprimée: {file.name}")
            
            if files_to_delete:
                self.logger.info(f"🧹 {len(files_to_delete)} anciennes sauvegardes nettoyées")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage sauvegardes: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Retourne le statut des sauvegardes"""
        try:
            status = {
                "session_backups": len(list(self.session_backup_dir.glob("session_*.json"))),
                "ollama_backups": len(list(self.config_backup_dir.glob("ollama_config_*.json"))),
                "locrits_backups": len(list(self.locrits_backup_dir.glob("locrits_backup_*.json"))),
                "backup_dir_size": self._get_directory_size(self.backup_dir)
            }
            
            # Dernières sauvegardes
            for backup_type, directory, pattern in [
                ("latest_session", self.session_backup_dir, "session_*.json"),
                ("latest_ollama", self.config_backup_dir, "ollama_config_*.json"),
                ("latest_locrits", self.locrits_backup_dir, "locrits_backup_*.json")
            ]:
                files = list(directory.glob(pattern))
                if files:
                    latest_file = max(files, key=lambda x: x.stat().st_mtime)
                    status[backup_type] = {
                        "filename": latest_file.name,
                        "timestamp": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
                    }
                else:
                    status[backup_type] = None
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Erreur statut sauvegardes: {e}")
            return {}
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calcule la taille d'un dossier en octets"""
        try:
            total_size = 0
            for file in directory.rglob('*'):
                if file.is_file():
                    total_size += file.stat().st_size
            return total_size
        except:
            return 0


# Instance globale
local_backup_service = LocalBackupService()
