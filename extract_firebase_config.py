#!/usr/bin/env python3
"""
Script helper pour configurer Firebase depuis la console Firebase
Génère les variables d'environnement pour le fichier .env (configuration client)

Usage:
    python extract_firebase_config.py
"""

import os

def create_env_from_web_config():
    """Génère un fichier .env à partir de la configuration web Firebase"""
    
    print("🔥 Configuration Firebase Client pour Locrit")
    print("=" * 50)
    print("Rendez-vous sur Firebase Console :")
    print("1. https://console.firebase.google.com/")
    print("2. Sélectionnez votre projet (ou créez-en un)")
    print("3. Paramètres du projet > Général > Vos applications")
    print("4. Cliquez sur l'icône de configuration (engrenage) de votre app web")
    print("5. Copiez les valeurs depuis 'Configuration du SDK'")
    print()
    
    # Demander à l'utilisateur d'entrer les valeurs
    api_key = input("FIREBASE_API_KEY: ")
    auth_domain = input("FIREBASE_AUTH_DOMAIN: ")
    database_url = input("FIREBASE_DATABASE_URL (optionnel): ") or ""
    project_id = input("FIREBASE_PROJECT_ID: ")
    storage_bucket = input("FIREBASE_STORAGE_BUCKET: ")
    messaging_sender_id = input("FIREBASE_MESSAGING_SENDER_ID: ")
    app_id = input("FIREBASE_APP_ID: ")
    
    print()
    locrit_name = input("Nom de votre Locrit (ex: mon-locrit): ") or "my-locrit"
    
    env_content = f"""# Configuration Firebase Client (obligatoire)
# Obtenez ces valeurs depuis Firebase Console > Paramètres du projet > Configuration du SDK
FIREBASE_API_KEY={api_key}
FIREBASE_AUTH_DOMAIN={auth_domain}
FIREBASE_DATABASE_URL={database_url}
FIREBASE_PROJECT_ID={project_id}
FIREBASE_STORAGE_BUCKET={storage_bucket}
FIREBASE_MESSAGING_SENDER_ID={messaging_sender_id}
FIREBASE_APP_ID={app_id}

# Configuration de l'application Locrit
LOCRIT_NAME={locrit_name}
LOCRIT_HOST=localhost
LOCRIT_PORT=8000
LOCRIT_AUTO_AUTH=true

# Configuration Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:latest

# Configuration Tunneling (optionnel)
TUNNEL_SERVICE=localhost.run
TUNNEL_SUBDOMAIN={locrit_name}
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès!")
        print()
        print("🎯 Prochaines étapes :")
        print("1. Activer l'authentification anonyme dans Firebase Console > Authentication")
        print("2. Configurer les règles de sécurité selon BUILD_FIREBASE.md")
        print("3. Tester avec: python test_firebase.py")
        print("4. Lancer Locrit: python main.py")
    else:
        print("⚠️  Le fichier .env existe déjà. Voici le contenu à ajouter/mettre à jour :")
        print("=" * 50)
        print(env_content)

def verify_firebase_setup():
    """Vérifie que Firebase est correctement configuré"""
    print("\n🔍 Vérification de la configuration Firebase...")
    
    required_vars = [
        "FIREBASE_API_KEY",
        "FIREBASE_AUTH_DOMAIN", 
        "FIREBASE_PROJECT_ID",
        "FIREBASE_STORAGE_BUCKET",
        "FIREBASE_MESSAGING_SENDER_ID",
        "FIREBASE_APP_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}")
        else:
            print(f"❌ {var}: NON DÉFINIE")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Variables manquantes: {', '.join(missing_vars)}")
        return False
    else:
        print("\n🎉 Configuration Firebase complète!")
        return True

def main():
    print("🚀 Assistant de Configuration Firebase pour Locrit")
    print("Ce script configure Locrit en mode CLIENT (pas admin)")
    print()
    
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        
        if verify_firebase_setup():
            print("\n💡 Configuration déjà présente et valide!")
            response = input("Voulez-vous la reconfigurer ? (y/N): ")
            if response.lower() not in ['y', 'yes', 'oui']:
                print("Configuration conservée. Testez avec: python test_firebase.py")
                return
    
    create_env_from_web_config()

if __name__ == "__main__":
    main()
