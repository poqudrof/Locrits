#!/usr/bin/env python3
"""
Script de test pour vérifier les logs et la synchronisation
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.append(str(Path(__file__).parent / "src"))

from services.config_service import config_service
from services.sync_service import sync_service
from services.session_service import session_service


async def test_logs_and_sync():
    """Test des logs et de la synchronisation"""
    
    print("🔍 Test des logs et synchronisation Locrit")
    print("=" * 50)
    
    # 1. Tester la création d'un Locrit avec logs
    print("\n1. 📝 Test création Locrit avec logs...")
    
    test_locrit = {
        'name': 'Test Logger',
        'description': 'Locrit de test pour les logs',
        'public_address': 'test.localhost.run',
        'active': False,
        'open_to': {
            'humans': True,
            'locrits': False,
            'invitations': True,
            'internet': False,
            'platform': False
        },
        'access_to': {
            'logs': True,
            'quick': True,
            'full': False,
            'llm': True
        },
        'ollama_model': 'llama3.2',
        'memory_enabled': True,
        'search_enabled': True
    }
    
    # Créer le Locrit (cela devrait générer des logs)
    config_service.update_locrit_settings("Test Logger", test_locrit)
    config_service.save_config()
    
    print("✅ Locrit de test créé")
    
    # 2. Lister les Locrits (logs)
    print("\n2. 📋 Test listage des Locrits...")
    locrits = config_service.list_locrits()
    print(f"✅ {len(locrits)} Locrits trouvés: {locrits}")
    
    # 3. Tester la session (si disponible)
    print("\n3. 🔐 Test session...")
    session_info = session_service.get_session_info()
    print(f"📱 Session: {session_info}")
    
    # 4. Test de la synchronisation (sans vraiment envoyer au serveur)
    print("\n4. 🔄 Test synchronisation (simulation)...")
    
    # Simuler des informations d'auth pour les tests
    mock_auth = {
        "localId": "test-user-123",
        "uid": "test-user-123",
        "email": "test@locrit.com",
        "idToken": "mock-token-for-testing",
        "refreshToken": "mock-refresh-token",
        "is_anonymous": False
    }
    
    sync_service.set_auth_info(mock_auth)
    
    try:
        # Cette sync échouera (pas de serveur) mais testera les logs
        result = await sync_service.sync_all_locrits()
        print(f"📊 Résultat sync: {result.get('status')}")
        
        if result.get('errors'):
            print(f"⚠️ Erreurs attendues (pas de serveur): {len(result['errors'])}")
            
    except Exception as e:
        print(f"⚠️ Erreur sync attendue (pas de serveur): {str(e)[:100]}...")
    
    # 5. Nettoyer le Locrit de test
    print("\n5. 🧹 Nettoyage...")
    success = config_service.delete_locrit("Test Logger")
    if success:
        config_service.save_config()
        print("✅ Locrit de test supprimé")
    
    print("\n" + "=" * 50)
    print("🎯 Test terminé ! Vérifiez les logs dans logs/config.log")
    print("\nCommandes utiles :")
    print("  tail -f logs/config.log     # Surveiller les logs")
    print("  cat logs/config.log         # Voir tous les logs")
    print("  ls -la data/               # Voir les fichiers de données")


if __name__ == "__main__":
    asyncio.run(test_logs_and_sync())
