# Routes Publiques des Locrits

Ce document décrit le système de pages publiques pour les Locrits, permettant aux visiteurs d'interagir avec eux via une interface web.

## 📋 Vue d'ensemble

Les Locrits peuvent être rendus accessibles publiquement via Internet. Lorsqu'un Locrit a l'option `open_to.internet = true`, il devient accessible via :
- Une page personnalisable
- Une interface de chat pour les visiteurs
- Un annuaire public listant tous les Locrits accessibles

## 🔧 Configuration

### Activer l'accès public pour un Locrit

Dans `config.yaml`, configurez votre Locrit :

```yaml
locrits:
  instances:
    MonLocrit:
      active: true
      open_to:
        internet: true  # Active l'accès public
        humans: true
        locrits: true
      # ... autres paramètres
```

### Personnaliser la page publique

Vous pouvez personnaliser l'apparence et le comportement de la page publique :

```yaml
locrits:
  instances:
    MonLocrit:
      public_page:
        title: "Parlez avec MonLocrit"
        description: "Un assistant intelligent spécialisé en..."
        welcome_message: "Bonjour ! Comment puis-je vous aider aujourd'hui ?"
        theme: "default"
        avatar: "🤖"
        show_model_info: true
        custom_css: ""  # CSS personnalisé (futur)
```

## 🌐 Routes API Backend

### GET `/public/<locrit_name>`
Récupère les informations publiques d'un Locrit.

**Réponse réussie :**
```json
{
  "success": true,
  "locrit": {
    "name": "MonLocrit",
    "description": "Description du Locrit",
    "model": "llama3.2",
    "public_address": "monlocrit.locritland.net",
    "page_config": {
      "title": "Parlez avec MonLocrit",
      "description": "Un assistant intelligent",
      "welcome_message": "Bonjour !",
      "theme": "default",
      "avatar": "🤖"
    },
    "active": true
  }
}
```

**Erreurs possibles :**
- `404` : Locrit introuvable
- `403` : Locrit non actif ou non ouvert à Internet

### POST `/public/<locrit_name>/chat`
Envoie un message à un Locrit public.

**Corps de la requête :**
```json
{
  "visitor_name": "Jean",
  "message": "Bonjour, comment ça va ?"
}
```

**Réponse réussie :**
```json
{
  "success": true,
  "response": "Bonjour Jean ! Je vais bien, merci. Comment puis-je vous aider ?",
  "locrit_name": "MonLocrit",
  "timestamp": "2025-10-02T20:30:00.000Z"
}
```

### GET `/public/list`
Liste tous les Locrits accessibles publiquement.

**Réponse :**
```json
{
  "success": true,
  "locrits": [
    {
      "name": "MonLocrit",
      "description": "Un assistant intelligent",
      "public_address": "monlocrit.locritland.net",
      "avatar": "🤖",
      "title": "Parlez avec MonLocrit"
    }
  ],
  "count": 1
}
```

### PUT `/public/<locrit_name>/settings`
Met à jour la configuration de la page publique d'un Locrit.

**Corps de la requête :**
```json
{
  "page_config": {
    "title": "Nouveau titre",
    "description": "Nouvelle description",
    "welcome_message": "Nouveau message de bienvenue",
    "theme": "default",
    "avatar": "🦊"
  }
}
```

## 🎨 Routes Frontend (Platform)

### `/public`
Annuaire des Locrits publics - Liste tous les Locrits accessibles.

**URL :** `http://localhost:3003/public`

### `/public/:locritName`
Page de chat avec un Locrit spécifique.

**URL :** `http://localhost:3003/public/MonLocrit`

**Fonctionnalités :**
1. Saisie du nom du visiteur
2. Affichage du message de bienvenue personnalisé
3. Interface de chat en temps réel
4. Gestion des erreurs et états de chargement

## 🔒 Sécurité

### Vérifications automatiques

Le système vérifie automatiquement :
- ✅ Le Locrit est actif (`active: true`)
- ✅ Le Locrit est ouvert à Internet (`open_to.internet: true`)

Si l'une de ces conditions n'est pas remplie, l'accès est refusé avec un code 403.

### Futures améliorations de sécurité

- [ ] Rate limiting pour éviter le spam
- [ ] Captcha pour les nouveaux visiteurs
- [ ] Authentification optionnelle pour les propriétaires
- [ ] Logs des conversations publiques
- [ ] Modération des messages

## 📊 Logs et Monitoring

Les conversations publiques sont automatiquement loggées :

```
[INFO] Conversation publique avec MonLocrit - Visiteur: Jean
```

Chaque message envoyé au Locrit inclut le contexte :
```
[Conversation publique avec Jean via l'interface web]
Bonjour, comment ça va ?
```

## 🚀 Utilisation

### Pour les visiteurs

1. Accédez à `/public` pour voir la liste des Locrits disponibles
2. Cliquez sur un Locrit ou accédez directement à `/public/<nom-du-locrit>`
3. Entrez votre nom
4. Commencez à discuter !

### Pour les propriétaires de Locrits

1. Activez l'accès public dans `config.yaml`
2. Personnalisez la page via l'API ou directement dans le fichier de config
3. Partagez l'URL publique de votre Locrit

## 🔗 Exemples d'utilisation

### Curl - Tester l'API

```bash
# Récupérer les infos d'un Locrit
curl http://localhost:5000/public/MonLocrit

# Envoyer un message
curl -X POST http://localhost:5000/public/MonLocrit/chat \
  -H "Content-Type: application/json" \
  -d '{"visitor_name": "Alice", "message": "Bonjour !"}'

# Lister les Locrits publics
curl http://localhost:5000/public/list
```

### JavaScript - Intégration web

```javascript
// Charger les infos du Locrit
const response = await fetch('http://localhost:5000/public/MonLocrit');
const data = await response.json();

// Envoyer un message
const chatResponse = await fetch('http://localhost:5000/public/MonLocrit/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    visitor_name: 'Alice',
    message: 'Bonjour !'
  })
});
const chatData = await chatResponse.json();
console.log(chatData.response);
```

## 🎯 Cas d'usage

- **Support client** : Locrits spécialisés en service client
- **Assistants éducatifs** : Tuteurs pour différents sujets
- **Divertissement** : Personnages de jeu ou storytelling
- **Consultation** : Experts dans un domaine spécifique
- **Communauté** : Assistants pour forums ou communautés

## 📝 Notes techniques

- Les routes publiques ne nécessitent pas d'authentification
- Les messages sont envoyés de manière synchrone
- Le contexte indique toujours qu'il s'agit d'une conversation publique
- Les Locrits inactifs ou privés retournent une erreur 403
- L'interface utilise React avec React Router pour le routing
- Le backend est Flask avec CORS activé pour le frontend

## 🔮 Roadmap

- [ ] WebSocket pour le chat en temps réel
- [ ] Système de thèmes personnalisables
- [ ] Statistiques de conversation
- [ ] Partage de conversations
- [ ] Embedding pour intégrer le chat sur d'autres sites
- [ ] Mode lecture seule / démo
- [ ] Limites de messages par visiteur
