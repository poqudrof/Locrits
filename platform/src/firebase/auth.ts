import {
  signInAnonymously,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  User,
  updateProfile
} from "firebase/auth";
import { doc, setDoc, getDoc, updateDoc, serverTimestamp } from "firebase/firestore";
import { auth, db } from "./config";

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  isAnonymous: boolean;
}

// Connexion anonyme
export const signInAnonymous = async (): Promise<AuthUser> => {
  try {
    const result = await signInAnonymously(auth);
    const user = result.user;
    
    // Créer ou mettre à jour le document utilisateur
    await createOrUpdateUserDoc(user, "Utilisateur Anonyme");
    
    return {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName || "Utilisateur Anonyme",
      isAnonymous: user.isAnonymous
    };
  } catch (error) {
    console.error("Erreur lors de la connexion anonyme:", error);
    throw error;
  }
};

// Connexion avec email/mot de passe
export const signInWithEmail = async (email: string, password: string): Promise<AuthUser> => {
  try {
    const result = await signInWithEmailAndPassword(auth, email, password);
    const user = result.user;
    
    // Mettre à jour le statut en ligne
    await updateUserStatus(user.uid, true);
    
    return {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      isAnonymous: user.isAnonymous
    };
  } catch (error) {
    console.error("Erreur lors de la connexion:", error);
    throw error;
  }
};

// Inscription avec email/mot de passe
export const signUpWithEmail = async (
  email: string, 
  password: string, 
  displayName: string
): Promise<AuthUser> => {
  try {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    const user = result.user;
    
    // Mettre à jour le profil avec le nom d'affichage
    await updateProfile(user, { displayName });
    
    // Créer le document utilisateur
    await createOrUpdateUserDoc(user, displayName);
    
    return {
      uid: user.uid,
      email: user.email,
      displayName: displayName,
      isAnonymous: user.isAnonymous
    };
  } catch (error) {
    console.error("Erreur lors de l'inscription:", error);
    throw error;
  }
};

// Connexion avec Google
export const signInWithGoogle = async (): Promise<AuthUser> => {
  try {
    const provider = new GoogleAuthProvider();
    // Permet de sélectionner le compte Google
    provider.setCustomParameters({
      prompt: 'select_account'
    });
    
    const result = await signInWithPopup(auth, provider);
    const user = result.user;
    
    // Créer ou mettre à jour le document utilisateur
    await createOrUpdateUserDoc(user, user.displayName || "Utilisateur Google");
    
    return {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      isAnonymous: user.isAnonymous
    };
  } catch (error) {
    console.error("Erreur lors de la connexion Google:", error);
    throw error;
  }
};

// Déconnexion
export const logout = async (): Promise<void> => {
  try {
    if (auth.currentUser) {
      await updateUserStatus(auth.currentUser.uid, false);
    }
    await signOut(auth);
  } catch (error) {
    console.error("Erreur lors de la déconnexion:", error);
    throw error;
  }
};

// Écouter les changements d'état d'authentification
export const onAuthChange = (callback: (user: AuthUser | null) => void): (() => void) => {
  return onAuthStateChanged(auth, async (user: User | null) => {
    try {
      if (user) {
        const authUser: AuthUser = {
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          isAnonymous: user.isAnonymous
        };
        
        // Mettre à jour le statut en ligne (sans bloquer si ça échoue)
        try {
          await updateUserStatus(user.uid, true);
        } catch (error) {
          console.warn("Erreur lors de la mise à jour du statut utilisateur:", error);
        }
        
        callback(authUser);
      } else {
        callback(null);
      }
    } catch (error) {
      console.error("Erreur dans onAuthChange:", error);
      callback(null);
    }
  });
};

// Créer ou mettre à jour le document utilisateur dans Firestore
const createOrUpdateUserDoc = async (user: User, displayName: string): Promise<void> => {
  try {
    const userRef = doc(db, 'users', user.uid);
    const userSnap = await getDoc(userRef);
    
    const userData = {
      id: user.uid,
      name: displayName,
      email: user.email || '',
      isOnline: true,
      lastSeen: serverTimestamp(),
      ...(userSnap.exists() ? { updatedAt: serverTimestamp() } : { createdAt: serverTimestamp() })
    };
    
    await setDoc(userRef, userData, { merge: true });
  } catch (error) {
    console.error("Erreur lors de la création/mise à jour du document utilisateur:", error);
    // Ne pas faire échouer l'authentification si la création du document échoue
  }
};

// Mettre à jour le statut en ligne de l'utilisateur
const updateUserStatus = async (userId: string, isOnline: boolean): Promise<void> => {
  try {
    const userRef = doc(db, 'users', userId);
    await updateDoc(userRef, {
      isOnline,
      lastSeen: serverTimestamp(),
      updatedAt: serverTimestamp()
    });
  } catch (error) {
    console.error("Erreur lors de la mise à jour du statut:", error);
    // Ne pas faire échouer l'authentification si la mise à jour échoue
  }
};

// Obtenir l'utilisateur actuel
export const getCurrentUser = (): AuthUser | null => {
  const user = auth.currentUser;
  if (user) {
    return {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      isAnonymous: user.isAnonymous
    };
  }
  return null;
};