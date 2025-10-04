"""
Service d'authentification Firebase pour Locrit
Gère l'authentification anonyme et par email/mot de passe
"""

import os
import pyrebase
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging
from .comprehensive_logging_service import comprehensive_logger, LogLevel, LogCategory

load_dotenv()
logger = logging.getLogger(__name__)

class AuthService:
    """Service d'authentification Firebase"""
    
    def __init__(self):
        self.firebase = None
        self.auth = None
        self.current_user = None
        self.auth_token = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialise Firebase pour l'authentification"""
        try:
            # Charger la configuration Firebase depuis le ConfigService
            from .config_service import config_service
            config = config_service.get_firebase_config()
            
            # Vérifier que les clés essentielles sont présentes
            required_keys = ["apiKey", "authDomain", "projectId"]
            missing_keys = [key for key in required_keys if not config[key]]
            
            if missing_keys:
                raise ValueError(f"Configuration Firebase manquante dans .env: {missing_keys}")
            
            self.firebase = pyrebase.initialize_app(config)
            self.auth = self.firebase.auth()
            logger.info("🔥 Service d'authentification Firebase initialisé depuis .env")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Firebase Auth: {e}")
            raise
            raise
    
    def sign_in_anonymous(self) -> Dict[str, Any]:
        """Connexion anonyme"""
        try:
            user = self.auth.sign_in_anonymous()
            self.current_user = user
            self.auth_token = user["idToken"]

            logger.info(f"Connexion anonyme réussie: {user['localId'][:8]}...")

            # Log successful anonymous authentication
            comprehensive_logger.log_system_event(
                "auth_success",
                f"Anonymous authentication successful for user {user['localId'][:8]}...",
                data={
                    "auth_type": "anonymous",
                    "user_id": user["localId"],
                    "provider": "anonymous"
                }
            )

            return {
                "success": True,
                "localId": user["localId"],
                "uid": user["localId"],
                "email": None,
                "idToken": user["idToken"],
                "refreshToken": user.get("refreshToken"),
                "expiresIn": user.get("expiresIn"),
                "is_anonymous": True,
                "providerId": "anonymous"
            }

        except Exception as e:
            logger.error(f"Erreur connexion anonyme: {e}")

            # Log failed anonymous authentication
            comprehensive_logger.log_error(
                error=e,
                context="Anonymous authentication",
                additional_data={"auth_type": "anonymous"}
            )

            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_in_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """Connexion avec email et mot de passe"""
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            self.current_user = user
            self.auth_token = user["idToken"]

            logger.info(f"Connexion email réussie: {email}")

            # Log successful email authentication
            comprehensive_logger.log_system_event(
                "auth_success",
                f"Email authentication successful for {email}",
                data={
                    "auth_type": "email",
                    "email": email,
                    "provider": "password"
                }
            )

            return {
                "success": True,
                "localId": user["localId"],
                "uid": user["localId"],
                "email": email,
                "idToken": user["idToken"],
                "refreshToken": user.get("refreshToken"),
                "expiresIn": user.get("expiresIn"),
                "displayName": user.get("displayName"),
                "is_anonymous": False,
                "providerId": "password"
            }

        except Exception as e:
            error_msg = self._parse_auth_error(str(e))
            logger.error(f"Erreur connexion email: {error_msg}")

            # Log failed email authentication
            comprehensive_logger.log_error(
                error=Exception(error_msg),
                context="Email authentication",
                additional_data={
                    "auth_type": "email",
                    "email": email
                }
            )

            return {
                "success": False,
                "error": error_msg
            }
    
    def create_user_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """Création d'un nouveau compte avec email et mot de passe"""
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            self.current_user = user
            self.auth_token = user["idToken"]
            
            logger.info(f"Compte créé avec succès: {email}")
            return {
                "success": True,
                "localId": user["localId"],
                "uid": user["localId"],
                "email": email,
                "idToken": user["idToken"],
                "refreshToken": user.get("refreshToken"),
                "expiresIn": user.get("expiresIn"),
                "displayName": user.get("displayName"),
                "is_anonymous": False,
                "providerId": "password"
            }
            
        except Exception as e:
            error_msg = self._parse_auth_error(str(e))
            logger.error(f"Erreur création compte: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def sign_out(self):
        """Déconnexion"""
        try:
            user_id = self.current_user.get("localId") if self.current_user else "unknown"

            self.current_user = None
            self.auth_token = None
            logger.info("Déconnexion réussie")

            # Log successful sign out
            comprehensive_logger.log_system_event(
                "auth_signout",
                f"User {user_id[:8]}... signed out successfully",
                data={
                    "user_id": user_id,
                    "auth_type": "signout"
                }
            )

        except Exception as e:
            logger.error(f"Erreur déconnexion: {e}")

            # Log sign out error
            comprehensive_logger.log_error(
                error=e,
                context="User sign out",
                additional_data={"auth_type": "signout"}
            )
    
    def refresh_token(self, refresh_token: str = None) -> Dict[str, Any]:
        """Rafraîchit le token d'authentification"""
        try:
            token_to_use = refresh_token or (self.current_user.get("refreshToken") if self.current_user else None)
            
            if not token_to_use:
                return {
                    "success": False,
                    "error": "Aucun refresh token disponible"
                }
            
            refreshed_user = self.auth.refresh(token_to_use)
            
            # Mettre à jour les informations utilisateur
            if self.current_user:
                self.current_user.update(refreshed_user)
            else:
                self.current_user = refreshed_user
                
            self.auth_token = refreshed_user["idToken"]
            
            logger.info("Token rafraîchi avec succès")
            return {
                "success": True,
                "user": refreshed_user
            }
            
        except Exception as e:
            error_msg = self._parse_auth_error(str(e))
            logger.error(f"Erreur rafraîchissement token: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def is_authenticated(self) -> bool:
        """Vérifie si l'utilisateur est connecté"""
        return self.current_user is not None and self.auth_token is not None
    
    def get_user_info(self) -> Optional[Dict[str, str]]:
        """Retourne les informations de l'utilisateur actuel"""
        if not self.is_authenticated():
            return None
        
        return {
            "user_id": self.current_user["localId"],
            "email": self.current_user.get("email", "anonyme"),
            "auth_type": "anonymous" if not self.current_user.get("email") else "email"
        }
    
    def get_auth_token(self) -> Optional[str]:
        """Retourne le token d'authentification actuel"""
        return self.auth_token
    
    def _parse_auth_error(self, error_message: str) -> str:
        """Parse les erreurs Firebase en messages utilisateur"""
        error_map = {
            "INVALID_EMAIL": "Adresse email invalide",
            "EMAIL_NOT_FOUND": "Aucun compte trouvé avec cette adresse email",
            "INVALID_PASSWORD": "Mot de passe incorrect",
            "USER_DISABLED": "Ce compte a été désactivé",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Trop de tentatives. Réessayez plus tard",
            "EMAIL_EXISTS": "Un compte existe déjà avec cette adresse email",
            "OPERATION_NOT_ALLOWED": "L'authentification par email n'est pas activée",
            "WEAK_PASSWORD": "Le mot de passe doit contenir au moins 6 caractères"
        }
        
        for error_code, user_message in error_map.items():
            if error_code in error_message:
                return user_message
        
        return "Erreur d'authentification"
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """Envoie un email de réinitialisation de mot de passe"""
        try:
            self.auth.send_password_reset_email(email)
            logger.info(f"Email de réinitialisation envoyé à: {email}")
            return {
                "success": True,
                "message": f"Email de réinitialisation envoyé à {email}"
            }
            
        except Exception as e:
            error_msg = self._parse_auth_error(str(e))
            logger.error(f"Erreur réinitialisation: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }


# Instance globale du service d'authentification
auth_service = AuthService()
