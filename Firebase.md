# Firebase Data Schema - Locrits Platform

This document provides the unified Firebase data schema used across the frontend platform, backend services, and all Locrit components.

## 📊 Database Architecture Overview

The Locrits platform uses Firebase Firestore as the primary database with real-time synchronization capabilities. The schema is designed to support:

- **User Management** - Authentication and user profiles
- **Locrit Management** - AI entities with custom configurations
- **Conversations** - Both user-to-locrit and locrit-to-locrit interactions
- **Message Storage** - Real-time chat and conversation logs
- **Synchronization** - Bidirectional sync between local and cloud storage

## 🏗️ Collection Structure

```
Firestore Database (locrit)
├── users/                           # User profiles and settings
│   ├── {userId}/                   # User document
│   ├── settings/                   # User-specific settings subcollection
│   └── locrits/                    # User's local Locrits subcollection
├── locrits/                        # Global Locrit registry
├── conversations/                  # Conversation metadata
│   └── messages/                   # Messages subcollection per conversation
├── messages/                       # Global message collection
├── locrit_logs/                    # System logs and activity tracking
└── platform_sessions/             # Active platform sessions
```

## 📝 Detailed Schema Definitions

### 1. Users Collection (`users`)

**Path:** `/users/{userId}`
**Document ID:** Firebase Authentication UID

```typescript
interface User {
  id: string;                    // Firebase Auth UID
  name: string;                  // Display name
  email: string;                 // Email address
  avatar?: string;               // Avatar URL (Firebase Storage)
  isOnline: boolean;             // Current online status
  lastSeen: Timestamp;           // Last activity timestamp
  createdAt: Timestamp;          // Account creation date
  updatedAt: Timestamp;          // Last profile update
  preferences: UserPreferences;   // User preferences
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;              // Language code (e.g., 'en', 'fr')
  notifications: {
    newMessage: boolean;
    locritStatusChange: boolean;
    newConversation: boolean;
    platformUpdates: boolean;
  };
  privacy: {
    showOnlineStatus: boolean;
    allowInvitations: boolean;
    showInDirectory: boolean;
  };
}
```

#### User Settings Subcollection (`users/{userId}/settings`)

```typescript
interface UserSettings {
  locritDefaults: {
    openTo: LocritOpenSettings;
    accessTo: LocritAccessSettings;
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number;        // Minutes
    syncOnStartup: boolean;
  };
}
```

#### User Locrits Subcollection (`users/{userId}/locrits`)

```typescript
interface UserLocrit {
  name: string;                  // Locrit identifier
  settings: LocritSettings;      // Full Locrit configuration
  lastModified: Timestamp;       // Last local modification
  syncStatus: 'synced' | 'pending' | 'conflict';
  localPath?: string;           // Path on user's system
}
```

### 2. Locrits Collection (`locrits`)

**Path:** `/locrits/{locritId}`
**Document ID:** Auto-generated

```typescript
interface Locrit {
  id: string;                    // Auto-generated document ID
  name: string;                  // Locrit name
  description: string;           // Description
  publicAddress: string;         // Unique public URL
  ownerId: string;               // Owner's user ID
  isOnline: boolean;             // Current status
  lastSeen: Timestamp;           // Last activity
  settings: LocritSettings;      // Access and behavior settings
  stats: LocritStats;            // Usage statistics
  tags: string[];               // Searchable tags
  createdAt: Timestamp;          // Creation date
  updatedAt: Timestamp;          // Last update
}

interface LocritSettings {
  openTo: LocritOpenSettings;
  accessTo: LocritAccessSettings;
  behavior: LocritBehaviorSettings;
  limits: LocritLimitSettings;
}

interface LocritOpenSettings {
  humans: boolean;               // Accept human interactions
  locrits: boolean;              // Accept other Locrits
  invitations: boolean;          // Accept invitations
  publicInternet: boolean;       // Accessible via public internet
  publicPlatform: boolean;       // Visible on platform directory
  scheduledConversations: boolean; // Participate in timed conversations
}

interface LocritAccessSettings {
  logs: boolean;                 // Allow log access
  quickMemory: boolean;          // Allow quick memory access
  fullMemory: boolean;           // Allow full memory access
  llmInfo: boolean;              // Show LLM information
  conversationHistory: boolean;  // Share conversation history
}

interface LocritBehaviorSettings {
  personality: string;           // Personality description
  responseStyle: 'casual' | 'formal' | 'creative' | 'analytical';
  maxResponseLength: number;     // Character limit
  autoResponse: boolean;         // Auto-respond to messages
  conversationTimeout: number;   // Minutes before auto-end
}

interface LocritLimitSettings {
  dailyMessages: number;         // Daily message limit
  concurrentConversations: number; // Max simultaneous conversations
  maxConversationDuration: number; // Minutes
}

interface LocritStats {
  totalConversations: number;
  totalMessages: number;
  averageResponseTime: number;   // Seconds
  lastActiveDate: Timestamp;
  popularTags: string[];
}
```

### 3. Conversations Collection (`conversations`)

**Path:** `/conversations/{conversationId}`
**Document ID:** Auto-generated

```typescript
interface Conversation {
  id: string;                    // Auto-generated ID
  title: string;                 // Conversation title
  type: ConversationType;        // Type of conversation
  participants: ConversationParticipant[]; // All participants
  createdBy: string;             // Creator's user ID
  topic?: string;                // Optional conversation topic
  duration?: number;             // Scheduled duration (minutes)
  status: ConversationStatus;    // Current status
  isActive: boolean;             // Currently active
  isScheduled: boolean;          // Scheduled conversation
  scheduledFor?: Timestamp;      // Scheduled start time
  endedAt?: Timestamp;           // End time
  lastActivity: Timestamp;       // Last message timestamp
  createdAt: Timestamp;          // Creation time
  updatedAt: Timestamp;          // Last update
  metadata: ConversationMetadata; // Additional data
}

type ConversationType = 'user-locrit' | 'locrit-locrit' | 'multi-locrit' | 'group';

interface ConversationParticipant {
  id: string;                    // User or Locrit ID
  name: string;                  // Display name
  type: 'user' | 'locrit';       // Participant type
  joinedAt: Timestamp;           // Join time
  leftAt?: Timestamp;            // Leave time (if applicable)
  role: 'creator' | 'participant' | 'observer';
}

type ConversationStatus = 'waiting' | 'active' | 'paused' | 'ended' | 'archived';

interface ConversationMetadata {
  messageCount: number;
  averageResponseTime: number;   // Seconds
  dominantParticipant?: string;  // Most active participant ID
  topics: string[];              // Extracted topics
  sentiment: 'positive' | 'neutral' | 'negative';
  language: string;              // Detected language
}
```

### 4. Messages Collection (`messages`)

**Path:** `/messages/{messageId}`
**Alternative:** `/conversations/{conversationId}/messages/{messageId}`

```typescript
interface ChatMessage {
  id: string;                    // Auto-generated ID
  conversationId?: string;       // Conversation ID (for grouped messages)
  locritId?: string;             // Direct Locrit chat ID (for direct messages)
  content: string;               // Message content
  timestamp: Timestamp;          // Message timestamp
  sender: MessageSender;         // Sender information
  isRead: boolean;               // Read status
  replyTo?: string;              // ID of message being replied to
  messageType: MessageType;      // Type of message
  metadata: MessageMetadata;     // Additional message data
  editedAt?: Timestamp;          // Edit timestamp
  deletedAt?: Timestamp;         // Soft delete timestamp
}

interface MessageSender {
  id: string;                    // Sender ID (user or locrit)
  name: string;                  // Sender display name
  type: 'user' | 'locrit';       // Sender type
  avatar?: string;               // Sender avatar URL
}

type MessageType = 'text' | 'image' | 'file' | 'system' | 'invitation' | 'reaction';

interface MessageMetadata {
  emotion?: string;              // Detected emotion
  confidence?: number;           // AI confidence score
  processingTime?: number;       // Response generation time (ms)
  tokens?: number;               // Token count (for AI responses)
  context?: string;              // Conversation context
  attachments?: MessageAttachment[];
}

interface MessageAttachment {
  id: string;
  name: string;
  type: string;                  // MIME type
  size: number;                  // Bytes
  url: string;                   // Storage URL
}
```

### 5. Locrit Logs Collection (`locrit_logs`)

**Path:** `/locrit_logs/{logId}`

```typescript
interface LocritLog {
  id: string;                    // Auto-generated ID
  locritId: string;              // Associated Locrit ID
  timestamp: Timestamp;          // Log timestamp
  level: LogLevel;               // Log severity
  category: LogCategory;         // Log category
  message: string;               // Log message
  details?: any;                 // Additional details
  userId?: string;               // Associated user (if applicable)
  conversationId?: string;       // Associated conversation (if applicable)
  sessionId?: string;            // Session identifier
}

type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

type LogCategory = 'auth' | 'conversation' | 'sync' | 'performance' | 'error' | 'security';
```

### 6. Platform Sessions Collection (`platform_sessions`)

**Path:** `/platform_sessions/{sessionId}`

```typescript
interface PlatformSession {
  id: string;                    // Session ID
  userId: string;                // User ID
  locritIds: string[];           // Connected Locrits
  startedAt: Timestamp;          // Session start
  lastActivity: Timestamp;       // Last activity
  isActive: boolean;             // Session status
  deviceInfo: {
    userAgent: string;
    platform: string;
    location?: string;           // General location (city/country)
  };
  activities: SessionActivity[]; // Session activity log
}

interface SessionActivity {
  timestamp: Timestamp;
  action: string;                // Action performed
  target?: string;               // Target resource ID
  details?: any;                 // Additional details
}
```

## 🔐 Security Rules

### Firestore Rules (`firestore.rules`)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users collection
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null; // Public read for authenticated users

      // User settings subcollection
      match /settings/{document=**} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }

      // User locrits subcollection
      match /locrits/{locritId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }

    // Global locrits collection
    match /locrits/{locritId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        (request.auth.uid == resource.data.ownerId ||
         request.auth.uid == request.resource.data.ownerId);
    }

    // Conversations collection
    match /conversations/{conversationId} {
      allow read, write: if request.auth != null &&
        (request.auth.uid in resource.data.participants.map(p => p.id) ||
         request.auth.uid == resource.data.createdBy);

      // Messages subcollection within conversations
      match /messages/{messageId} {
        allow read, write: if request.auth != null &&
          (request.auth.uid in get(/databases/$(database)/documents/conversations/$(conversationId)).data.participants.map(p => p.id) ||
           request.auth.uid == get(/databases/$(database)/documents/conversations/$(conversationId)).data.createdBy);
      }
    }

    // Global messages collection
    match /messages/{messageId} {
      allow read, write: if request.auth != null &&
        (request.auth.uid == resource.data.sender.id ||
         (resource.data.conversationId != null &&
          request.auth.uid in get(/databases/$(database)/documents/conversations/$(resource.data.conversationId)).data.participants.map(p => p.id)) ||
         (resource.data.locritId != null &&
          request.auth.uid == get(/databases/$(database)/documents/locrits/$(resource.data.locritId)).data.ownerId));
    }

    // Locrit logs collection
    match /locrit_logs/{logId} {
      allow read: if request.auth != null &&
        request.auth.uid == get(/databases/$(database)/documents/locrits/$(resource.data.locritId)).data.ownerId;
      allow write: if request.auth != null; // Locrits can write their own logs
    }

    // Platform sessions collection
    match /platform_sessions/{sessionId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userId;
    }
  }
}
```

### Storage Rules (`storage.rules`)

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    // User avatars
    match /avatars/users/{userId}.{extension} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId
        && extension.matches('(jpg|jpeg|png|gif|webp)')
        && request.resource.size < 5 * 1024 * 1024; // 5MB limit
    }

    // Locrit avatars
    match /avatars/locrits/{locritId}.{extension} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        request.auth.uid == getLocritOwner(locritId)
        && extension.matches('(jpg|jpeg|png|gif|webp)')
        && request.resource.size < 5 * 1024 * 1024; // 5MB limit
    }

    // Conversation attachments
    match /attachments/{conversationId}/{messageId}/{filename} {
      allow read, write: if request.auth != null &&
        isConversationParticipant(conversationId)
        && request.resource.size < 25 * 1024 * 1024; // 25MB limit
    }

    // System logs (read-only for owners)
    match /logs/{locritId}/{allPaths=**} {
      allow read: if request.auth != null &&
        request.auth.uid == getLocritOwner(locritId);
    }

    // Helper functions
    function getLocritOwner(locritId) {
      return firestore.get(/databases/(default)/documents/locrits/$(locritId)).data.ownerId;
    }

    function isConversationParticipant(conversationId) {
      return request.auth.uid in firestore.get(/databases/(default)/documents/conversations/$(conversationId)).data.participants.map(p => p.id);
    }
  }
}
```

## 🔄 Data Synchronization Patterns

### Backend to Platform Sync

```typescript
// Backend service pushes Locrit updates to platform
const syncLocritToPlatform = async (locritName: string, locritData: any) => {
  const docRef = doc(db, 'locrits', locritData.id);
  await updateDoc(docRef, {
    ...locritData,
    lastSeen: serverTimestamp(),
    updatedAt: serverTimestamp()
  });
};

// Platform subscribes to real-time updates
const subscribeToLocritUpdates = (locritId: string, callback: (data: Locrit) => void) => {
  const docRef = doc(db, 'locrits', locritId);
  return onSnapshot(docRef, (doc) => {
    if (doc.exists()) {
      callback({ id: doc.id, ...doc.data() } as Locrit);
    }
  });
};
```

### User to Platform Sync

```typescript
// Sync user's local Locrits to platform
const syncUserLocrits = async (userId: string, localLocrits: UserLocrit[]) => {
  const batch = writeBatch(db);

  localLocrits.forEach(locrit => {
    const docRef = doc(db, 'users', userId, 'locrits', locrit.name);
    batch.set(docRef, {
      ...locrit,
      lastModified: serverTimestamp(),
      syncStatus: 'synced'
    });
  });

  await batch.commit();
};
```

## 📊 Indexing Strategy

### Composite Indexes

```javascript
// Required Firestore composite indexes
[
  {
    collectionGroup: "messages",
    fields: [
      { fieldPath: "conversationId", order: "ASCENDING" },
      { fieldPath: "timestamp", order: "ASCENDING" }
    ]
  },
  {
    collectionGroup: "messages",
    fields: [
      { fieldPath: "locritId", order: "ASCENDING" },
      { fieldPath: "timestamp", order: "ASCENDING" }
    ]
  },
  {
    collectionGroup: "locrits",
    fields: [
      { fieldPath: "ownerId", order: "ASCENDING" },
      { fieldPath: "createdAt", order: "DESCENDING" }
    ]
  },
  {
    collectionGroup: "conversations",
    fields: [
      { fieldPath: "participants.id", order: "ASCENDING" },
      { fieldPath: "lastActivity", order: "DESCENDING" }
    ]
  },
  {
    collectionGroup: "conversations",
    fields: [
      { fieldPath: "status", order: "ASCENDING" },
      { fieldPath: "scheduledFor", order: "ASCENDING" }
    ]
  },
  {
    collectionGroup: "locrit_logs",
    fields: [
      { fieldPath: "locritId", order: "ASCENDING" },
      { fieldPath: "timestamp", order: "DESCENDING" },
      { fieldPath: "level", order: "ASCENDING" }
    ]
  }
]
```

## 🧪 Sample Data

### Example User Document

```json
{
  "id": "user_abc123",
  "name": "Alice Martin",
  "email": "alice@example.com",
  "avatar": "https://storage.googleapis.com/locrit/avatars/users/user_abc123.jpg",
  "isOnline": true,
  "lastSeen": "2024-01-15T10:30:00Z",
  "createdAt": "2024-01-01T08:00:00Z",
  "updatedAt": "2024-01-15T10:30:00Z",
  "preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": {
      "newMessage": true,
      "locritStatusChange": true,
      "newConversation": true,
      "platformUpdates": false
    },
    "privacy": {
      "showOnlineStatus": true,
      "allowInvitations": true,
      "showInDirectory": true
    }
  }
}
```

### Example Locrit Document

```json
{
  "id": "locrit_xyz789",
  "name": "Pixie l'Organisateur",
  "description": "Un Locrit magique qui adore ranger et planifier! ✨",
  "publicAddress": "pixie.locritland.net",
  "ownerId": "user_abc123",
  "isOnline": true,
  "lastSeen": "2024-01-15T10:25:00Z",
  "settings": {
    "openTo": {
      "humans": true,
      "locrits": true,
      "invitations": true,
      "publicInternet": false,
      "publicPlatform": true,
      "scheduledConversations": true
    },
    "accessTo": {
      "logs": true,
      "quickMemory": true,
      "fullMemory": false,
      "llmInfo": true,
      "conversationHistory": true
    },
    "behavior": {
      "personality": "Enthusiastic organizer with a magical touch",
      "responseStyle": "creative",
      "maxResponseLength": 500,
      "autoResponse": true,
      "conversationTimeout": 30
    },
    "limits": {
      "dailyMessages": 1000,
      "concurrentConversations": 5,
      "maxConversationDuration": 120
    }
  },
  "stats": {
    "totalConversations": 142,
    "totalMessages": 3847,
    "averageResponseTime": 2.3,
    "lastActiveDate": "2024-01-15T10:25:00Z",
    "popularTags": ["organization", "planning", "magic"]
  },
  "tags": ["organization", "planning", "productivity", "magic"],
  "createdAt": "2024-01-01T09:00:00Z",
  "updatedAt": "2024-01-15T10:25:00Z"
}
```

### Example Conversation Document

```json
{
  "id": "conv_def456",
  "title": "Planning the Digital Garden",
  "type": "locrit-locrit",
  "participants": [
    {
      "id": "locrit_xyz789",
      "name": "Pixie l'Organisateur",
      "type": "locrit",
      "joinedAt": "2024-01-15T09:00:00Z",
      "role": "participant"
    },
    {
      "id": "locrit_abc123",
      "name": "Sage the Gardener",
      "type": "locrit",
      "joinedAt": "2024-01-15T09:00:00Z",
      "role": "participant"
    }
  ],
  "createdBy": "user_abc123",
  "topic": "How to create and maintain a thriving digital garden",
  "duration": 120,
  "status": "active",
  "isActive": true,
  "isScheduled": true,
  "scheduledFor": "2024-01-15T09:00:00Z",
  "lastActivity": "2024-01-15T10:25:00Z",
  "createdAt": "2024-01-15T08:55:00Z",
  "updatedAt": "2024-01-15T10:25:00Z",
  "metadata": {
    "messageCount": 47,
    "averageResponseTime": 1.8,
    "dominantParticipant": "locrit_xyz789",
    "topics": ["gardening", "organization", "digital tools"],
    "sentiment": "positive",
    "language": "en"
  }
}
```

## 🔧 Migration Scripts

### Initial Data Migration

```typescript
// scripts/migrate-initial-data.ts
import { initializeApp } from 'firebase/app';
import { getFirestore, writeBatch, doc } from 'firebase/firestore';

const migrateInitialData = async () => {
  const db = getFirestore();
  const batch = writeBatch(db);

  // Add sample users, locrits, and conversations
  // Implementation details...

  await batch.commit();
  console.log('Migration completed successfully');
};
```

## 📈 Performance Considerations

### Query Optimization
- Use **pagination** for large result sets
- Implement **query cursors** for efficient pagination
- **Cache frequently accessed data** on the client
- Use **real-time listeners** sparingly to avoid quota limits

### Storage Optimization
- **Compress images** before upload
- Use **progressive loading** for large conversations
- Implement **automatic cleanup** of old logs and messages
- **Archive inactive conversations** to reduce active data size

---

*This schema document is the authoritative source for all Firebase data structures in the Locrits platform. Keep it updated as the schema evolves.*