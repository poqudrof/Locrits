#!/usr/bin/env python3
"""
Test de l'interface d'authentification Locrit
Ce script teste l'écran d'authentification en mode démo (sans Firebase réel)
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Charger les variables d'environnement
load_dotenv()

class MockAuthService:
    """Service d'authentification simulé pour les tests"""
    
    def __init__(self):
        self.current_user = None
        self.auth_token = None
    
    def sign_in_anonymous(self):
        """Connexion anonyme simulée"""
        self.current_user = {
            "localId": "demo_user_12345",
            "idToken": "demo_token_abcdef"
        }
        self.auth_token = "demo_token_abcdef"
        
        return {
            "success": True,
            "user_id": "demo_user_12345",
            "email": "anonyme",
            "auth_type": "anonymous",
            "token": "demo_token_abcdef"
        }
    
    def sign_in_with_email(self, email, password):
        """Connexion email simulée"""
        # Simulation basique
        if email == "test@example.com" and password == "password123":
            self.current_user = {
                "localId": "demo_user_email",
                "email": email,
                "idToken": "demo_token_email"
            }
            self.auth_token = "demo_token_email"
            
            return {
                "success": True,
                "user_id": "demo_user_email",
                "email": email,
                "auth_type": "email",
                "token": "demo_token_email"
            }
        else:
            return {
                "success": False,
                "error": "Email ou mot de passe incorrect (utilisez test@example.com / password123)"
            }
    
    def create_user_with_email(self, email, password):
        """Création de compte simulée"""
        if "@" in email and len(password) >= 6:
            self.current_user = {
                "localId": "demo_user_new",
                "email": email,
                "idToken": "demo_token_new"
            }
            self.auth_token = "demo_token_new"
            
            return {
                "success": True,
                "user_id": "demo_user_new",
                "email": email,
                "auth_type": "email",
                "token": "demo_token_new"
            }
        else:
            return {
                "success": False,
                "error": "Email invalide ou mot de passe trop court"
            }
    
    def reset_password(self, email):
        """Réinitialisation de mot de passe simulée"""
        if "@" in email:
            return {
                "success": True,
                "message": f"Email de réinitialisation envoyé à {email} (simulation)"
            }
        else:
            return {
                "success": False,
                "error": "Adresse email invalide"
            }
    
    def is_authenticated(self):
        return self.current_user is not None
    
    def get_user_info(self):
        if self.current_user:
            return {
                "user_id": self.current_user["localId"],
                "email": self.current_user.get("email", "anonyme"),
                "auth_type": "anonymous" if not self.current_user.get("email") else "email"
            }
        return None

def test_auth_screen():
    """Test de l'écran d'authentification"""
    from textual.app import App
    from ui.auth_screen import AuthScreen
    
    class TestAuthApp(App):
        def on_mount(self):
            # Utiliser le service d'auth simulé
            mock_auth_service = MockAuthService()
            auth_screen = AuthScreen(mock_auth_service)
            self.push_screen(auth_screen)
        
        def _on_auth_success(self, auth_result):
            """Appelé quand l'authentification réussit"""
            self.bell()  # Son de notification
            self.exit(f"✅ Authentification réussie: {auth_result['email']} ({auth_result['auth_type']})")
    
    app = TestAuthApp()
    result = app.run()
    print(f"Résultat du test: {result}")

def test_auth_service():
    """Test du service d'authentification"""
    print("🧪 Test du service d'authentification (mode simulation)")
    print("=" * 50)
    
    auth_service = MockAuthService()
    
    # Test connexion anonyme
    print("1. Test connexion anonyme...")
    result = auth_service.sign_in_anonymous()
    if result["success"]:
        print(f"   ✅ Succès: {result['email']} ({result['auth_type']})")
    else:
        print(f"   ❌ Échec: {result['error']}")
    
    # Test connexion email valide
    print("\n2. Test connexion email (test@example.com / password123)...")
    result = auth_service.sign_in_with_email("test@example.com", "password123")
    if result["success"]:
        print(f"   ✅ Succès: {result['email']} ({result['auth_type']})")
    else:
        print(f"   ❌ Échec: {result['error']}")
    
    # Test connexion email invalide
    print("\n3. Test connexion email invalide...")
    result = auth_service.sign_in_with_email("wrong@example.com", "wrongpass")
    if result["success"]:
        print(f"   ✅ Succès: {result['email']} ({result['auth_type']})")
    else:
        print(f"   ❌ Échec (attendu): {result['error']}")
    
    # Test création de compte
    print("\n4. Test création de compte...")
    result = auth_service.create_user_with_email("new@example.com", "newpassword123")
    if result["success"]:
        print(f"   ✅ Succès: {result['email']} ({result['auth_type']})")
    else:
        print(f"   ❌ Échec: {result['error']}")
    
    # Test réinitialisation
    print("\n5. Test réinitialisation de mot de passe...")
    result = auth_service.reset_password("test@example.com")
    if result["success"]:
        print(f"   ✅ Succès: {result['message']}")
    else:
        print(f"   ❌ Échec: {result['error']}")
    
    print("\n🎉 Tous les tests du service terminés!")

def main():
    print("🔥 Test de l'authentification Firebase pour Locrit")
    print("Mode simulation - aucune connexion Firebase réelle requise")
    print()
    
    choice = input("Que voulez-vous tester ?\n1. Service d'authentification\n2. Interface d'authentification\nChoix (1/2): ")
    
    if choice == "1":
        test_auth_service()
    elif choice == "2":
        print("\n🎨 Lancement de l'interface d'authentification...")
        print("💡 Utilisez test@example.com / password123 pour tester la connexion email")
        test_auth_screen()
    else:
        print("Choix invalide. Relancez le script.")

if __name__ == "__main__":
    main()
