import {
  collection,
  doc,
  addDoc,
  updateDoc,
  deleteDoc,
  getDocs,
  getDoc,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  serverTimestamp,
  Timestamp
} from "firebase/firestore";
import { db } from "./config";
import { Locrit, ChatMessage, Conversation, User } from "../types";

// ============================================================================
// SERVICE UTILISATEURS
// ============================================================================

export class UserService {
  private collection = collection(db, 'users');

  // Récupérer tous les utilisateurs
  async getUsers(): Promise<User[]> {
    try {
      const snapshot = await getDocs(this.collection);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          lastSeen: data.lastSeen?.toDate() || new Date()
        } as User;
      });
    } catch (error) {
      console.error('Erreur lors de la récupération des utilisateurs:', error);
      throw error;
    }
  }

  // Récupérer un utilisateur par ID
  async getUser(userId: string): Promise<User | null> {
    try {
      const docRef = doc(db, 'users', userId);
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        const data = docSnap.data();
        return {
          id: docSnap.id,
          ...data,
          lastSeen: data.lastSeen?.toDate() || new Date()
        } as User;
      }
      return null;
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'utilisateur:', error);
      throw error;
    }
  }

  // Écouter les changements d'utilisateurs en temps réel
  subscribeToUsers(callback: (users: User[]) => void): () => void {
    const q = query(this.collection, orderBy('name', 'asc'));
    
    return onSnapshot(q, (snapshot) => {
      const users = snapshot.docs.map(doc => ({
        ...doc.data(),
        lastSeen: doc.data().lastSeen?.toDate() || new Date()
      } as User));
      callback(users);
    });
  }
}

// ============================================================================
// SERVICE LOCRITS
// ============================================================================

export class LocritService {
  private collection = collection(db, 'locrits');

  // Créer un nouveau Locrit
  async createLocrit(locrit: Omit<Locrit, 'id'>): Promise<string> {
    try {
      const docRef = await addDoc(this.collection, {
        ...locrit,
        lastSeen: new Date(locrit.lastSeen),
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
      return docRef.id;
    } catch (error) {
      console.error('Erreur lors de la création du Locrit:', error);
      throw error;
    }
  }

  // Récupérer tous les Locrits
  async getLocrits(): Promise<Locrit[]> {
    try {
      const snapshot = await getDocs(this.collection);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          lastSeen: data.lastSeen?.toDate() || new Date()
        } as Locrit;
      });
    } catch (error) {
      console.error('Erreur lors de la récupération des Locrits:', error);
      throw error;
    }
  }

  // Récupérer les Locrits d'un utilisateur
  async getUserLocrits(userId: string): Promise<Locrit[]> {
    try {
      const q = query(
        this.collection,
        where('ownerId', '==', userId),
        orderBy('createdAt', 'desc')
      );
      const snapshot = await getDocs(q);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          lastSeen: data.lastSeen?.toDate() || new Date()
        } as Locrit;
      });
    } catch (error) {
      console.error('Erreur lors de la récupération des Locrits utilisateur:', error);
      throw error;
    }
  }

  // Écouter les changements de Locrits d'un utilisateur en temps réel
  subscribeToUserLocrits(userId: string, callback: (locrits: Locrit[]) => void): () => void {
    const q = query(
      this.collection,
      where('ownerId', '==', userId),
      orderBy('createdAt', 'desc')
    );

    return onSnapshot(q, (snapshot) => {
      const locrits = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        lastSeen: doc.data().lastSeen?.toDate() || new Date()
      } as Locrit));
      callback(locrits);
    });
  }

  // Écouter tous les Locrits en temps réel
  subscribeToAllLocrits(callback: (locrits: Locrit[]) => void): () => void {
    const q = query(this.collection, orderBy('createdAt', 'desc'));

    return onSnapshot(q, (snapshot) => {
      const locrits = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        lastSeen: doc.data().lastSeen?.toDate() || new Date()
      } as Locrit));
      callback(locrits);
    });
  }

  // Mettre à jour un Locrit
  async updateLocrit(locritId: string, updates: Partial<Locrit>): Promise<void> {
    const docRef = doc(db, 'locrits', locritId);
    await updateDoc(docRef, {
      ...updates,
      updatedAt: serverTimestamp()
    });
  }

  // Supprimer un Locrit
  async deleteLocrit(locritId: string): Promise<void> {
    const docRef = doc(db, 'locrits', locritId);
    await deleteDoc(docRef);
  }
}

// ============================================================================
// SERVICE MESSAGES
// ============================================================================

export class MessageService {
  private collection = collection(db, 'messages');

  // Envoyer un message
  async sendMessage(message: Omit<ChatMessage, 'id'>): Promise<string> {
    try {
      const docRef = await addDoc(this.collection, {
        ...message,
        timestamp: serverTimestamp(),
        isRead: false
      });
      return docRef.id;
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      throw error;
    }
  }

  // Récupérer les messages d'un Locrit
  async getLocritMessages(locritId: string): Promise<ChatMessage[]> {
    try {
      const q = query(
        this.collection,
        where('locritId', '==', locritId),
        orderBy('timestamp', 'asc'),
        limit(100)
      );
      const snapshot = await getDocs(q);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          timestamp: data.timestamp?.toDate() || new Date()
        } as ChatMessage;
      });
    } catch (error) {
      console.error('Erreur lors de la récupération des messages du Locrit:', error);
      throw error;
    }
  }

  // Écouter les messages d'un Locrit en temps réel
  subscribeToLocritMessages(locritId: string, callback: (messages: ChatMessage[]) => void): () => void {
    const q = query(
      this.collection,
      where('locritId', '==', locritId),
      orderBy('timestamp', 'asc'),
      limit(100)
    );

    return onSnapshot(q, (snapshot) => {
      const messages = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        timestamp: doc.data().timestamp?.toDate() || new Date()
      } as ChatMessage));
      callback(messages);
    });
  }

  // Récupérer les messages d'une conversation
  async getConversationMessages(conversationId: string): Promise<ChatMessage[]> {
    const q = query(
      this.collection,
      where('conversationId', '==', conversationId),
      orderBy('timestamp', 'asc'),
      limit(100)
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp: doc.data().timestamp?.toDate() || new Date()
    } as ChatMessage));
  }

  // Écouter les messages d'une conversation en temps réel
  subscribeToConversationMessages(conversationId: string, callback: (messages: ChatMessage[]) => void): () => void {
    const q = query(
      this.collection,
      where('conversationId', '==', conversationId),
      orderBy('timestamp', 'asc'),
      limit(100)
    );

    return onSnapshot(q, (snapshot) => {
      const messages = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        timestamp: doc.data().timestamp?.toDate() || new Date()
      } as ChatMessage));
      callback(messages);
    });
  }
}

// ============================================================================
// SERVICE CONVERSATIONS
// ============================================================================

export class ConversationService {
  private collection = collection(db, 'conversations');

  // Créer une nouvelle conversation
  async createConversation(conversation: Omit<Conversation, 'id'>): Promise<string> {
    const docRef = await addDoc(this.collection, {
      ...conversation,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      lastActivity: serverTimestamp()
    });
    return docRef.id;
  }

  // Récupérer toutes les conversations actives
  async getActiveConversations(): Promise<Conversation[]> {
    const q = query(
      this.collection,
      where('isActive', '==', true),
      orderBy('lastActivity', 'desc')
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      lastActivity: doc.data().lastActivity?.toDate() || new Date(),
      createdAt: doc.data().createdAt?.toDate() || new Date()
    } as Conversation));
  }

  // Écouter les conversations actives en temps réel
  subscribeToActiveConversations(callback: (conversations: Conversation[]) => void): () => void {
    const q = query(
      this.collection,
      where('isActive', '==', true),
      orderBy('lastActivity', 'desc')
    );

    return onSnapshot(q, (snapshot) => {
      const conversations = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        lastActivity: doc.data().lastActivity?.toDate() || new Date(),
        createdAt: doc.data().createdAt?.toDate() || new Date()
      } as Conversation));
      callback(conversations);
    });
  }

  // Mettre à jour une conversation
  async updateConversation(conversationId: string, updates: Partial<Conversation>): Promise<void> {
    const docRef = doc(db, 'conversations', conversationId);
    await updateDoc(docRef, {
      ...updates,
      updatedAt: serverTimestamp(),
      lastActivity: serverTimestamp()
    });
  }
}

// ============================================================================
// INSTANCES DES SERVICES
// ============================================================================

export const userService = new UserService();
export const locritService = new LocritService();
export const messageService = new MessageService();
export const conversationService = new ConversationService();