#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration Firebase/Firestore

Ce script teste :
- La connexion à Firebase
- L'enregistrement d'un locrit de test
- La découverte de locrits
- La mise à jour de statut
- La sauvegarde de conversation

Usage:
    python test_firebase.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from services.firebase_service import FirebaseService
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("Assurez-vous que le FirebaseService est implémenté dans src/services/")
    sys.exit(1)

# Charger les variables d'environnement
load_dotenv()

async def test_firebase_connection():
    """Test la connexion Firebase et les opérations de base"""
    
    print("🔥 Test de la configuration Firebase pour Locrit")
    print("=" * 50)
    
    # Vérifier les variables d'environnement critiques
    required_env_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {missing_vars}")
        print("💡 Assurez-vous que le fichier .env est configuré correctement")
        return False
    
    try:
        # Initialiser le service Firebase
        print("🔗 Initialisation de Firebase...")
        firebase_service = FirebaseService()
        print("✅ Firebase initialisé avec succès")
        
        # Test 1: Enregistrement d'un locrit
        print("\n📝 Test 1: Enregistrement d'un locrit de test...")
        test_locrit = {
            "name": "test-locrit-firebase",
            "host": "localhost",
            "port": 8000,
            "status": "online",
            "capabilities": ["chat", "search", "memory"],
            "model": "llama3.2:latest",
            "version": "1.0.0",
            "description": "Locrit de test pour Firebase"
        }
        
        locrit_id = await firebase_service.register_locrit(test_locrit)
        print(f"✅ Locrit enregistré avec l'ID: {locrit_id}")
        
        # Test 2: Découverte de locrits
        print("\n🔍 Test 2: Découverte des locrits...")
        locrits = await firebase_service.discover_locrits()
        print(f"✅ Découverte réussie: {len(locrits)} locrit(s) trouvé(s)")
        
        for i, locrit in enumerate(locrits):
            print(f"  {i+1}. {locrit.get('name', 'Sans nom')} - {locrit.get('status', 'Statut inconnu')}")
        
        # Test 3: Mise à jour du statut
        print("\n🔄 Test 3: Mise à jour du statut...")
        await firebase_service.update_locrit_status(locrit_id, {
            "status": "busy",
            "current_task": "Testing Firebase connection"
        })
        print("✅ Statut mis à jour avec succès")
        
        # Test 4: Sauvegarde d'une conversation
        print("\n💬 Test 4: Sauvegarde d'une conversation...")
        test_conversation = {
            "participants": [locrit_id, "user-test"],
            "messages": [
                {
                    "sender": "user-test",
                    "content": "Hello, this is a test message",
                    "timestamp": "2024-01-01T10:00:00Z"
                },
                {
                    "sender": locrit_id,
                    "content": "Hello! I'm a test locrit. Firebase connection is working!",
                    "timestamp": "2024-01-01T10:00:05Z"
                }
            ],
            "title": "Test Conversation Firebase",
            "type": "test"
        }
        
        conversation_id = await firebase_service.save_conversation(test_conversation)
        print(f"✅ Conversation sauvegardée avec l'ID: {conversation_id}")
        
        # Test 5: Récupération des conversations
        print("\n📖 Test 5: Récupération des conversations...")
        conversations = await firebase_service.get_conversations(locrit_id, limit=10)
        print(f"✅ Récupération réussie: {len(conversations)} conversation(s) trouvée(s)")
        
        # Test 6: Nettoyage (mise à jour finale du statut)
        print("\n🧹 Test 6: Nettoyage final...")
        await firebase_service.update_locrit_status(locrit_id, {
            "status": "offline",
            "current_task": "Test completed"
        })
        print("✅ Nettoyage terminé")
        
        print("\n" + "=" * 50)
        print("🎉 Tous les tests Firebase ont réussi!")
        print("✅ La configuration Firebase est correcte")
        print("✅ Firestore est accessible et fonctionnel")
        print("✅ Les opérations CRUD fonctionnent")
        print("\n💡 Vous pouvez maintenant intégrer Firebase dans l'application Locrit")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests Firebase: {e}")
        print("\n🔧 Vérifications à effectuer:")
        print("1. Le fichier .env est-il correctement configuré ?")
        print("2. Les credentials Firebase sont-ils valides ?")
        print("3. Firestore est-il activé dans la console Firebase ?")
        print("4. Les règles de sécurité permettent-elles l'écriture ?")
        return False

async def test_environment_variables():
    """Test spécifique des variables d'environnement"""
    print("\n🔍 Vérification des variables d'environnement...")
    
    env_vars = {
        "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
        "FIREBASE_CLIENT_EMAIL": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "FIREBASE_PRIVATE_KEY_ID": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "FIREBASE_WEB_API_KEY": os.getenv("FIREBASE_WEB_API_KEY"),
    }
    
    for var_name, var_value in env_vars.items():
        if var_value:
            # Masquer les valeurs sensibles
            if "KEY" in var_name:
                display_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: Non définie")

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage des tests Firebase pour Locrit")
    
    # Vérifier que le fichier .env existe
    if not os.path.exists('.env'):
        print("❌ Fichier .env non trouvé!")
        print("💡 Créez un fichier .env basé sur .env.example")
        print("💡 Ou utilisez extract_firebase_config.py pour générer la configuration")
        sys.exit(1)
    
    try:
        # Tester les variables d'environnement
        asyncio.run(test_environment_variables())
        
        # Tester Firebase
        success = asyncio.run(test_firebase_connection())
        
        if success:
            print("\n🏁 Tests terminés avec succès!")
            sys.exit(0)
        else:
            print("\n💥 Tests échoués!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
