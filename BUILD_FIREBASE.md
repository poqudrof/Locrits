# Guide de Configuration Firebase pour Locrit

Ce guide explique comment configurer Firebase/Firestore pour le backend de Locrit. Le code Python sera distribué aux utilisateurs finaux et se connectera en tant que client (non-admin) à Firebase. Les clés utilisateur seront stockées dans un fichier `.env` local.

## 1. Création du Projet Firebase

### Étape 1 : Créer un projet Firebase
1. Aller sur [Firebase Console](https://console.firebase.google.com/)
2. Cliquer sur "Ajouter un projet"
3. Nom du projet : `locrit-network`
4. Activer Google Analytics (optionnel)
5. Créer le projet

### Étape 2 : Configurer Firestore
1. Dans la console Firebase, aller dans "Firestore Database"
2. Cliquer sur "Créer une base de données"
3. Choisir "Commencer en mode test" (pour le développement)
4. Sélectionner la région (ex: `europe-west1`)

### Étape 3 : Configurer l'authentification utilisateur
1. Dans la console Firebase, aller dans "Authentication"
2. Cliquer sur "Commencer"
3. Dans l'onglet "Sign-in method", activer :
   - **Anonymous** (pour les locrits sans compte)
   - **Email/Password** (pour les utilisateurs avec compte)
4. Dans l'onglet "Users", vous pourrez voir les connexions

### Étape 4 : Créer une application web
1. Dans "Paramètres du projet" → "Général"
2. Cliquer sur l'icône web `</>`
3. Nom de l'app : `locrit-client`
4. Cocher "Configurer aussi Firebase Hosting"
5. Copier la configuration web (pas la clé admin !)

## 2. Configuration de l'Environnement Python Client

### Installation des dépendances
```bash
# Ajouter à requirements.txt
firebase>=4.0.1
python-dotenv>=1.0.0
pyrebase4>=4.7.1
```

```bash
# Installer les dépendances
source .venv/bin/activate
pip install firebase python-dotenv pyrebase4
```

### Créer le fichier .env pour les utilisateurs
Créer un fichier `.env` à la racine du projet :

```env
# Configuration Firebase Web App (Client)
FIREBASE_API_KEY=your_web_api_key_here
FIREBASE_AUTH_DOMAIN=locrit-network.firebaseapp.com
FIREBASE_DATABASE_URL=https://locrit-network-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=locrit-network
FIREBASE_STORAGE_BUCKET=locrit-network.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
FIREBASE_APP_ID=your_app_id_here

# Configuration de l'application Locrit
LOCRIT_NAME=my-locrit
LOCRIT_HOST=localhost
LOCRIT_PORT=8000
LOCRIT_AUTO_AUTH=true

# Configuration Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:latest
```

### Ajouter .env au .gitignore
```bash
echo ".env" >> .gitignore
```

## 3. Obtenir les Clés de Configuration Web

### Récupérer la configuration client
1. Dans Firebase Console → "Paramètres du projet" → "Général"
2. Faire défiler vers "Vos applications"
3. Cliquer sur l'icône de configuration (engrenage) de votre app web
4. Copier la configuration dans "Configuration du SDK"

### Script pour générer le .env
Créer un script helper `extract_firebase_config.py` :

```python
import json
import os

def create_env_from_web_config():
    """Génère un fichier .env à partir de la configuration web Firebase"""
    
    print("=== Configuration Firebase Client pour Locrit ===")
    print("Copiez les valeurs depuis Firebase Console > Paramètres du projet > Configuration du SDK")
    print()
    
    # Demander à l'utilisateur d'entrer les valeurs
    api_key = input("FIREBASE_API_KEY: ")
    auth_domain = input("FIREBASE_AUTH_DOMAIN: ")
    database_url = input("FIREBASE_DATABASE_URL (optionnel): ") or ""
    project_id = input("FIREBASE_PROJECT_ID: ")
    storage_bucket = input("FIREBASE_STORAGE_BUCKET: ")
    messaging_sender_id = input("FIREBASE_MESSAGING_SENDER_ID: ")
    app_id = input("FIREBASE_APP_ID: ")
    
    locrit_name = input("Nom de votre Locrit (ex: mon-locrit): ") or "my-locrit"
    
    env_content = f"""# Configuration Firebase Web App (Client)
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
    else:
        print("⚠️  Le fichier .env existe déjà. Voici le contenu à ajouter/mettre à jour :")
        print(env_content)

if __name__ == "__main__":
    create_env_from_web_config()
```

## 4. Implémentation du Service Firebase Client

### Créer src/services/firebase_service.py
```python
import os
import pyrebase
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import logging
import asyncio
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class FirebaseService:
    """Service client pour interagir avec Firebase/Firestore depuis les locrits utilisateur"""
    
    def __init__(self):
        self.firebase = None
        self.auth = None
        self.db = None
        self.user = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialise la connexion Firebase client"""
        try:
            # Configuration client Firebase
            config = {
                "apiKey": os.getenv("FIREBASE_API_KEY"),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
                "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                "appId": os.getenv("FIREBASE_APP_ID")
            }
            
            # Initialiser Firebase
            self.firebase = pyrebase.initialize_app(config)
            self.auth = self.firebase.auth()
            self.db = self.firebase.database()
            
            # Authentification automatique anonyme si configurée
            if os.getenv("LOCRIT_AUTO_AUTH", "true").lower() == "true":
                self._authenticate_anonymously()
            
            logger.info("Firebase client initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Firebase: {e}")
            raise
    
    def _authenticate_anonymously(self):
        """Authentifie le locrit de manière anonyme"""
        try:
            self.user = self.auth.sign_in_anonymous()
            logger.info("Authentification anonyme réussie")
        except Exception as e:
            logger.warning(f"Échec de l'authentification anonyme: {e}")
    
    async def register_locrit(self, locrit_data: Dict[str, Any]) -> str:
        """Enregistre un locrit dans Firebase"""
        try:
            if not self.user:
                self._authenticate_anonymously()
            
            # Ajouter des métadonnées
            locrit_data.update({
                "user_id": self.user["localId"] if self.user else "anonymous",
                "created_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "client_type": "locrit-python"
            })
            
            # Enregistrer dans Firebase Realtime Database
            result = self.db.child("locrits").push(locrit_data, self.user["idToken"] if self.user else None)
            locrit_id = result["name"]
            
            logger.info(f"Locrit enregistré: {locrit_id}")
            return locrit_id
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement: {e}")
            raise
    
    async def update_locrit_status(self, locrit_id: str, status_data: Dict[str, Any]):
        """Met à jour le statut d'un locrit"""
        try:
            if not self.user:
                self._authenticate_anonymously()
            
            # Ajouter timestamp de mise à jour
            status_data["last_seen"] = datetime.now().isoformat()
            
            # Mettre à jour dans Firebase
            self.db.child("locrits").child(locrit_id).update(
                status_data, 
                self.user["idToken"] if self.user else None
            )
            
            logger.info(f"Statut mis à jour pour: {locrit_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour: {e}")
            raise
    
    async def discover_locrits(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Découvre les locrits disponibles"""
        try:
            # Récupérer tous les locrits publics
            all_locrits = self.db.child("locrits").get()
            
            if not all_locrits.val():
                return []
            
            locrits = []
            current_time = datetime.now()
            
            for locrit_id, locrit_data in all_locrits.val().items():
                # Ajouter l'ID
                locrit_data["id"] = locrit_id
                
                # Vérifier si le locrit est actif (dernière activité < 5 minutes)
                try:
                    last_seen = datetime.fromisoformat(locrit_data.get("last_seen", ""))
                    time_diff = (current_time - last_seen).total_seconds()
                    if time_diff > 300:  # 5 minutes
                        continue
                except:
                    continue
                
                # Appliquer les filtres
                if filters:
                    match = True
                    for field, value in filters.items():
                        if locrit_data.get(field) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                locrits.append(locrit_data)
            
            logger.info(f"Découvert {len(locrits)} locrits actifs")
            return locrits
            
        except Exception as e:
            logger.error(f"Erreur lors de la découverte: {e}")
            raise
    
    async def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Sauvegarde une conversation"""
        try:
            if not self.user:
                self._authenticate_anonymously()
            
            # Ajouter des métadonnées
            conversation_data.update({
                "created_at": datetime.now().isoformat(),
                "user_id": self.user["localId"] if self.user else "anonymous"
            })
            
            # Sauvegarder dans Firebase
            result = self.db.child("conversations").push(
                conversation_data, 
                self.user["idToken"] if self.user else None
            )
            conversation_id = result["name"]
            
            logger.info(f"Conversation sauvegardée: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise
    
    async def get_conversations(self, locrit_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les conversations d'un locrit"""
        try:
            # Récupérer toutes les conversations
            all_conversations = self.db.child("conversations").get()
            
            if not all_conversations.val():
                return []
            
            conversations = []
            for conv_id, conv_data in all_conversations.val().items():
                # Vérifier si le locrit participe à cette conversation
                participants = conv_data.get("participants", [])
                if locrit_id in participants:
                    conv_data["id"] = conv_id
                    conversations.append(conv_data)
            
            # Trier par date de création (plus récent en premier)
            conversations.sort(
                key=lambda x: x.get("created_at", ""), 
                reverse=True
            )
            
            return conversations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            raise
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.user:
            try:
                # Optionnel: marquer le locrit comme offline
                pass
            except:
                pass
```

## 5. Configuration des Règles de Sécurité Firebase

Dans Firebase Console → Firestore → Règles :

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Règles pour les locrits - accès utilisateur
    match /locrits/{locritId} {
      allow read: if true; // Lecture publique pour découverte
      allow create: if request.auth != null; // Création pour utilisateurs authentifiés
      allow update: if request.auth != null && 
                       request.auth.uid == resource.data.user_id; // Mise à jour par propriétaire
      allow delete: if request.auth != null && 
                       request.auth.uid == resource.data.user_id; // Suppression par propriétaire
    }
    
    // Règles pour les conversations
    match /conversations/{conversationId} {
      allow read: if request.auth != null && 
                     request.auth.uid in resource.data.participants;
      allow create: if request.auth != null;
      allow update: if request.auth != null && 
                       request.auth.uid in resource.data.participants;
      allow delete: if request.auth != null && 
                       request.auth.uid == resource.data.user_id;
    }
    
    // Règles pour les connexions en temps réel
    match /connections/{connectionId} {
      allow read, write: if request.auth != null;
    }
  }
}

// Règles pour Realtime Database
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

**ET** dans Firebase Console → Realtime Database → Règles :

```json
{
  "rules": {
    ".read": true,
    ".write": "auth != null",
    "locrits": {
      "$locritId": {
        ".read": true,
        ".write": "auth != null && (auth.uid == data.user_id || !data.exists())"
      }
    },
    "conversations": {
      "$conversationId": {
        ".read": "auth != null && auth.uid == data.user_id",
        ".write": "auth != null"
      }
    }
  }
}
```

## 6. Tests de Configuration Client

### Script de test test_firebase.py
```python
import asyncio
import os
from dotenv import load_dotenv
from src.services.firebase_service import FirebaseService

load_dotenv()

async def test_firebase_connection():
    """Test la connexion Firebase client"""
    try:
        firebase_service = FirebaseService()
        
        # Test d'enregistrement
        test_locrit = {
            "name": "test-locrit-client",
            "host": "localhost",
            "port": 8000,
            "status": "online",
            "capabilities": ["chat", "search"],
            "description": "Locrit de test en mode client"
        }
        
        locrit_id = await firebase_service.register_locrit(test_locrit)
        print(f"✅ Locrit enregistré avec l'ID: {locrit_id}")
        
        # Test de découverte
        locrits = await firebase_service.discover_locrits()
        print(f"✅ Découverte: {len(locrits)} locrits trouvés")
        
        # Test de mise à jour
        await firebase_service.update_locrit_status(locrit_id, {
            "status": "busy",
            "current_task": "Testing client connection"
        })
        print("✅ Statut mis à jour")
        
        # Test de conversation
        conversation_id = await firebase_service.save_conversation({
            "participants": [locrit_id, "user-test"],
            "messages": [
                {
                    "sender": "user-test",
                    "content": "Test message from user",
                    "timestamp": "2024-01-01T10:00:00Z"
                }
            ],
            "title": "Test Client Conversation"
        })
        print(f"✅ Conversation sauvegardée: {conversation_id}")
        
        print("🎉 Tous les tests Firebase client passent!")
        
    except Exception as e:
        print(f"❌ Erreur de test Firebase: {e}")

if __name__ == "__main__":
    asyncio.run(test_firebase_connection())
```

### Lancer le test
```bash
source .venv/bin/activate
python test_firebase.py
```

## 7. Intégration dans l'Application Locrit

### Modifier src/services/locrit_manager.py
Ajouter l'importation et l'initialisation :

```python
from .firebase_service import FirebaseService

class LocritManager:
    def __init__(self):
        # ... autres initialisations
        self.firebase_service = FirebaseService()
        self.firebase_locrit_id = None
    
    async def start_locrit(self):
        """Démarre le locrit et l'enregistre sur Firebase"""
        try:
            # Enregistrer ce locrit sur Firebase
            locrit_data = {
                "name": self.locrit_config.get("name", "unnamed-locrit"),
                "host": self.locrit_config.get("host", "localhost"),
                "port": self.locrit_config.get("port", 8000),
                "status": "online",
                "capabilities": ["chat", "search", "memory"],
                "model": getattr(self.ollama_service, 'current_model', 'unknown'),
                "version": "1.0.0"
            }
            
            self.firebase_locrit_id = await self.firebase_service.register_locrit(locrit_data)
            print(f"🔥 Locrit enregistré sur Firebase: {self.firebase_locrit_id}")
            
            # Démarrer le heartbeat
            asyncio.create_task(self._firebase_heartbeat())
            
        except Exception as e:
            print(f"⚠️ Impossible de s'enregistrer sur Firebase: {e}")
    
    async def _firebase_heartbeat(self):
        """Envoie un heartbeat périodique à Firebase"""
        while True:
            try:
                if self.firebase_locrit_id:
                    await self.firebase_service.update_locrit_status(
                        self.firebase_locrit_id,
                        {
                            "status": "online",
                            "last_heartbeat": True
                        }
                    )
                await asyncio.sleep(60)  # Heartbeat toutes les minutes
            except Exception as e:
                print(f"⚠️ Erreur heartbeat Firebase: {e}")
                await asyncio.sleep(120)  # Retry dans 2 minutes
    
    async def discover_network_locrits(self) -> List[Dict[str, Any]]:
        """Découvre les autres locrits sur le réseau Firebase"""
        try:
            all_locrits = await self.firebase_service.discover_locrits()
            # Filtrer pour exclure ce locrit
            network_locrits = [
                locrit for locrit in all_locrits 
                if locrit.get("id") != self.firebase_locrit_id
            ]
            return network_locrits
        except Exception as e:
            print(f"⚠️ Erreur découverte réseau: {e}")
            return []
    
    async def save_conversation_to_firebase(self, conversation_data: Dict[str, Any]) -> str:
        """Sauvegarde une conversation sur Firebase"""
        try:
            return await self.firebase_service.save_conversation(conversation_data)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde conversation: {e}")
            return ""
    
    def cleanup(self):
        """Nettoyage lors de la fermeture"""
        if self.firebase_service:
            self.firebase_service.cleanup()
```

## 8. Distribution et Configuration Utilisateur

### Pour les développeurs qui distribuent Locrit

1. **Publier Locrit avec le .env.example**
2. **Créer des instructions utilisateur simples**
3. **Fournir le script extract_firebase_config.py**

### Pour les utilisateurs finaux

#### Étapes de configuration utilisateur :

1. **Cloner/télécharger Locrit**
```bash
git clone https://github.com/votre-repo/locrit.git
cd locrit
```

2. **Installer les dépendances**
```bash
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configurer Firebase**
```bash
# Copier le template
cp .env.example .env

# Lancer l'assistant de configuration
python extract_firebase_config.py
```

4. **Entrer les valeurs Firebase** (depuis console.firebase.google.com)
   - API Key
   - Auth Domain  
   - Project ID
   - etc.

5. **Tester la connexion**
```bash
python test_firebase.py
```

6. **Lancer Locrit**
```bash
python main.py
```

### Variables d'environnement simplifiées pour utilisateurs
Dans `.env.example` pour distribution :

```env
# Configuration Firebase (obligatoire)
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_STORAGE_BUCKET=
FIREBASE_MESSAGING_SENDER_ID=
FIREBASE_APP_ID=

# Configuration Locrit (optionnel)
LOCRIT_NAME=mon-locrit
LOCRIT_HOST=localhost
LOCRIT_PORT=8000
LOCRIT_AUTO_AUTH=true

# Configuration Ollama (optionnel)
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:latest
```

### Sécurité pour la distribution
1. **Jamais** inclure de vraies clés dans le code distribué
2. Utiliser uniquement la configuration web (pas de clés admin)
3. Les utilisateurs s'authentifient de manière anonyme ou avec leur compte
4. Chaque locrit est isolé par son propriétaire (user_id)
5. Règles Firebase empêchent l'accès croisé non autorisé

### Avantages de l'approche client
- **Pas de serveur à maintenir** : Firebase gère l'infrastructure
- **Authentification utilisateur** : Chaque locrit appartient à son utilisateur
- **Scalabilité automatique** : Firebase scale automatiquement
- **Sécurité** : Règles de sécurité empêchent les accès non autorisés
- **Simplicité** : Les utilisateurs n'ont besoin que de leur configuration web

## 9. Dépannage Client

### Erreurs communes

**Erreur de configuration**
```
ValueError: Invalid API key
```
→ Vérifier que FIREBASE_API_KEY est correctement définie dans .env

**Erreur d'authentification**
```
AuthenticationError: Anonymous authentication disabled
```
→ Activer l'authentification anonyme dans Firebase Console > Authentication

**Erreur de permissions**
```
PermissionDenied: Missing or insufficient permissions
```
→ Vérifier les règles Firebase Realtime Database et Firestore

**Erreur de réseau**
```
ConnectionError: Unable to connect to Firebase
```
→ Vérifier la connexion internet et les paramètres proxy

### Vérification de configuration
```python
# Test rapide dans un script Python
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "FIREBASE_API_KEY",
    "FIREBASE_AUTH_DOMAIN", 
    "FIREBASE_PROJECT_ID",
    "FIREBASE_STORAGE_BUCKET",
    "FIREBASE_MESSAGING_SENDER_ID",
    "FIREBASE_APP_ID"
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {'*' * len(value[:10])}...")
    else:
        print(f"❌ {var}: NON DÉFINIE")
```

### Logs de débogage
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pyrebase')
```

## 10. Prochaines Étapes

### Pour les développeurs de Locrit :
1. **Créer le projet Firebase central** pour tous les utilisateurs
2. **Configurer l'authentification anonyme** 
3. **Définir les règles de sécurité** pour protéger les données utilisateur
4. **Tester avec le service client** 
5. **Documenter la configuration pour les utilisateurs finaux**

### Pour les utilisateurs finaux :
1. **Installer Locrit** selon les instructions
2. **Copier .env.example vers .env**
3. **Configurer Firebase** avec extract_firebase_config.py
4. **Tester la connexion** avec test_firebase.py
5. **Lancer Locrit** et découvrir le réseau !

### Architecture de réseau résultante :
- **Firebase central** : Un seul projet Firebase pour tous les locrits
- **Authentification utilisateur** : Chaque locrit s'authentifie individuellement
- **Isolation des données** : Chaque utilisateur voit seulement ses données
- **Découverte publique** : Tous les locrits peuvent se découvrir mutuellement
- **Communications sécurisées** : Firebase gère l'authentification et l'autorisation

Ce guide fournit une architecture distribuée et sécurisée où les locrits clients peuvent communiquer via Firebase sans nécessiter de serveur central à maintenir.
