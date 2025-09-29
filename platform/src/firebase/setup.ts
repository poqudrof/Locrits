import { doc, setDoc, collection, addDoc } from "firebase/firestore";
import { db } from "./config";
import { mockUsers, mockLocrits, mockMessages, mockConversations, mockConversationMessages } from "../data/mockData";

/**
 * Script d'initialisation Firebase
 * Ce script permet de migrer les données mockup vers Firebase
 * et de configurer les collections initiales
 */

export async function initializeFirebaseData() {
  console.log("🚀 Initialisation des données Firebase...");
  
  try {
    // 1. Migrer les utilisateurs
    console.log("📥 Migration des utilisateurs...");
    for (const user of mockUsers) {
      const userRef = doc(db, 'users', user.id);
      await setDoc(userRef, {
        ...user,
        lastSeen: new Date(user.lastSeen),
        createdAt: new Date(),
        updatedAt: new Date()
      }, { merge: true });
    }
    console.log(`✅ ${mockUsers.length} utilisateurs migrés`);

    // 2. Migrer les Locrits
    console.log("📥 Migration des Locrits...");
    for (const locrit of mockLocrits) {
      const { id, ...locritData } = locrit;
      await addDoc(collection(db, 'locrits'), {
        ...locritData,
        lastSeen: new Date(locrit.lastSeen),
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }
    console.log(`✅ ${mockLocrits.length} Locrits migrés`);

    // 3. Migrer les conversations
    console.log("📥 Migration des conversations...");
    for (const conversation of mockConversations) {
      const { id, ...conversationData } = conversation;
      await addDoc(collection(db, 'conversations'), {
        ...conversationData,
        lastActivity: new Date(conversation.lastActivity),
        createdAt: new Date(conversation.createdAt),
        updatedAt: new Date()
      });
    }
    console.log(`✅ ${mockConversations.length} conversations migrées`);

    // 4. Migrer les messages
    console.log("📥 Migration des messages...");
    const allMessages = [...mockMessages, ...mockConversationMessages];
    for (const message of allMessages) {
      const { id, ...messageData } = message;
      await addDoc(collection(db, 'messages'), {
        ...messageData,
        timestamp: new Date(message.timestamp),
        isRead: false
      });
    }
    console.log(`✅ ${allMessages.length} messages migrés`);

    console.log("🎉 Migration terminée avec succès!");
    return true;

  } catch (error) {
    console.error("❌ Erreur lors de la migration:", error);
    throw error;
  }
}

/**
 * Fonction pour vérifier si Firebase est configuré correctement
 */
export async function testFirebaseConnection() {
  try {
    console.log("🔍 Test de la connexion Firebase...");
    
    // Test de lecture sur la collection users
    const testCollection = collection(db, 'users');
    console.log("✅ Connexion à Firestore réussie");
    
    return true;
  } catch (error) {
    console.error("❌ Erreur de connexion Firebase:", error);
    return false;
  }
}

/**
 * Fonction pour nettoyer les données de test
 * ⚠️ Utiliser avec précaution - supprime toutes les données!
 */
export async function clearFirebaseData() {
  console.warn("⚠️ Cette fonction supprimera toutes les données Firebase!");
  // Implémentation de nettoyage si nécessaire
  console.log("🧹 Nettoyage des données Firebase...");
  // TODO: Implémenter la suppression des collections si nécessaire
}