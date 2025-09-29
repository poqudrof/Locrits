import { useState, useEffect } from 'react';
import { 
  signInAnonymous, 
  signInWithEmail, 
  signUpWithEmail, 
  signInWithGoogle,
  logout, 
  onAuthChange, 
  AuthUser 
} from '../firebase/auth';

export interface UseAuthReturn {
  user: AuthUser | null;
  isLoading: boolean;
  signInAnonymously: () => Promise<void>;
  signInWithCredentials: (email: string, password: string) => Promise<void>;
  signInWithGoogleSSO: () => Promise<void>;
  signUp: (email: string, password: string, displayName: string) => Promise<void>;
  signOut: () => Promise<void>;
  error: string | null;
}

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthChange((user) => {
      setUser(user);
      setIsLoading(false);
    });

    // Timeout de sécurité - si Firebase ne répond pas dans les 10 secondes
    const timeout = setTimeout(() => {
      console.warn("Timeout d'authentification - Firebase ne répond pas");
      setIsLoading(false);
    }, 10000);

    return () => {
      unsubscribe();
      clearTimeout(timeout);
    };
  }, []);

  const signInAnonymously = async (): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      await signInAnonymous();
    } catch (err: any) {
      setError(getErrorMessage(err));
      setIsLoading(false);
    }
  };

  const signInWithCredentials = async (email: string, password: string): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      await signInWithEmail(email, password);
    } catch (err: any) {
      setError(getErrorMessage(err));
      setIsLoading(false);
    }
  };

  const signUp = async (email: string, password: string, displayName: string): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      await signUpWithEmail(email, password, displayName);
    } catch (err: any) {
      setError(getErrorMessage(err));
      setIsLoading(false);
    }
  };

  const signInWithGoogleSSO = async (): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      await signInWithGoogle();
    } catch (err: any) {
      setError(getErrorMessage(err));
      setIsLoading(false);
    }
  };

  const signOut = async (): Promise<void> => {
    try {
      setError(null);
      await logout();
    } catch (err: any) {
      setError(getErrorMessage(err));
    }
  };

  return {
    user,
    isLoading,
    signInAnonymously,
    signInWithCredentials: signInWithCredentials,
    signInWithGoogleSSO,
    signUp,
    signOut,
    error
  };
};

const getErrorMessage = (error: any): string => {
  switch (error.code) {
    case 'auth/user-not-found':
      return 'Aucun compte trouvé avec cette adresse email';
    case 'auth/wrong-password':
      return 'Mot de passe incorrect';
    case 'auth/email-already-in-use':
      return 'Cette adresse email est déjà utilisée';
    case 'auth/weak-password':
      return 'Le mot de passe doit contenir au moins 6 caractères';
    case 'auth/invalid-email':
      return 'Adresse email invalide';
    case 'auth/network-request-failed':
      return 'Erreur de connexion. Vérifiez votre connexion internet';
    case 'auth/popup-closed-by-user':
      return 'Connexion annulée par l\'utilisateur';
    case 'auth/popup-blocked':
      return 'Pop-up bloquée par le navigateur. Autorisez les pop-ups pour ce site';
    case 'auth/cancelled-popup-request':
      return 'Une autre demande de connexion est en cours';
    case 'auth/account-exists-with-different-credential':
      return 'Un compte existe déjà avec cette adresse email avec un autre mode de connexion';
    default:
      return error.message || 'Une erreur est survenue';
  }
};