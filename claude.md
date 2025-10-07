# Contexte du projet

Les Locrits sont des personnages qui sont animés par des LLMs.
Ces personnages sont «locaux» c'est à dire sur une machine.

Fonctionnalité d'un Locrit:
* Personnalité propre (prompt initial)
* Mémoire propre avec des avis (via graphe à implémenter) et souvenirs (mémoire vectorielle)

Comment un Locrit «vit»:
* L'utilisateur local peut lui parler directement via cette application.
* Il peut être exposé en ligne (via un reverse proxy tunnel par ex) pour permettre à d'autres personnes de lui parler.
* Il peut aller parler à un autre Locrit sur instruction de l'utilisateur ou de manière autonome.
* Il peut aller sur un «chat» dédié au Locrits de durée éphémère.

Les Locrits sont repertoriés en ligne:
* Grâce au FireStore pour stocker les informations sur les Locrits.
* Pour savoir comment trouver d'autres locrits et leurs parler.
* Le réseau Locrit est sur un autre dépôt / code.

Ce dépôt / code est pour les locrits locaux.

L'interface est en React, et doit être sympathique et enfantine.
Les locrits sont un peu des «enfants» ou «petits animaux» IA et
l'UX - UI doit reflèter ça.

## Avancement

Dans les premières étapes on est focus sur:
* l'implémentation de l'UI en React.
* Leur parler avec un prompt : L0.
* Leur parler avec un côté agentique : L1.
* Leur parler avec une mémoire de graphe : L2.
* Leur parler avec une mémoire vectorielle : L3.
* La création du serveur Locrit qui permet de leur donnée vie (API - UI)

---

# Architecture: Les 3 Applications

## 1️⃣ Backend (Flask) - Port 5000
**Point d'entrée:** `python backend/web_app.py`

**Rôle:**
- API REST pour gestion des Locrits (CRUD)
- WebSocket pour chat temps réel
- Gestion mémoire et conversations
- Auth Firebase
- Services: LocritManager, ConversationService, MemoryService, KuzuMemoryService, OllamaService

**Structure:**
```
backend/
├── web_app.py          # Entry point
├── app.py              # Flask factory
├── routes/             # Blueprints modulaires
│   ├── auth.py
│   ├── locrits.py
│   ├── chat.py
│   ├── conversation.py
│   ├── memory.py
│   ├── websocket.py
│   └── public.py
└── middleware/         # Auth middleware
```

## 2️⃣ Frontend (React) - Port 5174
**Démarrage:** `cd frontend && npm run dev`

**Rôle:** Interface utilisateur personnel pour gérer ses Locrits
- Dashboard, création, édition de Locrits
- Chat interface avec WebSocket
- Memory explorer
- Settings et configuration

**Tech:** React + Vite + shadcn/ui + Tailwind CSS

## 3️⃣ Platform (React) - Port 5173
**Démarrage:** `cd platform && npm run dev`

**Rôle:** Interface publique et admin
- Directory public des Locrits
- Chat public avec n'importe quel Locrit
- Conversations autonomes programmées
- Admin: gestion utilisateurs et Locrits
- Intégration Firestore pour catalogage

**Composants clés:**
- PublicLocritsDirectory, PublicLocritChat
- ScheduledConversation, ConversationManager
- Dashboard admin, UserManagement

---

# Code Instructions

## Startup
**Ordre:** Backend → Frontend et/ou Platform

```bash
# 1. Backend (obligatoire)
source .venv/bin/activate
python backend/web_app.py

# 2. Frontend (user dashboard)
cd frontend && npm run dev

# 3. Platform (public/admin)
cd platform && npm run dev
```

## Ollama Configuration
Each Locrit has its own ollama config.
If it fails to connect the server should respond with not available.
**Never use local ollama (without url).**

## Folder Structure
```
Locrits/
├── backend/         # Flask backend (port 5000)
├── frontend/        # React user UI (port 5174)
├── platform/        # React public/admin (port 5173)
├── src/services/    # Core services (shared)
├── tests/           # Unit, integration, e2e, fullstack, memory
└── data/            # SQLite, KuzuDB
```

## Testing
```bash
# All tests
./run_tests.sh

# Backend tests
python -m pytest tests/fullstack/ -v
python -m pytest tests/memory/ -v

# Frontend E2E (root)
npm run test

# Platform tests
cd platform && npm run test
cd platform && npm run test:e2e
```

## Development Rules

**Do not write code in the documentations.**

**When the code is too long (> 800 lignes) split it in modules or sub-components.**

**Trust the frameworks.** Avoid writing yourself CSS code when the components should work correctly using shadcn. Write tailwindcss instead of pure CSS when possible.

**Use BrowserMCP to debug as much as possible.**

**In the UI, allow auto-saves for each field or save buttons beside them when more important fields. Do not put save buttons at the bottom of the pages.**

**We can always chat with our local locrits.**

---

# Key Services (src/services/)

- **locrit_manager.py** - Central coordinator
- **conversation_service.py** - Conversation logic & history
- **memory_service.py** - SQLite + FAISS vectors
- **kuzu_memory_service.py** - Graph memory (KuzuDB)
- **graph_memory_service.py** - Graph operations
- **ollama_service.py** - LLM integration
- **auth_service.py** - Firebase auth
- **config_service.py** - YAML config

# Ports Reference
| Service | Port | URL |
|---------|------|-----|
| Backend | 5000 | http://localhost:5000 |
| Frontend | 5174 | http://localhost:5174 |
| Platform | 5173 | http://localhost:5173 |
| Ollama | 11434 | http://localhost:11434 |

# Documentation
See **auto-claude.md** for complete architecture, tests structure, and troubleshooting.
