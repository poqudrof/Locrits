"""
Service de session Firebase pour Locrit
Sauvegarde et restaure les sessions d'authentification
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class SessionService:
    """Service de gestion des sessions Firebase persistantes"""
    
    def __init__(self, session_file: str = "data/session.json"):
        self.session_file = Path(session_file)
        self.session_data: Optional[Dict[str, Any]] = None
        
        # Créer le dossier data s'il n'existe pas
        self.session_file.parent.mkdir(exist_ok=True)
        
    def save_session(self, auth_result: Dict[str, Any]) -> bool:
        """
        Sauvegarde une session d'authentification Firebase
        
        Args:
            auth_result: Résultat de l'authentification Firebase
            
        Returns:
            True si la sauvegarde réussit
        """
        try:
            # Extraire les informations importantes
            session_data = {
                "user_id": auth_result.get("localId") or auth_result.get("uid"),
                "email": auth_result.get("email"),
                "id_token": auth_result.get("idToken"),
                "refresh_token": auth_result.get("refreshToken"),
                "expires_in": auth_result.get("expiresIn"),
                "display_name": auth_result.get("displayName"),
                "is_anonymous": auth_result.get("is_anonymous", False),
                "provider_id": auth_result.get("providerId", "anonymous" if auth_result.get("is_anonymous") else "password"),
                "saved_at": datetime.now().isoformat(),
                "expires_at": self._calculate_expiry(auth_result.get("expiresIn"))
            }
            
            # Sauvegarder dans le fichier JSON
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            # Sauvegarder également dans les backups locaux
            try:
                from .local_backup_service import local_backup_service
                local_backup_service.backup_session(session_data, auth_result.get("localId"))
            except Exception as backup_error:
                print(f"⚠️ Erreur sauvegarde backup session: {backup_error}")
            
            self.session_data = session_data
            print(f"✅ Session sauvegardée: {session_data['email'] or 'Anonyme'}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde session: {e}")
            return False
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Charge une session sauvegardée si elle est valide
        
        Returns:
            Données de session si valides, None sinon
        """
        try:
            if not self.session_file.exists():
                return None
                
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Vérifier si la session est encore valide
            if self._is_session_valid(session_data):
                self.session_data = session_data
                print(f"✅ Session restaurée: {session_data['email'] or 'Anonyme'}")
                return session_data
            else:
                print("⚠️ Session expirée, suppression...")
                self.clear_session()
                return None
                
        except Exception as e:
            print(f"❌ Erreur chargement session: {e}")
            return None
    
    def refresh_session(self, auth_service) -> Optional[Dict[str, Any]]:
        """
        Tente de rafraîchir une session expirée ou proche de l'expiration

        Args:
            auth_service: Service d'authentification Firebase

        Returns:
            Nouvelles données de session si le refresh réussit, données existantes si pas besoin de refresh
        """
        # S'assurer que session_data est chargé
        if not self.session_data:
            self.session_data = self.load_session()

        if not self.session_data or not self.session_data.get("refresh_token"):
            return None

        # Vérifier si la session a besoin d'être rafraîchie
        if self._is_session_valid(self.session_data) and not self._is_session_near_expiry(self.session_data):
            return self.session_data  # Pas besoin de rafraîchir

        try:
            # Utiliser le refresh token pour obtenir un nouveau token
            refresh_result = auth_service.refresh_token(self.session_data["refresh_token"])

            if refresh_result.get("success"):
                # Mettre à jour les données de session
                new_auth_data = refresh_result["user"]

                # Convertir au format de session
                session_format_data = {
                    "user_id": new_auth_data.get("localId") or new_auth_data.get("uid"),
                    "email": new_auth_data.get("email"),
                    "id_token": new_auth_data.get("idToken"),
                    "refresh_token": new_auth_data.get("refreshToken"),
                    "expires_in": new_auth_data.get("expiresIn"),
                    "display_name": new_auth_data.get("displayName"),
                    "is_anonymous": new_auth_data.get("is_anonymous", self.session_data.get("is_anonymous", False)),
                    "provider_id": new_auth_data.get("providerId", self.session_data.get("provider_id", "unknown")),
                    "saved_at": datetime.now().isoformat(),
                    "expires_at": self._calculate_expiry(new_auth_data.get("expiresIn"))
                }

                # Sauvegarder dans le fichier JSON
                with open(self.session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_format_data, f, indent=2)

                # Sauvegarder également dans les backups locaux
                try:
                    from .local_backup_service import local_backup_service
                    local_backup_service.backup_session(session_format_data, session_format_data.get("user_id"))
                except Exception as backup_error:
                    print(f"⚠️ Erreur sauvegarde backup session: {backup_error}")

                self.session_data = session_format_data
                print("🔄 Session rafraîchie avec succès")
                return session_format_data
            else:
                print("❌ Échec du rafraîchissement, session supprimée")
                self.clear_session()
                return None

        except Exception as e:
            print(f"❌ Erreur rafraîchissement session: {e}")
            self.clear_session()
            return None
    
    def clear_session(self) -> None:
        """Supprime la session sauvegardée"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            self.session_data = None
            print("🗑️ Session supprimée")
        except Exception as e:
            print(f"❌ Erreur suppression session: {e}")
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Retourne la session actuelle si elle est valide"""
        if self.session_data and self._is_session_valid(self.session_data):
            return self.session_data
        return None
    
    def is_logged_in(self) -> bool:
        """Vérifie si l'utilisateur est connecté avec une session valide"""
        return self.get_current_session() is not None
    
    def get_user_info(self) -> Dict[str, Any]:
        """Retourne les informations utilisateur de la session actuelle"""
        session = self.get_current_session()
        if session:
            return {
                "user_id": session.get("user_id"),
                "email": session.get("email", "Utilisateur anonyme"),
                "display_name": session.get("display_name"),
                "is_anonymous": session.get("is_anonymous", False),
                "provider_id": session.get("provider_id", "unknown")
            }
        return {}
    
    def _calculate_expiry(self, expires_in: Optional[str]) -> Optional[str]:
        """Calcule la date d'expiration à partir de expires_in"""
        if not expires_in:
            # Session anonyme ou sans expiration explicite
            # Durer 7 jours par défaut
            expiry = datetime.now() + timedelta(days=7)
            return expiry.isoformat()
        
        try:
            # expires_in est en secondes
            seconds = int(expires_in)
            expiry = datetime.now() + timedelta(seconds=seconds)
            return expiry.isoformat()
        except (ValueError, TypeError):
            # Si on ne peut pas parser, utiliser 1 heure par défaut
            expiry = datetime.now() + timedelta(hours=1)
            return expiry.isoformat()
    
    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Vérifie si une session est encore valide"""
        try:
            expires_at = session_data.get("expires_at")
            if not expires_at:
                return False

            expiry_date = datetime.fromisoformat(expires_at)

            # Vérifier si la session n'est pas expirée (sans marge pour permettre le refresh)
            return datetime.now() < expiry_date

        except Exception as e:
            print(f"⚠️ Erreur validation session: {e}")
            return False

    def _is_session_near_expiry(self, session_data: Dict[str, Any]) -> bool:
        """Vérifie si une session approche de son expiration (moins de 10 minutes)"""
        try:
            expires_at = session_data.get("expires_at")
            if not expires_at:
                return True

            expiry_date = datetime.fromisoformat(expires_at)
            margin = timedelta(minutes=10)
            return datetime.now() > (expiry_date - margin)

        except Exception as e:
            return True
    
    def get_session_info(self) -> str:
        """Retourne des informations lisibles sur la session"""
        session = self.get_current_session()
        if not session:
            return "❌ Aucune session active"
        
        user_type = "👤 Anonyme" if session.get("is_anonymous") else "🔐 Authentifié"
        email = session.get("email", "Utilisateur anonyme")
        expires_at = session.get("expires_at", "Inconnue")
        
        try:
            expiry_date = datetime.fromisoformat(expires_at)
            time_left = expiry_date - datetime.now()
            
            if time_left.total_seconds() > 0:
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                time_str = f"{hours_left}h {minutes_left}m"
            else:
                time_str = "Expirée"
        except:
            time_str = "Inconnue"
        
        return f"{user_type} - {email} - Expire dans: {time_str}"


# Instance globale du service de session
session_service = SessionService()
