# Locrit - Fonctionnalités et Architecture

## Vue d'ensemble

Locrit est un système de gestion de chatbots autonomes appelés "locrits". Chaque locrit possède sa propre i### À implémenter V1 ✅ (COMPLÉTÉ!)
- [x] Connexion Ollama
- [x] Système de mémoire hybride (SQLite + vecteurs)
- [x] Mémoire sous forme de graphes ✅ **NOUVEAU!**
- [x] Mode chat local pour l'utilisateur
- [x] Recherche internet avec DuckDuckGo
- [x] Mode serveur API (FastAPI/WebSocket) ✅ **NOUVEAU!**
- [x] Intégration avec serveur central (récupère les noms des locrits) ✅ **NOUVEAU!**
- [x] Mode client pour communication inter-locrits ✅ **NOUVEAU!**
- [x] Indicateurs de statut en temps réelgentivité et mémoire persistante, utilisant un serveur Ollama pour le modèle de langage.

## État d'implémentation (Septembre 2025)

### ✅ Services Core (Fonctionnels)
- **Interface TUI** : Application Textual complète avec gestion événements asynchrones
- **LocritManager** : Coordinateur central pour tous les services
- **OllamaService** : Client asynchrone avec gestion modèles et connexion
- **SearchService** : Intégration DuckDuckGo pour recherche web autonome
- **MemoryService** : Stockage SQLite + intégration embeddings vectoriels
- **ConfigService** : **MISE À JOUR** - Gestion .env + config.yaml + sauvegardes automatiques
- **LocalBackupService** : **NOUVEAU** - Sauvegardes locales sessions, configs et Locrits

### ✅ Services Avancés (Implémentés)
- **EmbeddingService** : sentence-transformers + index FAISS pour recherche sémantique
- **APIService** : FastAPI avec endpoints REST et WebSocket pour communication
- **TunnelingService** : Création tunnels SSH via localhost.run et pinggy.io
- **AuthService** : **MISE À JOUR** - Firebase Auth depuis .env + gestion sessions persistantes
- **FirestoreSyncService** : **NOUVEAU** - Synchronisation bidirectionnelle avec Firebase Realtime DB
- **SessionService** : **MISE À JOUR** - Sauvegarde/restauration sessions + backup local automatique

### 🔧 En cours d'intégration
- **Connexion services** : Finalisation de l'intégration dans LocritManager
- **Interface utilisateur** : Ajout boutons mode serveur, tunneling, recherche sémantique
- **Tests complets** : Validation communication inter-locrits

### 📋 TODO Priorité élevée
- Finir intégration APIService et TunnelingService dans LocritManager
- Ajouter interface TUI pour mode serveur et tunneling
- Implémenter recherche sémantique dans l'interface utilisateur
- Tests de communication WebSocket entre locrits

## Architecture de données

### Méthode de stockage : Hybrid baseline ✅ (Implémenté)

- **SQLite** : Données canoniques (id, text, metadata, timestamps, user_id)
- **Index vectoriel** : FAISS ou pgvector pour les embeddings
- **Flux de requête** : Préfiltre métadonnées (SQL) → k-NN sur embeddings → rerank (optionnel) → bundle vers LLM

## Modes de fonctionnement

### 1. Chat classique avec utilisateur ✅
Interface TUI directe pour interaction avec le locrit via Textual.
**État** : Fonctionnel avec mémoire persistante et recherche web.

### 2. Mode serveur (API) ✅ (Implémenté)
Le locrit peut servir d'API FastAPI pour communiquer avec :
- Autres utilisateurs via REST endpoints
- Autres LLMs via WebSocket
- Autres locrits via communication réseau
**État** : Service créé, en cours d'intégration dans l'interface.

### 3. Mode client ✅ (Implémenté)
Le locrit peut se connecter et dialoguer avec d'autres LLMs ou locrits.
**État** : Capabilities dans APIService, tunneling disponible.

### 4. Recherche internet ✅
Intégration avec DuckDuckGo pour recherches web autonomes.
**État** : Fonctionnel via SearchService.

### 5. Mémoire sémantique ✅ (Implémenté)
Stockage et recherche vectorielle avec embeddings.
**État** : EmbeddingService + FAISS, intégré dans MemoryService.

### 6. Tunneling réseau ✅ (Implémenté)
Accès distant via SSH tunnels automatiques.
**État** : TunnelingService créé, support localhost.run et pinggy.io.

### 5. Agentivité avancée
Capacités d'action multi-étapes :
- Recherches et navigation internet autonomes
- Communication avec d'autres locrits connus depuis sa mémoire
- Prise de décision sur les actions à entreprendre

## Interface utilisateur

### 🎨 NOUVELLE INTERFACE REFAITE (Septembre 2025)

#### 🔐 **Écran d'authentification Firebase**
- [x] Interface de connexion anonyme
- [x] Formulaire email/mot de passe
- [x] Création de nouveaux comptes  
- [x] Réinitialisation de mot de passe
- [x] Bascule entre modes connexion/création
- [x] Messages d'état et validation
- [x] Intégration Firebase Auth complète
- [x] **Configuration depuis .env** - Chargement automatique depuis variables d'environnement
- [x] **Sauvegarde session locale** - Backup automatique des sessions Firebase
- [x] **Restauration automatique** - Récupération des sessions depuis sauvegardes

#### 🏠 **Écran d'accueil principal (Dashboard)**
- [x] Interface utilisateur avec email affiché
- [x] Grille de boutons principaux 6x2
- [x] **👥 Locrits Amis En ligne** - Navigation vers écran amis
- [x] **🏠 Mes Locrits Locaux** - Gestion des Locrits locaux
- [x] **➕ Créer Nouveau Locrit** - Interface de création
- [x] **⚙️ Paramètres Application** - Configuration globale
- [x] **🔐 Déconnexion** - Retour au login
- [x] **ℹ️ À propos** - Informations application

#### 👥 **Écran Locrits Amis**
- [x] Liste des Locrits amis connectés
- [x] Statut en ligne/hors ligne avec indicateurs visuels
- [x] Recherche automatique des amis disponibles
- [x] Informations de connexion (nom, description, URL)
- [ ] Navigation vers chat avec ami sélectionné
- [x] Bouton retour vers dashboard

#### 🏠 **Écran Mes Locrits Locaux**
- [x] Liste des Locrits créés localement
- [x] **Affichage depuis config.yaml** - Lecture des 4 Locrits existants
- [x] **Synchronisation Firestore automatique** - Upload vers Firebase au chargement
- [x] **Zone de logs temps réel** - Suivi des opérations de synchronisation
- [x] Informations détaillées par Locrit (nom, description, statut, date, modèle, adresse)
- [x] Actions par Locrit : 
  - [x] Démarrer/arrêter
  - [ ] Configurer
  - [x] Chat direct
  - [x] Supprimer
- [x] **Bouton synchronisation manuelle** - Force la sync avec Firestore
- [x] Indicateurs de statut (actif, mode serveur, tunnel)
- [x] Bouton retour vers dashboard
- [x] Bouton créer nouveau Locrit
- [x] **Sauvegarde locale automatique** - Backup des Locrits dans data/backups/

#### ➕ **Écran Création de Locrit**
- [x] **Informations de base** :
  - [x] Champ nom du Locrit
  - [x] Champ description courte
  - [x] Champ adresse publique
- [x] **Paramètres d'ouverture** (boutons toggle) :
  - [x] 👥 Ouvert aux humains
  - [x] 🤖 Ouvert aux autres Locrits
  - [x] 📧 Ouvert aux invitations
  - [x] 🌐 Ouvert à Internet public
  - [x] 🏢 Ouvert à la plateforme publique
- [x] **Paramètres d'accès** (boutons toggle) :
  - [x] 📋 Accès aux logs
  - [x] 🧠 Accès mémoire rapide
  - [x] 🗂️ Accès mémoire complète
  - [x] 🤖 Accès infos LLM
- [x] **Actions** :
  - [x] ✅ Bouton créer avec validation
  - [x] 🔙 Bouton annuler
  - [x] Gestion des erreurs de création
  - [x] Sauvegarde dans configuration YAML

#### ⚙️ **Écran Paramètres Application**
- [x] **Configuration Ollama depuis .env** :
  - [x] Chargement automatique de OLLAMA_HOST depuis .env
  - [x] Support OLLAMA_DEFAULT_MODEL depuis .env
  - [x] Champ adresse serveur Ollama (override local)
  - [x] Bouton test de connexion
  - [x] Indicateur de statut connexion
  - [x] Sauvegarde configuration locale + backup automatique
- [x] **Configuration Tunnel** :
  - [x] Champ URL publique (optionnel)
  - [x] Bouton activer/désactiver tunnel
  - [x] Statut du tunnel actuel
- [x] **Informations & Diagnostics** :
  - [x] **Statut des sauvegardes locales** - Nombre et dates des backups
  - [ ] Bouton voir logs application
  - [ ] Bouton diagnostics système
  - [ ] Bouton voir erreurs
  - [x] Bouton recharger configuration
- [x] **Informations système** :
  - [x] Chemins de fichiers (DB, config, backups)
  - [x] Thème et paramètres UI
- [x] Bouton retour vers dashboard

#### 💬 **Écran Chat avec Locrit**
- [x] Interface de chat temps réel
- [x] Historique des conversations
- [x] Informations du Locrit contacté
- [x] Zone de saisie avec bouton envoyer
- [x] Envoi avec touche Entrée
- [x] Messages utilisateur et Locrit différenciés
- [x] Boutons d'action (effacer, sauvegarder)
- [x] Retour vers liste des Locrits
- [x] Indicateur de frappe
- [x] Simulation de réponses (en attente Ollama)

#### ℹ️ **Écran À propos**
- [x] Informations version de Locrit
- [x] Statut des services connectés
- [x] Informations de licence
- [x] Bouton retour vers dashboard

### 📱 **Système de navigation**
- [x] Navigation par écrans (Screen push/pop)
- [x] Cohérence visuelle entre écrans
- [x] Gestion des retours (boutons 🔙)
- [x] Raccourcis clavier globaux (d=dark, q=quit)

### 🎨 **Design et UX**
- [x] Thème Textual cohérent avec CSS
- [x] Emojis pour identification rapide
- [x] Classes CSS pour sections (containers, buttons, etc.)
- [x] Gestion des couleurs par type d'action
- [x] Messages de notification (self.notify)
- [x] Indicateurs de statut visuels

### ⚙️ **Système de configuration**
- [x] Fichier config.yaml complet
- [x] Service ConfigService pour gestion
- [x] Chargement/sauvegarde automatique
- [x] Configuration par défaut
- [x] Paramètres Ollama, réseau, UI
- [x] Gestion des Locrits instances
- [x] Validation et gestion d'erreurs
- [ ] **⚙️ Paramètres Application** - Configuration globale
- [ ] **🔐 Déconnexion** - Retour au login
- [ ] **ℹ️ À propos** - Informations application

#### 👥 **Écran Locrits Amis**
- [ ] Liste des Locrits amis connectés
- [ ] Statut en ligne/hors ligne avec indicateurs visuels
- [ ] Recherche automatique des amis disponibles
- [ ] Informations de connexion (nom, description, URL)
- [ ] Navigation vers chat avec ami sélectionné
- [ ] Bouton retour vers dashboard

#### 🏠 **Écran Mes Locrits Locaux**
- [ ] Liste des Locrits créés localement
- [ ] Informations pour chaque Locrit (nom, description, statut)
- [ ] Actions par Locrit : 
  - [ ] Démarrer/arrêter
  - [ ] Configurer
  - [ ] Chat direct
  - [ ] Supprimer
- [ ] Indicateurs de statut (actif, mode serveur, tunnel)
- [ ] Bouton retour vers dashboard

#### ➕ **Écran Création de Locrit**
- [ ] **Informations de base** :
  - [ ] Champ nom du Locrit
  - [ ] Champ description courte
  - [ ] Champ adresse publique
- [ ] **Paramètres d'ouverture** (boutons toggle) :
  - [ ] 👥 Ouvert aux humains
  - [ ] 🤖 Ouvert aux autres Locrits
  - [ ] 📧 Ouvert aux invitations
  - [ ] 🌐 Ouvert à Internet public
  - [ ] 🏢 Ouvert à la plateforme publique
- [ ] **Paramètres d'accès** (boutons toggle) :
  - [ ] 📋 Accès aux logs
  - [ ] 🧠 Accès mémoire rapide
  - [ ] 🗂️ Accès mémoire complète
  - [ ] 🤖 Accès infos LLM
- [ ] **Actions** :
  - [ ] ✅ Bouton créer avec validation
  - [ ] 🔙 Bouton annuler
  - [ ] Gestion des erreurs de création

#### ⚙️ **Écran Paramètres Application**
- [ ] **Configuration Ollama** :
  - [ ] Champ adresse serveur Ollama
  - [ ] Bouton test de connexion
  - [ ] Indicateur de statut connexion
- [ ] **Configuration Tunnel** :
  - [ ] Champ URL publique (optionnel)
  - [ ] Bouton activer/désactiver tunnel
  - [ ] Statut du tunnel actuel
- [ ] **Informations & Diagnostics** :
  - [ ] Bouton voir logs application
  - [ ] Bouton diagnostics système
  - [ ] Bouton voir erreurs
- [ ] Bouton retour vers dashboard

#### 💬 **Écran Chat avec Locrit** (À créer)
- [ ] Interface de chat temps réel
- [ ] Historique des conversations
- [ ] Informations du Locrit contacté
- [ ] Boutons d'action (partager fichier, etc.)
- [ ] Retour vers liste des Locrits

#### ℹ️ **Écran À propos**
- [ ] Informations version de Locrit
- [ ] Statut des services connectés
- [ ] Informations de licence
- [ ] Bouton retour vers dashboard

### 📱 **Système de navigation**
- [ ] Navigation par écrans (Screen push/pop)
- [ ] Cohérence visuelle entre écrans
- [ ] Gestion des retours (boutons 🔙)
- [ ] Raccourcis clavier globaux (d=dark, q=quit)

### 🎨 **Design et UX**
- [ ] Thème Textual cohérent avec CSS
- [ ] Emojis pour identification rapide
- [ ] Classes CSS pour sections (containers, buttons, etc.)
- [ ] Gestion des couleurs par type d'action
- [ ] Responsive design pour différentes tailles terminal

### Configuration ✅ (Implémenté - ANCIENNE INTERFACE)
- **Serveur Ollama** : Configuration de l'adresse (localhost:port par défaut)
- **Indicateurs de statut** : 
  - ✅ LLM connecté
  - ✅ Mémoire initialisée  
  - ✅ Recherche web active
  - ✅ Services API prêts
- **Interface TUI** : Navigation complète avec boutons pour toutes les fonctions

### Accès distant ✅ (Implémenté)
- **Tunneling automatique** : Intégration avec localhost.run et pinggy.io
- **TunnelingService** : Création automatique de tunnels SSH  
- **Workflow** : 
  1. Détection SSH disponible
  2. Création tunnel vers port local FastAPI
  3. Génération URL publique accessible
  4. Retour URL pour partage/communication

### Architecture de communication ✅
- **FastAPI server** : Endpoints REST pour communication externe
- **WebSocket** : Canal temps réel pour chat inter-locrits
- **Découverte réseau** : Mécanismes pour locrits de se connecter

## Extensions futures 📋

### Interface web avancée
- **Dashboard multi-locrits** : Gestion centralisée de plusieurs instances
- **Configuration graphique** : Interface web pour paramètres avancés
- **Monitoring réseau** : Visualisation des connexions inter-locrits

### Sécurité et authentification  
- **Chiffrement communications** : TLS/SSL pour tunnels et API
- **Authentification** : Tokens pour accès sécurisé entre locrits
- **Permissions** : Contrôle d'accès granulaire aux fonctions

### Agentivité avancée
- **Navigation web autonome** : BeautifulSoup + selenium pour interactions
- **Planification multi-étapes** : Système de tâches avec persistance
- **Apprentissage** : Adaptation du comportement selon l'usage

## État de développement (Mis à jour - Septembre 2025)

### ✅ Implémenté et fonctionnel
- **Interface TUI complète** avec Textual - Navigation et événements asynchrones
- **Services core** : Ollama, Search, Memory avec SQLite
- **Architecture modulaire** : LocritManager pour coordination centrale
- **Mémoire hybride** : SQLite + embeddings vectoriels FAISS  
- **Communication API** : FastAPI avec REST endpoints et WebSocket
- **Tunneling réseau** : SSH automatique via localhost.run/pinggy.io
- **Recherche sémantique** : sentence-transformers + recherche par similarité

### 🔧 En cours d'intégration
- **Connexion finale** des services avancés dans LocritManager
- **Interface utilisateur** pour mode serveur et tunneling
- **Tests communication** inter-locrits via WebSocket

### 📋 Prochaines priorités
- Finalisation intégration APIService et TunnelingService
- Interface TUI pour contrôler mode serveur et tunnels  
- Tests end-to-end de communication entre locrits distants
- Documentation utilisateur avec exemples pratiques

### 🏗️ Architecture technique V1 - FINALISÉE
```
Locrit/
├── main.py                    # Point d'entrée ✅
├── src/
│   ├── app.py                # TUI Textual complète ✅  
│   └── services/
│       ├── locrit_manager.py # Coordinateur central ✅
│       ├── ollama_service.py # Client LLM ✅
│       ├── search_service.py # DuckDuckGo ✅
│       ├── memory_service.py # SQLite + embeddings ✅
│       ├── embedding_service.py # Vectoriel FAISS ✅
│       ├── api_service.py    # FastAPI + WebSocket ✅
│       ├── tunneling_service.py # SSH tunnels ✅
│       ├── central_server_service.py # Découverte ✅ NEW!
│       └── graph_memory_service.py # Mémoire graphe ✅ NEW!
```

## ✨ Fonctionnalités V1 complètes


### Architecture de mémoire révolutionnaire
- **Stockage canonique** : SQLite pour persistance
- **Recherche sémantique** : Embeddings + FAISS pour similarité
- **Graphe de relations** : Apprentissage automatique des concepts liés
- **Contexte intelligent** : Combinaison des 3 types de mémoire pour réponses enrichies

### Communication inter-locrits avancée
- **Mode serveur** : API REST + WebSocket pour communication temps réel
- **Mode client** : Connexion à d'autres locrits via URL
- **Tunneling SSH** : Accès distant automatique (localhost.run/pinggy.io)
- **Serveur central** : Découverte et enregistrement de locrits
- **Mémoire partagée** : Les interactions avec autres locrits sont mémorisées

### 📊 Métriques de progression V1 - COMPLÉTÉ! 🎉
- **Services implémentés** : 8/8 (100%) ✅
- **Intégration services** : 8/8 (100%) ✅
- **Interface utilisateur** : Complète avec toutes les fonctions ✅
- **Communication inter-locrits** : Infrastructure complète ✅
- **Mémoire graphe** : Système d'apprentissage de relations ✅
- **Serveur central** : Découverte et enregistrement ✅
- Connexion Ollama avec auto-détection
- Système de mémoire hybride (SQLite de base)
- Recherche internet avec DuckDuckGo
- Architecture services modulaires
- Indicateurs de statut en temps réel
- Gestionnaire coordinateur (LocritManager)

### En cours de développement
- Serveur central pour coordination des locrits
- Système de comptes et authentification

### À implémenter  V1 
- [x] Connexion Ollama
- [x] Système de mémoire hybride (SQLite + vecteurs)
- [ ] Mémoire sous forme de graphes 
- [ ] Mode chat local pour l’utilisateur
- [x] Recherche internet avec DuckDuckGo
- [ ] Mode serveur API (FastAPI/WebSocket)
- [ ] Intégration avec serveur central (récupère les noms des locrits)
- [ ] Mode client pour communication inter-locrits Utilise le nom du locrit
- [x] Indicateurs de statut en temps réel


### Pour la V2 - IA 

- [ ] Interface de configuration Ollama avancée
- [ ] Communication inter-locrits autonome
- [ ] Système d'agentivité multi-étapes
- [ ] Actions autonomes (navigation web, etc.)

### Pour la V2 - Réseau 

- [ ] Tunneling automatique pour accès distant

## Technologies clés

- **Textual** : Interface utilisateur TUI
- **Ollama** : Serveur de modèles de langage
- **SQLite** : Base de données locale
- **FAISS/pgvector** : Index vectoriel pour embeddings
- **DuckDuckGo Search** : Recherche internet
- **BeautifulSoup4/lxml** : Parsing de contenu web
- **sqlite-utils** : Utilitaires base de données
- **SSH tunneling** : Accès distant via localhost.run/pinggy.io
