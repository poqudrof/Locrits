# Locrit - Frontend Features (React)

## Vue d'ensemble

Frontend React pour Locrit - système de gestion de chatbots autonomes appelés "locrits". Interface moderne utilisant React, Shadcn/ui, et Tailwind CSS pour une expérience utilisateur fluide et responsive.

## État d'implémentation (Septembre 2025)

## Architecture de données frontend

### Méthode de stockage : Client-side state management
- **React Context** : État global de l'application
- **Local Storage** : Persistance des préférences utilisateur
- **API Communication** : Communication avec backend SQLite/FAISS
- **WebSocket** : Communication temps réel avec les locrits

## Modes de fonctionnement - Interface

### 1. Chat classique avec utilisateur
Interface React moderne pour interaction directe avec le locrit.
**État** : À implémenter avec composants Shadcn/ui.

### 2. Mode serveur (API)
Interface de gestion pour le mode serveur FastAPI du locrit.
**État** : À créer avec tableaux de bord et métriques.

### 3. Mode client
Interface pour la connexion et dialogue avec d'autres LLMs ou locrits.
**État** : À implémenter avec liste de connexions disponibles.

### 4. Recherche internet
Interface pour les recherches web autonomes via DuckDuckGo.
**État** : À créer avec historique de recherches et résultats.

### 5. Mémoire sémantique
Interface de visualisation et gestion de la mémoire vectorielle.
**État** : À implémenter avec graphiques et recherche sémantique.

### 6. Tunneling réseau
Interface de gestion pour l'accès distant via SSH tunnels.
**État** : À créer avec configuration et monitoring des tunnels.

## Interface utilisateur

### 🎨 INTERFACE REACT À CRÉER (Septembre 2025)

#### 🔐 **Écran d'authentification Firebase**
- [ ] Interface de connexion anonyme avec Shadcn components
- [ ] Formulaire email/mot de passe responsive + sans login (sans internet) + avec Google
- [ ] Messages d'état et validation avec Toast
- [ ] Intégration Firebase Auth complète
- [ ] Configuration depuis variables d'environnement
- [ ] Sauvegarde session locale dans LocalStorage
- [ ] Restauration automatique des sessions

#### 🏠 **Dashboard principal**
- [ ] Interface utilisateur avec email affiché  ( ou local si pas internet )
- [ ] Grille de cartes principales responsive
- [ ] **👥 Locrits Amis En ligne** - Navigation vers écran amis
- [ ] **🏠 Mes Locrits Locaux** - Gestion des Locrits locaux
- [ ] **➕ Créer Nouveau Locrit** - Interface de création
- [ ] **⚙️ Paramètres Application** - Configuration globale
- [ ] **🔐 Déconnexion** - Retour au login
- [ ] **ℹ️ À propos** - Informations application
- [ ] Navigation responsive avec menu mobile

#### 👥 **Écran Locrits Amis**
- [ ] Liste des Locrits amis connectés avec cartes
- [ ] Statut en ligne/hors ligne avec badges visuels
- [ ] Recherche automatique avec filtre en temps réel
- [ ] Informations de connexion (nom, description, URL)
- [ ] Navigation vers chat avec ami sélectionné
- [ ] Bouton retour vers dashboard
- [ ] Interface responsive pour mobile/desktop

#### 🏠 **Écran Mes Locrits Locaux**
- [ ] Liste des Locrits créés localement avec cartes
- [ ] Affichage depuis API backend config
- [ ] Synchronisation Firestore en temps réel
- [ ] Zone de logs temps réel avec WebSocket
- [ ] Informations détaillées par Locrit
- [ ] Actions par Locrit avec boutons Shadcn :
  - [ ] Démarrer/arrêter avec Switch
  - [ ] Configurer avec Dialog
  - [ ] Chat direct
  - [ ] Supprimer avec confirmation
- [ ] Bouton synchronisation manuelle
- [ ] Indicateurs de statut avec Badge components
- [ ] Interface responsive avec grille adaptative

#### ➕ **Écran Création de Locrit**
- [ ] **Informations de base** avec Form components :
  - [ ] Champ nom du Locrit avec validation
  - [ ] Champ description avec Textarea
  - [ ] Champ adresse publique avec Input
- [ ] **Paramètres d'ouverture** avec Switch components :
  - [ ] 👥 Ouvert aux humains
  - [ ] 🤖 Ouvert aux autres Locrits
  - [ ] 📧 Ouvert aux invitations
  - [ ] 🌐 Ouvert à Internet public
  - [ ] 🏢 Ouvert à la plateforme publique
- [ ] **Paramètres d'accès** avec Checkbox components :
  - [ ] 📋 Accès aux logs
  - [ ] 🧠 Accès mémoire rapide
  - [ ] 🗂️ Accès mémoire complète
  - [ ] 🤖 Accès infos LLM
- [ ] **Actions** avec Button components :
  - [ ] ✅ Bouton créer avec validation
  - [ ] 🔙 Bouton annuler
  - [ ] Gestion des erreurs avec Alert
  - [ ] Sauvegarde via API backend

#### ⚙️ **Écran Paramètres Application**
- [ ] **Configuration Ollama** avec Tabs :
  - [ ] Configuration depuis variables d'environnement
  - [ ] Champ adresse serveur Ollama
  - [ ] Bouton test de connexion avec Loading state
  - [ ] Indicateur de statut avec Badge
  - [ ] Sauvegarde configuration avec Toast feedback
- [ ] **Configuration Tunnel** :
  - [ ] Champ URL publique avec validation
  - [ ] Toggle activer/désactiver tunnel
  - [ ] Statut du tunnel avec indicateur temps réel
- [ ] **Informations & Diagnostics** :
  - [ ] Statut des sauvegardes avec Progress
  - [ ] Bouton voir logs avec Dialog
  - [ ] Bouton diagnostics système
  - [ ] Bouton recharger configuration
- [ ] **Informations système** :
  - [ ] Chemins de fichiers dans Card components
  - [ ] Thème et paramètres UI avec Toggle
- [ ] Navigation avec Breadcrumb

#### 💬 **Écran Chat avec Locrit**
- [ ] Interface de chat temps réel avec WebSocket
- [ ] Historique des conversations avec ScrollArea
- [ ] Informations du Locrit avec Avatar et Badge
- [ ] Zone de saisie avec Textarea et Button
- [ ] Messages avec différentiation visuelle
- [ ] Actions avec Dropdown Menu
- [ ] Indicateur de frappe avec Animation
- [ ] Interface responsive pour mobile
- [ ] Raccourcis clavier pour envoi

#### ℹ️ **Écran À propos**
- [ ] Informations version avec Card layout
- [ ] Statut des services avec Table component
- [ ] Informations de licence dans Accordion
- [ ] Liens utiles avec Button variants
- [ ] Navigation retour

### 📱 **Système de navigation React**
- [ ] React Router pour navigation
- [ ] Navigation par routes protégées
- [ ] Breadcrumb component pour navigation
- [ ] Menu responsive avec Sheet component
- [ ] Raccourcis clavier globaux
- [ ] History management

### 🎨 **Design et UX avec Tailwind/Shadcn**
- [ ] Design system cohérent avec Shadcn/ui
- [ ] Thème sombre/clair avec mode toggle
- [ ] Composants réutilisables
- [ ] Animations fluides avec Framer Motion
- [ ] Design responsive mobile-first
- [ ] Accessibility avec focus management
- [ ] Toast notifications pour feedback
- [ ] Loading states avec Skeleton components

### ⚙️ **Système de configuration React**
- [ ] Context pour configuration globale
- [ ] Hooks personnalisés pour API calls
- [ ] Validation avec Zod schema
- [ ] Gestion d'erreurs centralisée
- [ ] Cache avec React Query
- [ ] Optimistic updates
- [ ] Offline support avec Service Worker

### 🔗 **Intégration API**
- [ ] Client HTTP avec Axios/Fetch
- [ ] WebSocket client pour temps réel
- [ ] Authentication tokens management
- [ ] API error handling
- [ ] Request/response interceptors
- [ ] Retry logic pour resilience
- [ ] Rate limiting handling

## État de développement (Frontend React)

### 📋 À implémenter
- **Architecture React** : Création de l'application de base
- **Composants Shadcn/ui** : Intégration des composants design system
- **Routing** : Configuration React Router avec routes protégées
- **État global** : Context API ou Zustand pour state management
- **API integration** : Client pour communication avec backend
- **Authentication** : Firebase Auth integration
- **WebSocket** : Client temps réel pour communication

### 🔧 Priorités développement
1. **Setup projet** : Create React App/Vite + Tailwind + Shadcn/ui
2. **Authentication flow** : Login/logout avec Firebase
3. **Dashboard principal** : Layout et navigation de base
4. **Chat interface** : Composant de base pour communication
5. **API integration** : Connexion avec backend FastAPI
6. **Responsive design** : Adaptation mobile/desktop
7. **Tests** : Jest + React Testing Library

### 🏗️ Architecture technique React
```
frontend/
├── src/
│   ├── components/        # Composants réutilisables
│   │   ├── ui/           # Shadcn/ui components
│   │   ├── chat/         # Composants chat
│   │   ├── dashboard/    # Composants dashboard
│   │   └── forms/        # Composants formulaires
│   ├── pages/            # Pages principales
│   │   ├── auth/         # Pages authentification
│   │   ├── dashboard/    # Dashboard et sous-pages
│   │   └── chat/         # Interface chat
│   ├── hooks/            # Hooks personnalisés
│   ├── lib/              # Utilitaires et config
│   │   ├── api.ts        # Client API
│   │   ├── auth.ts       # Firebase config
│   │   └── utils.ts      # Utilitaires
│   ├── contexts/         # React contexts
│   └── types/            # Types TypeScript
```

## Technologies clés Frontend

- **React 18** : Framework principal avec Hooks
- **TypeScript** : Typage statique
- **Vite** : Build tool et dev server
- **Tailwind CSS** : Framework CSS utility-first
- **Shadcn/ui** : Composants design system
- **React Router** : Navigation client-side
- **Firebase Auth** : Authentification utilisateur
- **React Query** : Cache et state management server
- **Framer Motion** : Animations fluides
- **Zod** : Validation de schemas
- **WebSocket** : Communication temps réel