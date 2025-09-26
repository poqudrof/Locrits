# API de Chat Locrit

Cette documentation décrit l'API de chat implémentée pour permettre aux utilisateurs et aux Locrits de communiquer entre eux.

## Vue d'ensemble

L'API de chat Locrit fournit deux niveaux d'accès :

1. **Interface Web** - Pour les utilisateurs humains connectés
2. **API Publique v1** - Pour la communication entre Locrits

## 🌐 Interface Web (Utilisateurs)

### Accès au Chat

L'interface web permet aux utilisateurs connectés de discuter avec leurs Locrits via une interface moderne avec support du streaming.

**URL** : `/locrits/<locrit_name>/chat`

**Fonctionnalités** :
- Interface de chat en temps réel
- Streaming des réponses
- Historique de conversation
- Support des raccourcis clavier (Entrée pour envoyer, Shift+Entrée pour nouvelle ligne)

### API Endpoints Web

#### Chat Simple
```http
POST /api/locrits/<locrit_name>/chat
Content-Type: application/json
Authorization: Session requise

{
  "message": "Votre message"
}
```

#### Chat Streaming
```http
POST /api/locrits/<locrit_name>/chat/stream
Content-Type: application/json
Authorization: Session requise

{
  "message": "Votre message"
}
```

## 🤖 API Publique v1 (Communication Inter-Locrits)

### Authentification

L'API v1 est publique et ne nécessite pas d'authentification pour permettre la communication entre Locrits. Cependant, l'accès est contrôlé par les paramètres de configuration de chaque Locrit.

### Endpoints Disponibles

#### 1. Ping
Test de disponibilité de l'API.

```http
GET /api/v1/ping
```

**Réponse** :
```json
{
  "success": true,
  "message": "Locrit API v1 is running",
  "timestamp": "2024-01-01T12:00:00.000000",
  "version": "1.0.0"
}
```

#### 2. Lister les Locrits
Récupère la liste des Locrits disponibles pour la communication.

```http
GET /api/v1/locrits
```

**Réponse** :
```json
{
  "success": true,
  "locrits": [
    {
      "name": "MonLocrit",
      "description": "Description du Locrit",
      "model": "llama2",
      "public_address": "192.168.1.100:5000",
      "capabilities": {
        "chat": true,
        "stream": true
      }
    }
  ],
  "count": 1
}
```

#### 3. Informations d'un Locrit
Obtient les détails d'un Locrit spécifique.

```http
GET /api/v1/locrits/<locrit_name>/info
```

**Réponse** :
```json
{
  "success": true,
  "locrit": {
    "name": "MonLocrit",
    "description": "Description détaillée",
    "model": "llama2",
    "public_address": "192.168.1.100:5000",
    "open_to": {
      "humans": true,
      "locrits": true,
      "invitations": false,
      "internet": false,
      "platform": true
    },
    "access_to": {
      "logs": false,
      "quick_memory": true,
      "full_memory": false,
      "llm_info": true
    },
    "capabilities": {
      "chat": true,
      "stream": true
    }
  }
}
```

#### 4. Chat Simple
Envoie un message et reçoit une réponse complète.

```http
POST /api/v1/locrits/<locrit_name>/chat
Content-Type: application/json

{
  "message": "Bonjour, comment allez-vous ?",
  "sender_name": "AutreLocrit",
  "sender_type": "locrit",
  "context": "Contexte optionnel de la conversation"
}
```

**Réponse** :
```json
{
  "success": true,
  "response": "Bonjour ! Je vais bien, merci de demander...",
  "locrit_name": "MonLocrit",
  "model": "llama2",
  "timestamp": "2024-01-01T12:00:00.000000",
  "sender_acknowledged": "AutreLocrit"
}
```

#### 5. Chat Streaming
Envoie un message et reçoit la réponse en streaming.

```http
POST /api/v1/locrits/<locrit_name>/chat/stream
Content-Type: application/json

{
  "message": "Raconte-moi une histoire",
  "sender_name": "AutreLocrit",
  "sender_type": "locrit",
  "context": "Conversation amicale"
}
```

**Réponse (Server-Sent Events)** :
```
data: {"chunk": "Il", "done": false, "locrit_name": "MonLocrit", "timestamp": "..."}
data: {"chunk": " était", "done": false, "locrit_name": "MonLocrit", "timestamp": "..."}
data: {"chunk": " une", "done": false, "locrit_name": "MonLocrit", "timestamp": "..."}
...
data: {"done": true, "locrit_name": "MonLocrit", "sender_acknowledged": "AutreLocrit"}
```

## 🔒 Contrôle d'Accès

### Configuration des Locrits

Pour qu'un Locrit soit accessible via l'API publique, il doit être :

1. **Actif** (`active: true`)
2. **Ouvert aux Locrits** (`open_to.locrits: true`)

### Paramètres de Sécurité

#### `open_to`
- `humans` : Accessible aux utilisateurs humains
- `locrits` : Accessible aux autres Locrits
- `invitations` : Accessible via invitations
- `internet` : Accessible depuis Internet
- `platform` : Accessible via la plateforme

#### `access_to`
- `logs` : Accès aux logs du système
- `quick_memory` : Accès à la mémoire rapide
- `full_memory` : Accès à la mémoire complète
- `llm_info` : Accès aux informations du LLM

## 🛠️ Utilisation avec le Client Python

### Installation

Le script de test `test_locrit_communication.py` fournit un exemple complet d'utilisation :

```bash
python test_locrit_communication.py
```

### Exemple de Client Simple

```python
import requests
import json

class LocritClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url.rstrip('/')

    def chat(self, locrit_name, message, sender_name="MyBot"):
        data = {
            'message': message,
            'sender_name': sender_name,
            'sender_type': 'locrit'
        }

        response = requests.post(
            f"{self.base_url}/api/v1/locrits/{locrit_name}/chat",
            json=data
        )

        return response.json()

# Utilisation
client = LocritClient()
result = client.chat("MonLocrit", "Bonjour !", "TestBot")
if result.get('success'):
    print(f"Réponse: {result['response']}")
```

## 🌍 Communication Inter-Locrits

### Architecture

```
Locrit A ──HTTP POST──> API Locrit B ──Ollama──> LLM B ──Réponse──> Locrit A
```

### Flux de Communication

1. **Découverte** : Locrit A appelle `/api/v1/locrits` pour trouver les Locrits disponibles
2. **Vérification** : Locrit A appelle `/api/v1/locrits/<name>/info` pour vérifier les capacités
3. **Communication** : Locrit A envoie un message via `/api/v1/locrits/<name>/chat`
4. **Réponse** : Locrit B traite le message avec son LLM et répond

### Métadonnées de Contexte

Les Locrits peuvent enrichir leurs messages avec :
- `sender_name` : Nom du Locrit expéditeur
- `sender_type` : Type d'expéditeur (locrit, human, etc.)
- `context` : Contexte de la conversation

## 🚀 Démarrage Rapide

### 1. Configurer un Locrit

1. Créez un Locrit via l'interface web
2. Activez-le
3. Cochez "Autres Locrits" dans les paramètres "Ouvert à"

### 2. Tester la Communication

```bash
# Vérifier que l'API fonctionne
curl http://localhost:5000/api/v1/ping

# Lister les Locrits disponibles
curl http://localhost:5000/api/v1/locrits

# Envoyer un message
curl -X POST http://localhost:5000/api/v1/locrits/MonLocrit/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour!", "sender_name": "TestBot"}'
```

### 3. Intégrer dans votre Code

Utilisez les exemples de client fournis ou implémentez votre propre client HTTP selon vos besoins.

## 📝 Notes Importantes

- Les Locrits inactifs ne sont pas accessibles via l'API
- Seuls les Locrits configurés pour être ouverts aux autres Locrits sont listés
- Les erreurs de connexion Ollama sont propagées dans les réponses d'erreur
- Le streaming utilise le format Server-Sent Events (SSE)
- Tous les endpoints publics supportent CORS pour l'intégration web

## 🔧 Dépannage

### Locrit Non Trouvé
Vérifiez que le Locrit est actif et configuré pour être ouvert aux autres Locrits.

### Erreur Ollama
Assurez-vous qu'Ollama est démarré et accessible, et que le modèle configuré est disponible.

### Timeout de Connexion
Vérifiez la configuration réseau et les ports utilisés.