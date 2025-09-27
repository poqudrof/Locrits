# Locrit

Un système de gestion de chatbots autonomes avec interfaces TUI et Web. Chaque "locrit" possède sa propre identité, mémoire et capacités d'agentivité.

## 🚀 Démarrage rapide

### 🌐 Interface Web (Recommandée)
```bash
# 1. Activer l'environnement virtuel
source .venv/bin/activate

# 2. Installer les dépendances (si nécessaire)
pip install -r requirements.txt

# 3. Démarrer le backend
python web_app.py

# 4. Ouvrir dans votre navigateur
# http://localhost:5000
```

### 💻 Interface Terminal (TUI)
```bash
# 1. Démarrage rapide
./start.sh

# 2. Ou manuellement
source .venv/bin/activate
python main.py
```

### 🎯 Frontend React (Optionnel)
```bash
# 1. Aller dans le dossier frontend
cd frontend

# 2. Installer les dépendances
npm install

# 3. Démarrer le serveur de développement
npm run dev

# 4. Ouvrir dans votre navigateur
# http://localhost:5174
```

> **Note**: Le backend Flask doit être démarré en premier pour que le frontend puisse communiquer avec l'API.

## ✨ Fonctionnalités implémentées

### Core Services ✅
- 🖥️ **Interface TUI** avec Textual - Navigation intuitive et événements asynchrones
- 🌐 **Interface Web** moderne avec Flask - Gestion complète des Locrits via navigateur
- 🔍 **Recherche web** intégrée via DuckDuckGo - Service fonctionnel
- 🤖 **Chat avec LLM** via Ollama - Client asynchrone avec gestion des modèles
- 🧠 **Mémoire persistante** SQLite + recherche vectorielle FAISS
- 📊 **Monitoring de statut** en temps réel pour tous les services
- ⚙️ **Auto-configuration** des services avec gestion des erreurs
- 🔐 **Authentification Firebase** - Sécurisation des accès
- 📝 **Logging avancé** - Journalisation intelligente avec UI/fichiers séparés

### Services Avancés 🔧 (Implémentés, en cours d'intégration)
- 🔗 **API REST/WebSocket** FastAPI pour communication inter-locrits
- 🌐 **Tunneling SSH** pour accès distant (localhost.run, pinggy.io)
- 🧮 **Embeddings vectoriels** sentence-transformers + recherche sémantique
- 🏗️ **Architecture modulaire** avec LocritManager central

## 🏗️ État de développement

### Architecture actuelle
```
src/
├── app.py                 # Interface TUI Textual ✅
├── services/
│   ├── locrit_manager.py  # Coordinateur central 🔧
│   ├── ollama_service.py  # Client LLM asynchrone ✅
│   ├── search_service.py  # DuckDuckGo integration ✅
│   ├── memory_service.py  # SQLite + embeddings ✅
│   ├── embedding_service.py # Sentence transformers + FAISS ✅
│   ├── api_service.py     # FastAPI REST/WebSocket ✅
│   └── tunneling_service.py # SSH tunnels ✅
```

### Prochaines étapes
- **Integration finale** : Connecter tous les services dans LocritManager
- **Interface avancée** : Boutons pour mode serveur, tunneling, recherche sémantique
- **Tests d'intégration** : Validation de la communication inter-locrits
- **Documentation** : Guide utilisateur complet avec exemples

### Notes techniques
- **Python 3.12.2** avec environnement virtuel configuré
- **Dépendances** : textual, ollama, sentence-transformers, faiss-cpu, fastapi
- **Base de données** : SQLite avec index FAISS pour recherche vectorielle
- **Communication** : REST API + WebSocket pour temps réel

## ⚙️ Configuration des variables d'environnement

### Variables Backend (Flask)
```bash
# Port de l'interface web (défaut: 5000)
export WEB_PORT=5000

# Host d'écoute (défaut: localhost)
export WEB_HOST=localhost

# Mode debug Flask (défaut: False)
export FLASK_DEBUG=true

# Clé secrète pour les sessions (générez-en une en production)
export FLASK_SECRET_KEY=your-secret-key-here
```

### Variables Frontend (React)
```bash
# URL de l'API backend (défaut: http://localhost:5000)
VITE_API_URL=http://localhost:5000

# Mode de développement
VITE_NODE_ENV=development
```

### 🔧 Résolution des problèmes CORS

Si vous rencontrez des erreurs CORS entre le frontend et le backend :

1. **Vérifiez que le backend est démarré en premier**
2. **Ports supportés automatiquement** : 3000, 5173, 5174 (localhost et localhost)
3. **Test CORS** : `python test_cors.py` (après installation des dépendances)

Le backend est configuré pour accepter les requêtes cross-origin depuis les ports de développement standard.

## 🎮 Utilisation

### Interface Terminal (TUI)
- **Champ de saisie** : Entrez vos requêtes/messages
- **🔍 Rechercher** : Recherche web avec analyse
- **🤖 Chat** : Discussion avec le LLM (Entrée = Chat par défaut)
- **💾 Statut** : Vérifier l'état des services
- **🧠 Mémoire** : Rechercher dans l'historique
- **🗑️ Effacer** : Nettoyer le journal

#### Raccourcis clavier TUI
- `d` : Basculer mode sombre/clair
- `q` : Quitter l'application

### Interface Web 🌐

L'interface web offre une expérience complète et moderne pour gérer vos Locrits :

#### **🏠 Tableau de bord**
- Vue d'ensemble avec statistiques (total, actifs, inactifs)
- Liste des Locrits récents avec actions rapides
- Statut du système en temps réel

#### **📋 Gestion des Locrits**
- **Liste complète** : Voir tous vos Locrits avec détails
- **Création** : Formulaire complet pour nouveaux Locrits
- **Édition** : Modifier configurations existantes
- **Actions rapides** : Démarrer/Arrêter, Supprimer

#### **⚙️ Configuration**
- **Paramètres Ollama** : URL serveur, modèle par défaut, timeout
- **Configuration réseau** : Host/port API
- **Préférences UI** : Thème, intervalle de rafraîchissement
- **Test de connexion** : Vérifier la connectivité Ollama

#### **🔧 Fonctionnalités avancées**
- **Authentification Firebase** : Connexion sécurisée
- **Interface responsive** : Compatible mobile/desktop
- **Validation en temps réel** : Formulaires intelligents
- **Notifications** : Feedback utilisateur immédiat
- **Raccourcis clavier** : `Ctrl+K` recherche, `Esc` fermer modales

## ⚙️ Configuration Ollama (optionnel)

Pour activer le chat avec LLM :

1. Installer Ollama : https://ollama.com
2. Lancer un modèle : `ollama run llama3.2`
3. Relancer Locrit - détection automatique !

## 📁 Structure du projet

```
locrit/
├── .venv/              # Environnement virtuel (configuré)
├── backend/            # Backend modulaire Flask ✨ NOUVEAU
│   ├── __init__.py     # Package backend
│   ├── app.py          # Factory Flask et runner
│   ├── config/         # Configuration Flask
│   │   ├── __init__.py
│   │   └── flask_config.py # Classes de configuration
│   ├── middleware/     # Middleware d'authentification
│   │   ├── __init__.py
│   │   └── auth.py     # Décorateurs d'auth
│   └── routes/         # Routes modulaires
│       ├── __init__.py
│       ├── auth.py     # Authentification (login/logout)
│       ├── dashboard.py # Tableau de bord
│       ├── locrits.py  # CRUD Locrits
│       ├── chat.py     # Chat avec Locrits
│       ├── config.py   # Configuration app
│       ├── errors.py   # Gestionnaires d'erreurs
│       └── api/        # API publique
│           ├── __init__.py
│           └── v1.py   # API v1 inter-Locrits
├── frontend/           # Frontend React (optionnel)
│   ├── package.json    # Dépendances Node.js
│   ├── vite.config.js  # Configuration Vite
│   ├── src/            # Code source React
│   └── public/         # Assets publics
├── src/                # Code source TUI
│   ├── app.py          # Interface TUI principale
│   ├── ui/             # Interfaces utilisateur
│   │   └── screens/    # Écrans TUI
│   └── services/       # Services backend
│       ├── locrit_manager.py     # Coordinateur principal
│       ├── ollama_service.py     # Connexion LLM
│       ├── search_service.py     # Recherche web
│       ├── memory_service.py     # Mémoire persistante
│       ├── auth_service.py       # Authentification Firebase
│       ├── config_service.py     # Configuration YAML
│       └── ui_logging_service.py # Logging UI/fichiers
├── templates/          # Templates HTML (Interface Web)
│   ├── base.html       # Template de base avec navigation
│   ├── login.html      # Page de connexion
│   ├── dashboard.html  # Tableau de bord principal
│   ├── locrits_list.html # Liste des Locrits
│   ├── create_locrit.html # Création de Locrit
│   ├── edit_locrit.html   # Édition de Locrit
│   └── app_config.html    # Configuration de l'app
├── static/             # Fichiers statiques (CSS, JS)
│   ├── css/style.css   # Styles modernes
│   └── js/app.js       # JavaScript interactif
├── logs/               # Journaux de l'application
├── data/               # Base de données SQLite
├── admin/              # Fichiers admin Firebase SDK
├── web_app.py          # Point d'entrée backend Flask ✨
├── main.py             # Point d'entrée TUI
├── start.sh            # Script de lancement TUI
├── config.yaml         # Configuration principale
├── package.json        # Métadonnées projet Node.js
└── requirements.txt    # Dépendances Python
```

## 🧠 Capacités actuelles

### Interface Terminal (TUI)
- ✅ **Recherche autonome** avec analyse contextuelle
- ✅ **Mémoire conversationnelle** avec recherche sémantique
- ✅ **Chat intelligent** (si Ollama connecté)
- ✅ **Interface responsive** et intuitive
- ✅ **Monitoring système** en temps réel

### Interface Web 🌐
- ✅ **Gestion complète des Locrits** via navigateur
- ✅ **Authentification sécurisée** avec Firebase
- ✅ **Configuration centralisée** de l'application
- ✅ **Interface moderne et responsive**
- ✅ **Opérations en temps réel** (start/stop/delete)
- ✅ **Validation avancée** des formulaires
- ✅ **Logging intelligent** (UI + fichiers séparés)

## 🔮 Fonctionnalités prévues

Voir `FEATURES.md` pour la roadmap complète :
- Mode serveur API pour communication inter-locrits
- Agentivité avancée (actions multi-étapes)
- Tunneling SSH pour accès distant
- Communication inter-locrits autonome

## 🚀 Installation complète

1. **Cloner le repository**
```bash
git clone <repository-url>
cd locrit
```

2. **Configuration Python (Backend + TUI)**
```bash
# L'environnement virtuel est déjà configuré
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Configuration Node.js (Frontend React - Optionnel)**
```bash
cd frontend
npm install
```

4. **Configuration Ollama (Optionnel)**
```bash
# Installer Ollama : https://ollama.com
# Puis lancer un modèle
ollama run llama3.2
```

## 🔧 Dépendances installées

### Interface et Frameworks
- **textual** : Framework TUI (Terminal User Interface)
- **flask** : Framework web moderne pour l'interface web ✨
- **fastapi** : API REST/WebSocket pour communication inter-locrits

### Intelligence Artificielle
- **ollama** : Client pour les modèles de langage locaux
- **sentence-transformers** : Modèles d'embedding pour recherche sémantique
- **faiss-cpu** : Recherche vectorielle rapide

### Services et Utilitaires
- **firebase-admin** : Authentification et base de données Firebase
- **duckduckgo-search** : Recherche web via DuckDuckGo
- **beautifulsoup4** : Parsing HTML/XML
- **lxml** : Parser XML/HTML rapide
- **sqlite-utils** : Utilitaires pour SQLite
- **python-dotenv** : Gestion des variables d'environnement
- **pyyaml** : Configuration YAML
