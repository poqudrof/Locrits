#!/usr/bin/env python3
"""
Script de test pour créer des Locrits de démonstration
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.config_service import config_service
from datetime import datetime

def create_demo_locrits():
    """Crée quelques Locrits de démonstration"""
    
    demo_locrits = [
        {
            'name': 'Pixie Assistant',
            'description': 'Assistant personnel intelligent et organisé',
            'public_address': 'pixie.localhost.run',
            'active': True,
            'open_to': {
                'humans': True,
                'locrits': True,
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
            'search_enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'name': 'Marie Recherche',
            'description': 'Spécialisée dans la recherche et l\'analyse',
            'public_address': 'marie.example.com',
            'active': False,
            'open_to': {
                'humans': True,
                'locrits': True,
                'invitations': True,
                'internet': True,
                'platform': False
            },
            'access_to': {
                'logs': True,
                'quick': True,
                'full': True,
                'llm': True
            },
            'ollama_model': 'llama3.2',
            'memory_enabled': True,
            'search_enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'name': 'Bob Technique',
            'description': 'Expert en programmation et technologies',
            'public_address': 'bob.dev.local',
            'active': True,
            'open_to': {
                'humans': True,
                'locrits': True,
                'invitations': False,
                'internet': False,
                'platform': False
            },
            'access_to': {
                'logs': False,
                'quick': True,
                'full': False,
                'llm': False
            },
            'ollama_model': 'codellama',
            'memory_enabled': True,
            'search_enabled': False,
            'created_at': datetime.now().isoformat()
        }
    ]
    
    print("🤖 Création des Locrits de démonstration...")
    
    for locrit in demo_locrits:
        name = locrit['name']
        print(f"   📝 Création de '{name}'...")
        
        config_service.update_locrit_settings(name, locrit)
    
    # Sauvegarder la configuration
    success = config_service.save_config()
    
    if success:
        print("✅ Locrits de démonstration créés avec succès!")
        print(f"📁 Configuration sauvegardée dans: {config_service.config_path}")
        
        # Afficher la liste
        locrits = config_service.list_locrits()
        print(f"\n📋 {len(locrits)} Locrits disponibles:")
        for name in locrits:
            settings = config_service.get_locrit_settings(name)
            status = "🟢 Actif" if settings.get('active') else "🔴 Inactif"
            print(f"   {status} {name} - {settings.get('description', 'Sans description')}")
    else:
        print("❌ Erreur lors de la sauvegarde!")

def clear_demo_locrits():
    """Supprime tous les Locrits de démonstration"""
    locrits = config_service.list_locrits()
    
    if not locrits:
        print("📭 Aucun Locrit à supprimer")
        return
    
    print(f"🗑️ Suppression de {len(locrits)} Locrits...")
    
    for name in locrits:
        config_service.delete_locrit(name)
        print(f"   🗑️ {name} supprimé")
    
    success = config_service.save_config()
    
    if success:
        print("✅ Tous les Locrits ont été supprimés!")
    else:
        print("❌ Erreur lors de la sauvegarde!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestion des Locrits de démonstration")
    parser.add_argument("--clear", action="store_true", help="Supprimer tous les Locrits")
    parser.add_argument("--create", action="store_true", help="Créer les Locrits de démonstration")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_demo_locrits()
    elif args.create:
        create_demo_locrits()
    else:
        print("Usage:")
        print("  python test_create_locrits.py --create   # Créer les Locrits de démo")
        print("  python test_create_locrits.py --clear    # Supprimer tous les Locrits")
