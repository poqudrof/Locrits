# Configuration Firebase - Guide Rapide 🚀

Ce guide vous permet de configurer rapidement Firebase pour l'application Monde des Locrits.

## ⚡ Configuration Express (5 minutes)

### 1. Console Firebase
1. Allez sur [console.firebase.google.com](https://console.firebase.google.com)
2. Créez un nouveau projet ou sélectionnez le projet `locrit`
3. Activez les services suivants :

#### Authentication
- Allez dans **Authentication > Sign-in method**
- Activez **Email/Password**
- Activez **Anonymous** (pour les tests)
- Activez **Google** :
  - Saisissez votre email de support du projet
  - Le nom public du projet sera affiché aux utilisateurs

#### Firestore Database
- Allez dans **Firestore Database**
- Cliquez **Create database**
- Mode : **Start in test mode** (pour commencer)
- Région : **europe-west1** (ou proche de vous)

### 2. Règles de Sécurité

#### Firestore Rules
Dans **Firestore Database > Rules**, remplacez le contenu par :

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

**⚠️ IMPORTANT : Ces règles sont permissives et à usage de développement uniquement !**

### 3. Index Firestore (Requis)

Dans **Firestore Database > Indexes**, créez ces index composés :

#### Index 1 : Messages par Locrit
```
Collection: messages
Fields: 
- locritId (Ascending)
- timestamp (Ascending)
```

#### Index 2 : Messages par Conversation
```
Collection: messages
Fields:
- conversationId (Ascending) 
- timestamp (Ascending)
```

#### Index 3 : Locrits par Propriétaire
```
Collection: locrits
Fields:
- ownerId (Ascending)
- createdAt (Descending)
```

### 4. Test de Configuration

1. **Dans l'application** :
   - Testez la connexion anonyme 
   - Testez la connexion Google SSO
   - Testez la connexion par email/mot de passe
   - Allez dans l'onglet **"Diagnostic"** 
   - Cliquez **"Lancer le diagnostic"**
   - Si tout est vert ✅, c'est bon !

2. **Si erreurs** :
   - Cliquez **"Migrer les données mockup"** pour initialiser
   - Vérifiez les règles de sécurité Firestore
   - Vérifiez que l'authentification est activée

## 🔧 Dépannage Rapide

### Erreur : "Missing or insufficient permissions"
- **Solution** : Vérifiez les règles Firestore ci-dessus
- Assurez-vous d'être connecté dans l'app

### Erreur : "The query requires an index"
- **Solution** : Créez les index composés listés ci-dessus
- Attendez 2-3 minutes après création des index

### Erreur de connexion Firebase
- **Solution** : Vérifiez la configuration dans `/firebase/config.ts`
- Assurez-vous que le projet ID correspond

### Toggle "Firebase" ne fonctionne pas
- **Solution** : D'abord migrer les données avec le bouton dans "Diagnostic"
- Vérifiez la console navigateur pour les erreurs

## 📊 Structure des Données

Après migration, vous aurez ces collections :
- `users` - Utilisateurs de la plateforme
- `locrits` - Les Locrits créés  
- `messages` - Messages entre utilisateurs et Locrits
- `conversations` - Conversations entre Locrits

## 🚀 Prochaines Étapes

1. **Tester** l'application avec le toggle Firebase activé
2. **Créer** de nouveaux Locrits depuis l'interface
3. **Envoyer** des messages et tester les fonctionnalités
4. **Durcir** les règles de sécurité pour la production

## 📞 Support

Si vous rencontrez des problèmes :
1. Utilisez l'onglet **"Diagnostic"** pour identifier les erreurs
2. Vérifiez la console navigateur (F12)
3. Consultez la console Firebase pour les erreurs backend

---

*Configuration testée avec Firebase SDK v9+ et React 18*