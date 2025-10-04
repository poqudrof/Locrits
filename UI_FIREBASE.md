# Guide de Configuration Firebase - Monde des Locrits

Ce document décrit la configuration Firebase complète pour la plateforme de gestion des Locrits, incluant toutes les structures de données, règles de sécurité et configuration d'authentification.

## 📋 Table des Matières

1. [Configuration Initiale](#configuration-initiale)
2. [Structure Firestore](#structure-firestore)
3. [Règles de Sécurité](#règles-de-sécurité)
4. [Configuration Authentication](#configuration-authentication)
5. [Configuration Storage](#configuration-storage)
6. [Exemples d'Utilisation](#exemples-dutilisation)
7. [Migration des Données](#migration-des-données)

## 🚀 Configuration Initiale

### Prérequis
- Compte Firebase actif
- Projet Firebase créé
- SDK Firebase installé dans l'application React

### Variables d'Environnement
Créer un fichier `.env.local` avec vos clés Firebase :

```env
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

## 🗃️ Structure Firestore

### Collections Principales

#### 1. Collection `users`
**Document ID :** UID Firebase Authentication

```typescript
interface User {
  id: string;                    // UID Firebase
  name: string;                  // Nom d'affichage
  email: string;                 // Email de l'utilisateur
  avatar?: string;               // URL de l'avatar (Firebase Storage)
  isOnline: boolean;             // Statut de connexion
  lastSeen: Timestamp;           // Dernière fois vu en ligne
  createdAt: Timestamp;          // Date de création du compte
  updatedAt: Timestamp;          // Dernière mise à jour
}
```

**Exemple de document :**
```json
{
  "id": "user123abc",
  "name": "Alice Martin",
  "email": "alice.martin@email.com",
  "avatar": "https://storage.googleapis.com/project/avatars/user123abc.jpg",
  "isOnline": true,
  "lastSeen": "2024-01-15T10:30:00Z",
  "createdAt": "2024-01-01T08:00:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

#### 2. Collection `locrits`
**Document ID :** Auto-généré par Firestore

```typescript
interface Locrit {
  id: string;                    // ID auto-généré
  name: string;                  // Nom du Locrit
  description: string;           // Description du Locrit
  publicAddress: string;         // Adresse publique unique
  ownerId: string;               // ID du propriétaire (référence users)
  isOnline: boolean;             // Statut de connexion
  lastSeen: Timestamp;           // Dernière activité
  settings: LocritSettings;      // Paramètres d'accès
  createdAt: Timestamp;          // Date de création
  updatedAt: Timestamp;          // Dernière mise à jour
}

interface LocritSettings {
  openTo: {
    humans: boolean;             // Ouvert aux humains
    locrits: boolean;            // Ouvert aux autres Locrits
    invitations: boolean;        // Accepte les invitations
    publicInternet: boolean;     // Accessible via internet public
    publicPlatform: boolean;     // Visible sur la plateforme publique
  };
  accessTo: {
    logs: boolean;               // Accès aux logs
    quickMemory: boolean;        // Accès à la mémoire rapide
    fullMemory: boolean;         // Accès à la mémoire complète
    llmInfo: boolean;            // Accès aux infos LLM
  };
}
```

**Exemple de document :**
```json
{
  "id": "locrit456def",
  "name": "Pixie l'Organisateur",
  "description": "Un Locrit magique qui adore ranger et planifier ! ✨",
  "publicAddress": "pixie.locritland.net",
  "ownerId": "user123abc",
  "isOnline": true,
  "lastSeen": "2024-01-15T10:25:00Z",
  "settings": {
    "openTo": {
      "humans": true,
      "locrits": true,
      "invitations": true,
      "publicInternet": false,
      "publicPlatform": true
    },
    "accessTo": {
      "logs": true,
      "quickMemory": true,
      "fullMemory": false,
      "llmInfo": true
    }
  },
  "createdAt": "2024-01-01T09:00:00Z",
  "updatedAt": "2024-01-15T10:25:00Z"
}
```

#### 3. Collection `conversations`
**Document ID :** Auto-généré par Firestore

```typescript
interface Conversation {
  id: string;                    // ID auto-généré
  title: string;                 // Titre de la conversation
  participants: ConversationParticipant[]; // Liste des participants (pour affichage)
  participantIds: string[];      // Liste des IDs des participants (pour les règles de sécurité)
  type: 'user-locrit' | 'locrit-locrit';   // Type de conversation
  isActive: boolean;             // Conversation active ou archivée
  lastActivity: Timestamp;       // Dernière activité
  createdAt: Timestamp;          // Date de création
  updatedAt: Timestamp;          // Dernière mise à jour
}

interface ConversationParticipant {
  id: string;                    // ID du participant (user ou locrit)
  name: string;                  // Nom d'affichage
  type: 'user' | 'locrit';       // Type de participant
}
```

#### 4. Collection `messages`
**Document ID :** Auto-généré par Firestore

```typescript
interface ChatMessage {
  id: string;                    // ID auto-généré
  locritId?: string;             // ID du Locrit (pour chat direct)
  conversationId?: string;       // ID de la conversation (pour observations)
  content: string;               // Contenu du message
  timestamp: Timestamp;          // Horodatage du message
  sender: 'user' | 'locrit';     // Type d'expéditeur
  senderName: string;            // Nom de l'expéditeur
  senderId: string;              // ID de l'expéditeur
  isRead: boolean;               // Message lu ou non
  metadata?: {                   // Métadonnées optionnelles
    emotion?: string;            // Émotion du Locrit
    context?: string;            // Contexte de la conversation
  };
}
```

#### 5. Collection `locrit_logs`
**Document ID :** Auto-généré par Firestore

```typescript
interface LocritLog {
  id: string;                    // ID auto-généré
  locritId: string;              // ID du Locrit
  timestamp: Timestamp;          // Horodatage du log
  level: 'info' | 'warning' | 'error'; // Niveau de log
  message: string;               // Message du log
  details?: any;                 // Détails supplémentaires
  userId?: string;               // ID de l'utilisateur concerné (optionnel)
}
```

### Sous-collections

#### Messages par Conversation
**Chemin :** `conversations/{conversationId}/messages`
- Utilise la même structure que la collection `messages`
- Permet de requêter facilement les messages d'une conversation spécifique

#### Paramètres Utilisateur
**Chemin :** `users/{userId}/settings`
```typescript
interface UserSettings {
  notifications: {
    newMessage: boolean;
    locritStatusChange: boolean;
    newConversation: boolean;
  };
  privacy: {
    showOnlineStatus: boolean;
    allowInvitations: boolean;
  };
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
  };
}
```

## 🔒 Règles de Sécurité Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Règles pour les utilisateurs
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null; // Lecture publique pour les utilisateurs connectés
    }
    
    // Règles pour les Locrits
    match /locrits/{locritId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        (request.auth.uid == resource.data.ownerId || 
         request.auth.uid == request.resource.data.ownerId);
    }
    
    // Règles pour les conversations
    match /conversations/{conversationId} {
      allow read, write: if request.auth != null && 
        request.auth.uid in resource.data.participantIds;
      
      // Messages dans les conversations
      match /messages/{messageId} {
        allow read, write: if request.auth != null && 
          request.auth.uid in get(/databases/$(database)/documents/conversations/$(conversationId)).data.participantIds;
      }
    }
    
    // Règles pour les messages directs
    match /messages/{messageId} {
      allow read, write: if request.auth != null && 
        (request.auth.uid == resource.data.senderId ||
         request.auth.uid == getLocritOwner(resource.data.locritId));
    }
    
    // Règles pour les logs des Locrits
    match /locrit_logs/{logId} {
      allow read: if request.auth != null && 
        request.auth.uid == getLocritOwner(resource.data.locritId);
      allow write: if request.auth != null; // Les Locrits peuvent écrire leurs logs
    }
    
    // Paramètres utilisateur
    match /users/{userId}/settings/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Fonction helper pour obtenir le propriétaire d'un Locrit
    function getLocritOwner(locritId) {
      return get(/databases/$(database)/documents/locrits/$(locritId)).data.ownerId;
    }
  }
}
```

## 🔐 Configuration Authentication

### Méthodes d'Authentification Recommandées
1. **Email/Mot de passe** - Pour l'inscription traditionnelle
2. **Google OAuth** - Pour une connexion rapide
3. **Anonyme** - Pour tester les fonctionnalités sans compte

### Configuration dans la Console Firebase
```javascript
// Configuration des domaines autorisés
// Ajouter : localhost, votre-domaine.com

// Configuration des templates d'email
// Personnaliser les emails de vérification et de réinitialisation
```

## 📁 Configuration Storage

### Structure des Dossiers
```
storage/
├── avatars/
│   ├── users/
│   │   └── {userId}.{ext}
│   └── locrits/
│       └── {locritId}.{ext}
├── attachments/
│   └── {conversationId}/
│       └── {messageId}/
│           └── {filename}
└── logs/
    └── {locritId}/
        └── {date}/
            └── {logfile}
```

### Règles de Sécurité Storage
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    
    // Avatars utilisateurs
    match /avatars/users/{userId}.{extension} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Avatars Locrits
    match /avatars/locrits/{locritId}.{extension} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        request.auth.uid == getLocritOwner(locritId);
    }
    
    // Pièces jointes
    match /attachments/{conversationId}/{messageId}/{filename} {
      allow read, write: if request.auth != null && 
        isConversationParticipant(conversationId);
    }
    
    // Logs (lecture seule pour les propriétaires)
    match /logs/{locritId}/{allPaths=**} {
      allow read: if request.auth != null && 
        request.auth.uid == getLocritOwner(locritId);
    }
  }
}
```

## 💻 Exemples d'Utilisation

### Initialisation Firebase
```typescript
// firebase.ts
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);
```

### Service pour les Locrits
```typescript
// services/locritService.ts
import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  getDocs, 
  query, 
  where,
  orderBy,
  onSnapshot 
} from 'firebase/firestore';
import { db } from '../firebase';
import { Locrit } from '../types';

export class LocritService {
  private collection = collection(db, 'locrits');

  // Créer un nouveau Locrit
  async createLocrit(locrit: Omit<Locrit, 'id'>): Promise<string> {
    const docRef = await addDoc(this.collection, {
      ...locrit,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    return docRef.id;
  }

  // Récupérer les Locrits d'un utilisateur
  async getUserLocrits(userId: string): Promise<Locrit[]> {
    const q = query(
      this.collection, 
      where('ownerId', '==', userId),
      orderBy('createdAt', 'desc')
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Locrit));
  }

  // Écouter les changements en temps réel
  subscribeToUserLocrits(userId: string, callback: (locrits: Locrit[]) => void) {
    const q = query(
      this.collection, 
      where('ownerId', '==', userId),
      orderBy('createdAt', 'desc')
    );
    
    return onSnapshot(q, (snapshot) => {
      const locrits = snapshot.docs.map(doc => 
        ({ id: doc.id, ...doc.data() } as Locrit)
      );
      callback(locrits);
    });
  }

  // Mettre à jour un Locrit
  async updateLocrit(locritId: string, updates: Partial<Locrit>): Promise<void> {
    const docRef = doc(db, 'locrits', locritId);
    await updateDoc(docRef, {
      ...updates,
      updatedAt: new Date()
    });
  }

  // Supprimer un Locrit
  async deleteLocrit(locritId: string): Promise<void> {
    const docRef = doc(db, 'locrits', locritId);
    await deleteDoc(docRef);
  }
}
```

### Service pour les Messages
```typescript
// services/messageService.ts
import { 
  collection, 
  addDoc, 
  query, 
  where, 
  orderBy, 
  limit,
  onSnapshot 
} from 'firebase/firestore';
import { db } from '../firebase';
import { ChatMessage } from '../types';

export class MessageService {
  private collection = collection(db, 'messages');

  // Envoyer un message
  async sendMessage(message: Omit<ChatMessage, 'id'>): Promise<string> {
    const docRef = await addDoc(this.collection, {
      ...message,
      timestamp: new Date(),
      isRead: false
    });
    return docRef.id;
  }

  // Écouter les messages d'un Locrit
  subscribeToLocritMessages(locritId: string, callback: (messages: ChatMessage[]) => void) {
    const q = query(
      this.collection,
      where('locritId', '==', locritId),
      orderBy('timestamp', 'asc'),
      limit(100)
    );

    return onSnapshot(q, (snapshot) => {
      const messages = snapshot.docs.map(doc => 
        ({ id: doc.id, ...doc.data() } as ChatMessage)
      );
      callback(messages);
    });
  }

  // Écouter les messages d'une conversation
  subscribeToConversationMessages(conversationId: string, callback: (messages: ChatMessage[]) => void) {
    const q = query(
      this.collection,
      where('conversationId', '==', conversationId),
      orderBy('timestamp', 'asc'),
      limit(100)
    );

    return onSnapshot(q, (snapshot) => {
      const messages = snapshot.docs.map(doc => 
        ({ id: doc.id, ...doc.data() } as ChatMessage)
      );
      callback(messages);
    });
  }
}
```

## 🔄 Migration des Données

### Script de Migration depuis les Données Mock
```typescript
// scripts/migrateData.ts
import { collection, addDoc, writeBatch, doc } from 'firebase/firestore';
import { db } from '../firebase';
import { mockUsers, mockLocrits, mockMessages, mockConversations } from '../data/mockData';

export async function migrateMockData() {
  const batch = writeBatch(db);

  try {
    // Migrer les utilisateurs
    console.log('Migration des utilisateurs...');
    for (const user of mockUsers) {
      const userRef = doc(db, 'users', user.id);
      batch.set(userRef, {
        ...user,
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }

    // Migrer les Locrits
    console.log('Migration des Locrits...');
    for (const locrit of mockLocrits) {
      const locritRef = doc(collection(db, 'locrits'));
      batch.set(locritRef, {
        ...locrit,
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }

    // Valider la batch
    await batch.commit();
    console.log('Migration terminée avec succès !');

    // Migrer les messages et conversations séparément
    await migrateMessagesAndConversations();

  } catch (error) {
    console.error('Erreur lors de la migration :', error);
  }
}

async function migrateMessagesAndConversations() {
  // Migration des conversations
  for (const conversation of mockConversations) {
    await addDoc(collection(db, 'conversations'), {
      ...conversation,
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  // Migration des messages
  for (const message of mockMessages) {
    await addDoc(collection(db, 'messages'), message);
  }
}
```

## 📊 Index Firestore Recommandés

### Index Composés à Créer
```javascript
// Dans la console Firebase -> Firestore -> Index
// 1. Messages par Locrit et timestamp
{
  collection: "messages",
  fields: [
    { field: "locritId", order: "ASCENDING" },
    { field: "timestamp", order: "ASCENDING" }
  ]
}

// 2. Messages par conversation et timestamp
{
  collection: "messages", 
  fields: [
    { field: "conversationId", order: "ASCENDING" },
    { field: "timestamp", order: "ASCENDING" }
  ]
}

// 3. Locrits par propriétaire et date de création
{
  collection: "locrits",
  fields: [
    { field: "ownerId", order: "ASCENDING" },
    { field: "createdAt", order: "DESCENDING" }
  ]
}

// 4. Conversations par participant et activité
{
  collection: "conversations",
  fields: [
    { field: "participants.id", order: "ASCENDING" },
    { field: "lastActivity", order: "DESCENDING" }
  ]
}
```

## 🚀 Prochaines Étapes

1. **Créer le projet Firebase** et activer les services nécessaires
2. **Configurer l'authentification** avec les méthodes choisies
3. **Créer les règles de sécurité** pour Firestore et Storage
4. **Implémenter les services** dans l'application React
5. **Tester la migration** des données mock vers Firebase
6. **Configurer les index** pour optimiser les performances
7. **Déployer** et monitorer l'application

## 📝 Notes Importantes

- **Sécurité** : Toujours valider les données côté client ET serveur
- **Performance** : Utiliser la pagination pour les grandes collections
- **Coût** : Surveiller l'utilisation pour éviter les frais inattendus
- **Backup** : Configurer des sauvegardes automatiques
- **Monitoring** : Utiliser Firebase Analytics pour surveiller l'usage

---

*Cette configuration Firebase est optimisée pour la plateforme Monde des Locrits et respecte les meilleures pratiques de sécurité et de performance.*