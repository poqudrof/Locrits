# NETWORK.md - Architecture Réseau Locrit

## Vue d'ensemble

Ce document décrit l'architecture réseau pour connecter les Locrits entre eux et avec une application web de gestion, en utilisant Firebase/Firestore comme backend central.

## 🏗️ Architecture Proposée

### Composants principaux
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Locrit A      │    │   Locrit B      │    │   Locrit C      │
│   (Instance)    │    │   (Instance)    │    │   (Instance)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Firebase/Firestore   │
                    │   (Backend Central)     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Application Web       │
                    │   (Interface Admin)     │
                    └─────────────────────────┘
```

## 🔥 Firebase/Firestore comme Backend

### Avantages de Firebase
- **Temps réel** : Synchronisation automatique entre clients
- **Scalabilité** : Gestion automatique de la charge
- **Authentification** : Système d'auth intégré
- **Hosting** : Hébergement web inclus
- **Pas de serveur** : Architecture serverless

### Structure de données Firestore

```javascript
// Collection: locrits
{
  "locrit_id": "locrit_001",
  "identity": {
    "name": "LocritAlpha",
    "description": "Assistant spécialisé en recherche",
    "personality": "Curieux et analytique"
  },
  "status": {
    "online": true,
    "last_heartbeat": "2025-09-13T10:30:00Z",
    "api_url": "https://alpha-locrit.tunneled.com:8000",
    "capabilities": ["chat", "search", "memory", "api"]
  },
  "configuration": {
    "ollama_model": "llama2",
    "public_access": true,
    "max_connections": 10
  },
  "statistics": {
    "messages_count": 1250,
    "connections_count": 45,
    "uptime_hours": 720
  },
  "created_at": "2025-09-01T00:00:00Z",
  "updated_at": "2025-09-13T10:30:00Z"
}

// Collection: connections
{
  "connection_id": "conn_001_002",
  "source_locrit": "locrit_001",
  "target_locrit": "locrit_002",
  "connection_type": "chat", // chat, search, memory_sharing
  "status": "active", // active, disconnected, blocked
  "established_at": "2025-09-13T09:15:00Z",
  "last_activity": "2025-09-13T10:25:00Z",
  "message_count": 42,
  "metadata": {
    "initiated_by": "locrit_001",
    "connection_quality": "excellent"
  }
}

// Collection: messages (optionnel pour historique global)
{
  "message_id": "msg_12345",
  "from_locrit": "locrit_001",
  "to_locrit": "locrit_002",
  "content": "Peux-tu m'aider avec une recherche sur l'IA ?",
  "message_type": "chat", // chat, search_request, memory_query
  "timestamp": "2025-09-13T10:30:00Z",
  "response_id": "msg_12346" // Lien vers la réponse
}

// Collection: network_events
{
  "event_id": "event_001",
  "event_type": "locrit_joined", // locrit_joined, locrit_left, connection_established
  "locrit_id": "locrit_001",
  "timestamp": "2025-09-13T10:30:00Z",
  "details": {
    "ip_address": "192.168.1.100",
    "user_agent": "Locrit/1.0"
  }
}
```

## 🔌 Intégration Locrit ↔ Firebase

### 1. Modification du CentralServerService

```python
# src/services/firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, List, Any
import asyncio
from datetime import datetime

class FirebaseService:
    """Service pour communiquer avec Firebase/Firestore."""
    
    def __init__(self, credentials_path: str = "firebase-credentials.json"):
        # Initialiser Firebase
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
    
    async def register_locrit(self, locrit_data: Dict[str, Any]) -> str:
        """Enregistre un locrit dans Firestore."""
        doc_ref = self.db.collection('locrits').document()
        locrit_data['created_at'] = datetime.now()
        locrit_data['updated_at'] = datetime.now()
        
        doc_ref.set(locrit_data)
        return doc_ref.id
    
    async def update_heartbeat(self, locrit_id: str, status: Dict[str, Any]):
        """Met à jour le heartbeat d'un locrit."""
        doc_ref = self.db.collection('locrits').document(locrit_id)
        doc_ref.update({
            'status.last_heartbeat': datetime.now(),
            'status.online': True,
            'status': status
        })
    
    async def discover_locrits(self, filters: Dict[str, Any] = None) -> List[Dict]:
        """Découvre les locrits disponibles."""
        query = self.db.collection('locrits').where('status.online', '==', True)
        
        # Ajouter des filtres si nécessaire
        if filters:
            for key, value in filters.items():
                query = query.where(key, '==', value)
        
        docs = query.stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in docs]
    
    async def log_connection(self, source_id: str, target_id: str, conn_type: str):
        """Log une nouvelle connexion."""
        connection_data = {
            'source_locrit': source_id,
            'target_locrit': target_id,
            'connection_type': conn_type,
            'status': 'active',
            'established_at': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0
        }
        
        self.db.collection('connections').add(connection_data)
```

### 2. Configuration Firebase

Créer un fichier `firebase-config.json` :
```json
{
  "type": "service_account",
  "project_id": "locrit-network",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

## 🌐 Application Web de Gestion

### Technologies recommandées
- **Frontend** : React + Firebase SDK
- **Hosting** : Firebase Hosting
- **Authentication** : Firebase Auth

### Fonctionnalités de l'interface web

#### 1. Dashboard Principal
```jsx
// components/Dashboard.jsx
import { useEffect, useState } from 'react';
import { collection, onSnapshot } from 'firebase/firestore';

function Dashboard() {
  const [locrits, setLocrits] = useState([]);
  const [connections, setConnections] = useState([]);

  useEffect(() => {
    // Écoute en temps réel des locrits
    const unsubscribe = onSnapshot(
      collection(db, 'locrits'),
      (snapshot) => {
        const locritsData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setLocrits(locritsData);
      }
    );

    return unsubscribe;
  }, []);

  return (
    <div className="dashboard">
      <h1>Réseau Locrit</h1>
      <LocritGrid locrits={locrits} />
      <ConnectionMap connections={connections} />
      <NetworkStats />
    </div>
  );
}
```

#### 2. Visualisation du Réseau
```jsx
// components/NetworkGraph.jsx
import { Network } from 'react-vis-network';

function NetworkGraph({ locrits, connections }) {
  const nodes = locrits.map(locrit => ({
    id: locrit.id,
    label: locrit.identity.name,
    color: locrit.status.online ? '#4CAF50' : '#f44336',
    title: `${locrit.identity.description}\nMessages: ${locrit.statistics.messages_count}`
  }));

  const edges = connections.map(conn => ({
    from: conn.source_locrit,
    to: conn.target_locrit,
    label: conn.message_count.toString(),
    color: conn.status === 'active' ? '#2196F3' : '#999'
  }));

  return (
    <Network
      graph={{ nodes, edges }}
      options={{
        height: "600px",
        physics: { enabled: true }
      }}
    />
  );
}
```

#### 3. Chat Interface
```jsx
// components/LocritChat.jsx
function LocritChat({ selectedLocrit }) {
  const [message, setMessage] = useState('');
  
  const sendMessage = async () => {
    // Envoyer via API directe du locrit
    const response = await fetch(`${selectedLocrit.status.api_url}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        user_id: 'web_admin'
      })
    });
    
    const result = await response.json();
    // Afficher la réponse...
  };

  return (
    <div className="chat-interface">
      <h3>Chat avec {selectedLocrit.identity.name}</h3>
      <div className="messages">
        {/* Messages history */}
      </div>
      <input 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
    </div>
  );
}
```

## 🔐 Sécurité et Authentification

### Firebase Auth Setup
```javascript
// auth.js
import { initializeAuth } from 'firebase/auth';

const authConfig = {
  providers: [
    'password', // Email/password
    'google',   // Google OAuth
    'github'    // GitHub OAuth (pour développeurs)
  ],
  rules: {
    admin: ['jeremy@locrit.com'],
    viewer: ['*@locrit.com']
  }
};
```

### Règles de sécurité Firestore
```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Locrits peuvent lire/écrire leurs propres données
    match /locrits/{locritId} {
      allow read: if true; // Lecture publique pour découverte
      allow write: if request.auth != null 
        && request.auth.token.locrit_id == locritId;
    }
    
    // Connexions lisibles par tous, écrites par les participants
    match /connections/{connectionId} {
      allow read: if true;
      allow create: if request.auth != null;
      allow update: if request.auth != null 
        && (request.auth.token.locrit_id == resource.data.source_locrit
        || request.auth.token.locrit_id == resource.data.target_locrit);
    }
    
    // Admin complet pour les utilisateurs web authentifiés
    match /{document=**} {
      allow read, write: if request.auth != null 
        && request.auth.token.email_verified == true;
    }
  }
}
```

## 📦 Déploiement

### 1. Setup Firebase Project
```bash
# Installer Firebase CLI
npm install -g firebase-tools

# Initialiser le projet
firebase init

# Déployer
firebase deploy
```

### 2. Configuration Locrit
```python
# requirements.txt (ajouter)
firebase-admin>=6.2.0
google-cloud-firestore>=2.11.0

# .env
FIREBASE_PROJECT_ID=locrit-network
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### 3. Integration dans LocritManager
```python
# Modifier src/services/locrit_manager.py
from .firebase_service import FirebaseService

class LocritManager:
    def __init__(self):
        # ... autres services
        self.firebase = FirebaseService()
        
    async def register_with_firebase(self):
        """S'enregistrer dans Firebase au lieu du serveur central."""
        locrit_data = {
            'identity': self.identity,
            'status': await self.get_status(),
            'configuration': {
                'ollama_model': 'llama2',
                'public_access': True
            }
        }
        
        self.firebase_id = await self.firebase.register_locrit(locrit_data)
        return self.firebase_id
```

## 🚀 Avantages de cette Architecture

### ✅ **Pour les Locrits**
- **Découverte automatique** via Firestore
- **Temps réel** : Synchronisation instantanée
- **Persistance** : Historique des connexions
- **Scalabilité** : Pas de limite de locrits

### ✅ **Pour l'Application Web**
- **Monitoring temps réel** de tout le réseau
- **Interface intuitive** pour gérer les locrits
- **Visualisation graphique** des connexions
- **Chat direct** avec n'importe quel locrit

### ✅ **Architecture Technique**
- **Serverless** : Pas de serveur à maintenir
- **Sécurisé** : Authentification Firebase
- **Économique** : Pay-as-you-use
- **Fiable** : Infrastructure Google

## 📋 Plan d'Implémentation

### Phase 1 : Setup Firebase (1-2 jours)
1. Créer projet Firebase
2. Configurer Firestore
3. Implémenter FirebaseService
4. Modifier LocritManager

### Phase 2 : Application Web (3-5 jours)
1. Setup React + Firebase SDK
2. Dashboard de monitoring
3. Visualisation réseau
4. Interface de chat

### Phase 3 : Intégration (1-2 jours)
1. Tests end-to-end
2. Déploiement
3. Documentation

**Total estimé : 5-9 jours de développement**

## 💡 Alternative Simple

Si Firebase semble trop complexe, une alternative plus simple serait :

```
┌─────────────────┐     ┌─────────────────┐
│   Locrits       │────▶│   Supabase      │
│   (Instances)   │     │   (Backend)     │
└─────────────────┘     └─────────┬───────┘
                                  │
                        ┌─────────▼───────┐
                        │   Web App       │
                        │   (Next.js)     │
                        └─────────────────┘
```

Supabase offre PostgreSQL + temps réel + auth + hosting dans un package plus simple que Firebase.

Est-ce que cette architecture répond à tes besoins ? Je peux détailler davantage certaines parties si nécessaire !
