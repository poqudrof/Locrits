"""
Application Locrit refaite - Interface de gestion des Locrits
Architecture modulaire avec écrans séparés et synchronisation serveur
Sauvegarde automatique des sessions Firebase
"""

import asyncio
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .services.locrit_manager import LocritManager
from .services.auth_service import AuthService
from .services.config_service import config_service
from .services.firestore_admin_service import firestore_admin_service
from .services.session_service import session_service
from .ui.auth_screen import AuthScreen
from .ui.screens import HomeScreen


class LocritApp(App):
    """Application Locrit principale refaite avec architecture modulaire"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .user-info {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("d", "toggle_dark", "Mode sombre"),
        ("q", "quit", "Quitter"),
    ]

    def __init__(self):
        """Initialise l'application Locrit."""
        super().__init__()
        self.auth_service = AuthService()
        self.locrit_manager = LocritManager()
        self.current_user = None

    def compose(self) -> ComposeResult:
        """Interface vide au démarrage - l'auth screen sera pushé"""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Affiche l'écran d'authentification au démarrage avec vérification de session"""
        # Vérifier s'il y a une session sauvegardée
        saved_session = session_service.load_session()
        
        if saved_session:
            # Session valide trouvée, la restaurer directement
            self.notify("🔄 Restauration de la session...")
            asyncio.create_task(self._restore_session(saved_session))
            return
        
        # Pas de session valide, afficher l'écran d'auth
        auto_auth = os.getenv("LOCRIT_AUTO_AUTH", "false").lower() == "true"
        
        if auto_auth:
            asyncio.create_task(self._auto_authenticate())
        else:
            self._show_auth_screen()

    def _show_auth_screen(self):
        """Affiche l'écran d'authentification"""
        auth_screen = AuthScreen(self.auth_service)
        self.push_screen(auth_screen)

    def _restore_auth_service_state(self, session_data: dict):
        """Restaure l'état du service d'authentification à partir des données de session"""
        try:
            # Reconstituer les données utilisateur pour l'AuthService
            auth_user_data = {
                "localId": session_data.get("user_id"),
                "uid": session_data.get("user_id"),
                "email": session_data.get("email"),
                "idToken": session_data.get("id_token"),
                "refreshToken": session_data.get("refresh_token"),
                "expiresIn": session_data.get("expires_in"),
                "displayName": session_data.get("display_name"),
                "is_anonymous": session_data.get("is_anonymous", False),
                "providerId": session_data.get("provider_id", "unknown")
            }

            # Restaurer l'état de l'AuthService
            self.auth_service.current_user = auth_user_data
            self.auth_service.auth_token = session_data.get("id_token")

            print(f"✅ État AuthService restauré pour: {session_data.get('email', 'Anonyme')}")

        except Exception as e:
            print(f"⚠️ Erreur restauration AuthService: {e}")
            # Ne pas lever d'exception, continuer avec une session partielle

    async def _restore_session(self, session_data: dict):
        """Restaure une session Firebase sauvegardée"""
        try:
            if not session_data:
                raise ValueError("Session data is None")

            print(f"🔍 Debug session_data keys: {list(session_data.keys()) if isinstance(session_data, dict) else 'Not a dict'}")
            print(f"🔍 Debug session_data type: {type(session_data)}")

            # Vérifier que session_data est un dictionnaire valide
            if not isinstance(session_data, dict):
                raise ValueError(f"Session data n'est pas un dictionnaire: {type(session_data)}")

            # Vérifier les champs requis
            required_fields = ['user_id', 'email']
            missing_fields = [field for field in required_fields if field not in session_data]
            if missing_fields:
                print(f"⚠️ Champs manquants dans session_data: {missing_fields}")

            self.current_user = session_data

            # Tenter de rafraîchir la session si elle est proche de l'expiration
            try:
                refreshed_session = session_service.refresh_session(self.auth_service)
                if refreshed_session and refreshed_session != session_data:
                    print("🔄 Session rafraîchie automatiquement")
                    session_data = refreshed_session
                elif refreshed_session:
                    print("✅ Session toujours valide")
            except Exception as refresh_error:
                print(f"⚠️ Erreur rafraîchissement: {refresh_error}")
                # Continuer avec la session existante

            # Restaurer l'état du service d'authentification
            self._restore_auth_service_state(session_data)
            
            # Configurer les services avec la session restaurée
            self.locrit_manager.set_auth_info(session_data)
            firestore_admin_service.set_auth_info(session_data)
            
            # Synchronisation initiale
            self.notify("🔄 Synchronisation avec le serveur...")
            print("🔍 Debug: Avant sync_all_locrits")
            try:
                sync_result = await firestore_admin_service.sync_all_locrits()
                print(f"🔍 Debug sync_result: {sync_result}")
                
                if sync_result and isinstance(sync_result, dict) and sync_result.get("status") == "success":
                    self.notify("✅ Session restaurée et synchronisée")
                else:
                    self.notify("✅ Session restaurée (sync en arrière-plan)")
            except Exception as sync_error:
                print(f"⚠️ Erreur de synchronisation: {sync_error}")
                self.notify("✅ Session restaurée (erreur de sync)")
            
            # Afficher l'écran d'accueil
            print("🔍 Debug: Avant création HomeScreen")
            print(f"🔍 Debug: session_data pour HomeScreen: {session_data}")
            home_screen = HomeScreen(session_data)
            self.push_screen(home_screen)
            print("🔍 Debug: Après push_screen")
            
        except Exception as e:
            self.notify(f"❌ Erreur restauration session: {str(e)}")
            print(f"❌ Erreur détaillée restauration session: {e}")
            import traceback
            traceback.print_exc()
            session_service.clear_session()
            self._show_auth_screen()

    async def _auto_authenticate(self):
        """Authentification automatique anonyme"""
        try:
            result = self.auth_service.sign_in_anonymous()
            
            if result["success"]:
                await self._on_auth_success_async(result)
            else:
                self._show_auth_screen()
        except Exception:
            self._show_auth_screen()

    async def _on_auth_success_async(self, auth_result: dict):
        """Appelé quand l'authentification réussit"""
        self.current_user = auth_result
        
        # Sauvegarder la session
        session_service.save_session(auth_result)
        
        # Passer les informations d'auth au LocritManager
        self.locrit_manager.set_auth_info(auth_result)
        
        # Configurer et démarrer la synchronisation
        firestore_admin_service.set_auth_info(auth_result)
        
        # Synchronisation initiale
        self.notify("🔄 Synchronisation avec le serveur...")
        try:
            sync_result = await firestore_admin_service.sync_all_locrits()
            
            if sync_result and isinstance(sync_result, dict):
                if sync_result.get("status") == "success":
                    self.notify("✅ Synchronisation réussie")
                elif sync_result.get("status") == "error":
                    self.notify("⚠️ Erreur de synchronisation (mode local)")
                else:
                    self.notify("✅ Connexion établie")
            else:
                self.notify("✅ Connexion établie (sync en arrière-plan)")
        except Exception as sync_error:
            print(f"⚠️ Erreur de synchronisation: {sync_error}")
            self.notify("✅ Connexion établie (erreur de sync)")
        
        # Démarrer la synchronisation automatique
        # Note: firestore_admin_service n'a pas d'auto-sync
        # sync_service.start_auto_sync()
        
        # Afficher l'écran d'accueil refait
        print(f"🔍 Debug auth_result pour HomeScreen: {auth_result}")
        print(f"🔍 Debug auth_result type: {type(auth_result)}")
        if isinstance(auth_result, dict):
            print(f"🔍 Debug auth_result keys: {list(auth_result.keys())}")
        home_screen = HomeScreen(auth_result)
        self.push_screen(home_screen)

    def _on_auth_success(self, auth_result: dict):
        """Méthode appelée par AuthScreen lors de la réussite de l'auth"""
        asyncio.create_task(self._on_auth_success_async(auth_result))

    def action_toggle_dark(self) -> None:
        """Basculer entre mode sombre et clair."""
        self.toggle_dark()

    def action_quit(self) -> None:
        """Quitter l'application."""
        # Note: firestore_sync_service n'a pas d'auto-sync à arrêter
        # sync_service.stop_auto_sync()
        
        # La session est conservée pour la prochaine fois
        # session_service.clear_session()  # Optionnel pour déconnexion complète
        
        if hasattr(self, 'locrit_manager'):
            asyncio.create_task(self.locrit_manager.shutdown())
        self.exit()

    def logout(self) -> None:
        """Déconnexion manuelle de l'utilisateur"""
        # Nettoyer la session
        session_service.clear_session()
        
        # Déconnecter du service auth
        self.auth_service.sign_out()
        
        # Note: firestore_sync_service n'a pas d'auto-sync à arrêter
        # sync_service.stop_auto_sync()
        
        # Nettoyer les données locales
        self.current_user = None
        
        self.notify("🔐 Déconnexion réussie")
