# Authentification Firebase dans Locrit

L'authentification Firebase a été intégrée dans Locrit pour permettre aux utilisateurs de se connecter soit de manière anonyme, soit avec un compte email/mot de passe.

## 🔧 Configuration

### 1. Variables d'environnement
Dans votre fichier `.env`, vous pouvez configurer :

```env
# Authentification automatique (true/false)
LOCRIT_AUTO_AUTH=false

# Si true : connexion anonyme automatique au démarrage
# Si false : affichage de l'écran d'authentification
```

### 2. Configuration Firebase
Assurez-vous que votre fichier `.env` contient les clés Firebase nécessaires :

```env
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
# etc.
```

## 🎯 Fonctionnalités

### Mode Automatique (`LOCRIT_AUTO_AUTH=true`)
- Connexion anonyme automatique au démarrage
- Aucune interaction utilisateur requise
- Idéal pour les tests et le développement

### Mode Interactif (`LOCRIT_AUTO_AUTH=false`)
- Écran d'authentification au démarrage
- Choix entre connexion anonyme et compte email
- Interface utilisateur intuitive

## 🎨 Interface d'Authentification

L'écran d'authentification propose :

### Connexion Rapide
- **🎭 Se connecter en anonyme** : Connexion immédiate sans compte

### Connexion avec Compte
- **Champs de saisie** : Email et mot de passe
- **🔑 Se connecter** : Connexion avec compte existant
- **📝 Créer un compte** : Création d'un nouveau compte
- **🔄 Mot de passe oublié** : Réinitialisation par email

### Gestion des Erreurs
- Messages d'erreur clairs en français
- Validation des champs de saisie
- Feedback visuel avec couleurs

## 🔐 Bouton Auth dans l'Interface Principale

Un nouveau bouton **🔐 Auth** a été ajouté dans l'interface principale :

- **Si connecté** : Affiche les informations de l'utilisateur actuel
- **Si déconnecté** : Ouvre l'écran d'authentification

## 🧩 Architecture

### Services Créés

1. **`AuthService`** (`src/services/auth_service.py`)
   - Gère l'authentification Firebase
   - Connexion anonyme et email/mot de passe
   - Gestion des erreurs et tokens

2. **`AuthScreen`** (`src/ui/auth_screen.py`)
   - Interface pour l'authentification
   - Gestion des interactions utilisateur
   - Validation des formulaires

### Intégration

- **`LocritManager`** : Stocke les informations d'authentification
- **`LocritApp`** : Gère les écrans et l'état de connexion
- **Flux automatisé** : De l'auth à l'initialisation des services

## 📊 États de l'Application

```
Démarrage
    ↓
LOCRIT_AUTO_AUTH?
    ↓              ↓
   true           false
    ↓              ↓
Auth Anonyme   Écran Auth
    ↓              ↓
Succès?        Connexion?
    ↓              ↓
   Oui            Oui
    ↓              ↓
Initialisation Locrit
    ↓
Interface Principale
```

## 🛠️ Utilisation

### Pour l'utilisateur final

1. **Première utilisation** :
   - Lancer Locrit
   - Choisir le mode de connexion
   - Créer un compte si souhaité

2. **Utilisation quotidienne** :
   - Configurer `LOCRIT_AUTO_AUTH=true` pour un accès rapide
   - Ou garder `false` pour choisir le compte à chaque fois

### Pour le développeur

1. **Mode développement** :
   ```env
   LOCRIT_AUTO_AUTH=true
   ```

2. **Mode démonstration** :
   ```env
   LOCRIT_AUTO_AUTH=false
   ```

## 🔒 Sécurité

- **Tokens gérés automatiquement** : Refresh automatique
- **Erreurs sécurisées** : Messages d'erreur sans divulgation
- **Isolation utilisateur** : Chaque utilisateur ses données
- **Déconnexion propre** : Nettoyage des tokens

## 🧪 Tests

Pour tester l'authentification :

```bash
# Test du service d'authentification
python test_auth_ui.py

# Choix 1: Test du service (sans interface)
# Choix 2: Test de l'interface complète
```

## 🚀 Démarrage Rapide

1. **Configuration minimale** :
   ```bash
   cp .env.example .env
   # Éditer .env avec vos clés Firebase
   ```

2. **Lancement** :
   ```bash
   python main.py
   ```

3. **Première connexion** :
   - Choisir "Se connecter en anonyme" pour commencer rapidement
   - Ou créer un compte pour personnaliser l'expérience

## 🎭 Expérience Utilisateur

### Connexion Anonyme
- **Avantages** : Accès immédiat, aucune configuration
- **Limitations** : Données non sauvegardées entre sessions

### Connexion Email
- **Avantages** : Persistance des données, personnalisation
- **Prérequis** : Compte Firebase, validation email

L'authentification Firebase transforme Locrit d'un outil local en une plateforme connectée où chaque utilisateur peut avoir sa propre expérience personnalisée tout en gardant la possibilité d'un accès anonyme rapide.
