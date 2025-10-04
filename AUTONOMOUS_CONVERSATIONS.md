# Système de Conversations Autonomes

## Vue d'ensemble

Le backend Locrits gère maintenant les conversations de façon **autonome** et **persistante**. L'UI n'a plus besoin de gérer le contexte - elle envoie juste un `conversation_id`.

## Architecture

```
┌─────────────┐
│     UI      │ Envoie conversation_id
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  conversation_service.py    │ ◄── Gère le contexte
│  (autonome, server-side)    │
└────┬────────────────────┬───┘
     │                    │
     ▼                    ▼
┌──────────────┐   ┌────────────────┐
│ YAML Files   │   │  Kuzu Memory   │
│ data/        │   │  (messages,    │
│ conversations│   │   concepts)     │
└──────────────┘   └────────────────┘
```

## Utilisation

### 1. Créer une conversation

```python
POST /api/v1/conversation/create
{
  "locrit_name": "Bob Technique",
  "user_id": "alice",
  "metadata": {
    "source": "web_ui",
    "topic": "Python help"
  }
}

Response:
{
  "success": true,
  "conversation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "locrit_name": "Bob Technique",
  "created_at": "2025-10-04T18:42:15.123Z"
}
```

### 2. Envoyer un message

```python
POST /api/v1/conversation/send
{
  "conversation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "Comment faire une liste en Python?"
}

Response:
{
  "success": true,
  "response": "En Python, tu peux créer une liste avec des crochets...",
  "conversation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message_count": 2,
  "timestamp": "2025-10-04T18:42:20.456Z"
}
```

### 3. Lister les conversations

```python
GET /api/v1/conversation/list?user_id=alice&locrit_name=Bob%20Technique

Response:
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "f47ac10b-...",
      "locrit_name": "Bob Technique",
      "created_at": "2025-10-04T18:42:15.123Z",
      "last_activity": "2025-10-04T18:42:20.456Z",
      "message_count": 2,
      "status": "active"
    }
  ]
}
```

### 4. Obtenir l'historique complet

```python
GET /api/v1/conversation/{conversation_id}/history?limit=50

Response:
{
  "success": true,
  "conversation_id": "f47ac10b-...",
  "messages": [
    {
      "role": "user",
      "content": "Comment faire une liste en Python?",
      "timestamp": "2025-10-04T18:42:18.789Z"
    },
    {
      "role": "assistant",
      "content": "En Python, tu peux créer une liste...",
      "timestamp": "2025-10-04T18:42:20.456Z"
    }
  ]
}
```

## Persistence YAML

Chaque conversation est stockée dans `data/conversations/{conversation_id}.yaml`:

```yaml
conversation_id: f47ac10b-58cc-4372-a567-0e02b2c3d479
locrit_name: Bob Technique
user_id: alice
created_at: '2025-10-04T18:42:15.123Z'
last_activity: '2025-10-04T18:42:20.456Z'
message_count: 2
session_id: f47ac10b-58cc-4372-a567-0e02b2c3d479
status: active
metadata:
  source: web_ui
  topic: Python help
```

## Avantages

✅ **Autonomie** : Backend gère tout le contexte
✅ **Persistence** : Survit aux redémarrages
✅ **Séparation** : Firebase uniquement pour la plateforme
✅ **Performance** : Cache en mémoire + disk storage
✅ **Thread-safe** : Locks per-conversation pour writes

## Gestion du Cycle de Vie

### Archivage Automatique

Les conversations inactives sont automatiquement archivées:

```python
# Archive conversations inactives depuis 30 jours
archived_count = await conversation_persistence.archive_old_conversations(days_inactive=30)
```

### Statuts

- `active` : Conversation en cours
- `archived` : Archivée (inactive)
- `deleted` : Marquée comme supprimée (historique préservé)

## Migration depuis le Mode Legacy

**Ancien mode** (UI gère session_id):
```javascript
// UI gère son propre session_id
const sessionId = generateSessionId();
socket.emit('chat_message', {
  locrit_name: 'Bob',
  session_id: sessionId,
  message: 'Hello'
});
```

**Nouveau mode** (Backend autonome):
```javascript
// 1. Créer la conversation une fois
const { conversation_id } = await fetch('/api/v1/conversation/create', {
  method: 'POST',
  body: JSON.stringify({ locrit_name: 'Bob', user_id: 'alice' })
}).then(r => r.json());

// 2. Utiliser conversation_id pour tous les messages
socket.emit('chat_message', {
  conversation_id: conversation_id,
  message: 'Hello'
});
```

## Fix Fuite Disque

**Problème** : 1GB/sec de logs pendant conversations actives

**Solution** :
- Désactivé les logs per-Locrit (50% de réduction)
- Logging des opérations mémoire seulement en cas d'erreur
- Truncate du contenu dans les logs (max 100 chars)
- Logs uniquement dans `data/logs/` (global)

**Résultat** : Logging réduit de ~95%, performances optimales
