#!/usr/bin/env python3
"""
Test de l'écran des Locrits locaux avec synchronisation Firestore
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.config_service import config_service
from src.services.firestore_sync_service import firestore_sync_service

def test_local_locrits_display():
    """Test d'affichage des Locrits locaux"""
    print("🏠 Test d'affichage des Locrits locaux")
    print("=" * 50)
    
    # Lister les Locrits depuis config.yaml
    locrits = config_service.list_locrits()
    print(f"📋 Locrits trouvés en local: {len(locrits)}")
    
    for locrit_name in locrits:
        settings = config_service.get_locrit_settings(locrit_name)
        if settings:
            print(f"\n🤖 {locrit_name}")
            print(f"   📝 Description: {settings.get('description', 'Aucune')}")
            print(f"   📅 Créé: {settings.get('created_at', 'Inconnu')[:19]}")
            print(f"   🤖 Modèle: {settings.get('ollama_model', 'Non spécifié')}")
            print(f"   🌐 Adresse: {settings.get('public_address', 'Aucune')}")
            print(f"   🟢 Actif: {'Oui' if settings.get('active', False) else 'Non'}")
        else:
            print(f"❌ Impossible de charger les paramètres de {locrit_name}")

def test_firebase_config():
    """Test de la configuration Firebase"""
    print("\n🔥 Test de la configuration Firebase")
    print("=" * 50)
    
    firebase_config = {
        "api_key": config_service.get('firebase.api_key'),
        "auth_domain": config_service.get('firebase.auth_domain'),
        "database_url": config_service.get('firebase.database_url'),
        "project_id": config_service.get('firebase.project_id'),
        "storage_bucket": config_service.get('firebase.storage_bucket'),
    }
    
    print("Configuration Firebase:")
    for key, value in firebase_config.items():
        status = "✅ Configuré" if value else "❌ Manquant"
        print(f"   {key}: {status}")
    
    # Test de la connexion Firestore
    is_configured = firestore_sync_service.is_configured()
    print(f"\n🔗 Firestore configuré: {'✅ Oui' if is_configured else '❌ Non'}")
    
    if not is_configured:
        missing_keys = [key for key, value in firebase_config.items() if not value]
        print(f"\n💡 Pour utiliser Firestore, configurez ces clés dans config.yaml:")
        for key in missing_keys:
            print(f"   firebase.{key}: 'votre_valeur'")

def test_sync_status():
    """Test du statut de synchronisation"""
    print("\n🔄 Test du statut de synchronisation")
    print("=" * 50)
    
    status = firestore_sync_service.get_status()
    
    print("Statut Firestore:")
    print(f"   🔥 Firebase initialisé: {'✅' if status['firebase_initialized'] else '❌'}")
    print(f"   📊 Firestore connecté: {'✅' if status['firestore_connected'] else '❌'}")
    print(f"   🔑 Authentifié: {'✅' if status['authenticated'] else '❌'}")
    if status.get('user_id'):
        print(f"   👤 User ID: {status['user_id']}")

if __name__ == "__main__":
    print("🧪 Test de l'interface des Locrits locaux")
    print("=" * 80)
    
    test_local_locrits_display()
    test_firebase_config()
    test_sync_status()
    
    print("\n" + "=" * 80)
    print("✅ Tests terminés")
    print("💡 Pour tester la synchronisation, configurez Firebase et lancez l'application")
