#!/usr/bin/env python3
"""
Test de synchronisation Firebase Realtime Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.services.firestore_sync_service import firestore_sync_service
from src.services.config_service import config_service

async def test_firebase_sync():
    """Test la synchronisation avec Firebase"""
    print("🧪 Test de synchronisation Firebase")
    print("=" * 50)
    
    # Vérifier la configuration Firebase
    firebase_config = config_service.get_firebase_config()
    print("🔥 Configuration Firebase :")
    for key, value in firebase_config.items():
        status = "✅" if value else "❌"
        print(f"   {key}: {status}")
    
    # Vérifier l'initialisation
    is_configured = firestore_sync_service.is_configured()
    print(f"\n🔗 Firebase initialisé : {'✅' if is_configured else '❌'}")
    
    # Afficher les Locrits locaux
    locrits = config_service.list_locrits()
    print(f"\n📋 Locrits locaux : {len(locrits)}")
    for locrit in locrits:
        print(f"   • {locrit}")
    
    if is_configured:
        print("\n✅ Firebase Realtime Database prêt pour la synchronisation !")
        print("💡 Connectez-vous dans l'application et allez dans 'Mes Locrits Locaux'")
    else:
        print("\n❌ Problème de configuration Firebase")
        print("💡 Vérifiez que Realtime Database est activé dans Firebase Console")

if __name__ == "__main__":
    asyncio.run(test_firebase_sync())
