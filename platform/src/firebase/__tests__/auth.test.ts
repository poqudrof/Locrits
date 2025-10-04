import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth';
import { AuthService } from '../auth';

// Mock Firebase Auth functions
vi.mock('firebase/auth');

const mockSignInWithEmailAndPassword = vi.mocked(signInWithEmailAndPassword);
const mockCreateUserWithEmailAndPassword = vi.mocked(createUserWithEmailAndPassword);
const mockSignOut = vi.mocked(signOut);
const mockOnAuthStateChanged = vi.mocked(onAuthStateChanged);
const mockSignInWithPopup = vi.mocked(signInWithPopup);

describe('AuthService', () => {
  let authService: AuthService;

  beforeEach(() => {
    vi.clearAllMocks();
    authService = new AuthService();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('signInWithEmail', () => {
    it('should sign in user with email and password successfully', async () => {
      const mockUserCredential = {
        user: {
          uid: 'user-123',
          email: 'test@example.com',
          displayName: 'Test User',
          photoURL: null,
        },
      };

      mockSignInWithEmailAndPassword.mockResolvedValue(mockUserCredential as any);

      const result = await authService.signInWithEmail('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUserCredential.user);
      expect(mockSignInWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        'test@example.com',
        'password123'
      );
    });

    it('should handle sign in errors', async () => {
      const error = new Error('Invalid credentials');
      mockSignInWithEmailAndPassword.mockRejectedValue(error);

      const result = await authService.signInWithEmail('test@example.com', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });

    it('should handle specific Firebase auth errors', async () => {
      const firebaseError = {
        code: 'auth/user-not-found',
        message: 'User not found',
      };
      mockSignInWithEmailAndPassword.mockRejectedValue(firebaseError);

      const result = await authService.signInWithEmail('nonexistent@example.com', 'password');

      expect(result.success).toBe(false);
      expect(result.error).toContain('utilisateur introuvable');
    });
  });

  describe('signUpWithEmail', () => {
    it('should create new user with email and password successfully', async () => {
      const mockUserCredential = {
        user: {
          uid: 'new-user-123',
          email: 'newuser@example.com',
          displayName: null,
          photoURL: null,
        },
      };

      mockCreateUserWithEmailAndPassword.mockResolvedValue(mockUserCredential as any);

      const result = await authService.signUpWithEmail('newuser@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUserCredential.user);
      expect(mockCreateUserWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        'newuser@example.com',
        'password123'
      );
    });

    it('should handle sign up errors', async () => {
      const firebaseError = {
        code: 'auth/email-already-in-use',
        message: 'Email already in use',
      };
      mockCreateUserWithEmailAndPassword.mockRejectedValue(firebaseError);

      const result = await authService.signUpWithEmail('existing@example.com', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toContain('adresse email est déjà utilisée');
    });

    it('should handle weak password errors', async () => {
      const firebaseError = {
        code: 'auth/weak-password',
        message: 'Password is too weak',
      };
      mockCreateUserWithEmailAndPassword.mockRejectedValue(firebaseError);

      const result = await authService.signUpWithEmail('test@example.com', '123');

      expect(result.success).toBe(false);
      expect(result.error).toContain('mot de passe est trop faible');
    });
  });

  describe('signInWithGoogle', () => {
    it('should sign in with Google successfully', async () => {
      const mockUserCredential = {
        user: {
          uid: 'google-user-123',
          email: 'google@example.com',
          displayName: 'Google User',
          photoURL: 'https://example.com/photo.jpg',
        },
      };

      mockSignInWithPopup.mockResolvedValue(mockUserCredential as any);

      const result = await authService.signInWithGoogle();

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUserCredential.user);
      expect(mockSignInWithPopup).toHaveBeenCalledWith(
        expect.anything(),
        expect.any(GoogleAuthProvider)
      );
    });

    it('should handle Google sign in cancellation', async () => {
      const firebaseError = {
        code: 'auth/popup-closed-by-user',
        message: 'Popup closed by user',
      };
      mockSignInWithPopup.mockRejectedValue(firebaseError);

      const result = await authService.signInWithGoogle();

      expect(result.success).toBe(false);
      expect(result.error).toContain('annulée par l\'utilisateur');
    });

    it('should handle Google sign in network errors', async () => {
      const firebaseError = {
        code: 'auth/network-request-failed',
        message: 'Network error',
      };
      mockSignInWithPopup.mockRejectedValue(firebaseError);

      const result = await authService.signInWithGoogle();

      expect(result.success).toBe(false);
      expect(result.error).toContain('Erreur de connexion');
    });
  });

  describe('signOut', () => {
    it('should sign out user successfully', async () => {
      mockSignOut.mockResolvedValue(undefined as any);

      const result = await authService.signOut();

      expect(result.success).toBe(true);
      expect(mockSignOut).toHaveBeenCalledWith(expect.anything());
    });

    it('should handle sign out errors', async () => {
      const error = new Error('Sign out failed');
      mockSignOut.mockRejectedValue(error);

      const result = await authService.signOut();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Sign out failed');
    });
  });

  describe('onAuthStateChanged', () => {
    it('should set up auth state listener', () => {
      const callback = vi.fn();
      const unsubscribe = vi.fn();

      mockOnAuthStateChanged.mockReturnValue(unsubscribe);

      const result = authService.onAuthStateChanged(callback);

      expect(mockOnAuthStateChanged).toHaveBeenCalledWith(expect.anything(), callback);
      expect(result).toBe(unsubscribe);
    });

    it('should call callback with user when authenticated', () => {
      const callback = vi.fn();
      const mockUser = {
        uid: 'user-123',
        email: 'test@example.com',
        displayName: 'Test User',
      };

      mockOnAuthStateChanged.mockImplementation((auth, cb) => {
        cb(mockUser as any);
        return vi.fn();
      });

      authService.onAuthStateChanged(callback);

      expect(callback).toHaveBeenCalledWith(mockUser);
    });

    it('should call callback with null when not authenticated', () => {
      const callback = vi.fn();

      mockOnAuthStateChanged.mockImplementation((auth, cb) => {
        cb(null);
        return vi.fn();
      });

      authService.onAuthStateChanged(callback);

      expect(callback).toHaveBeenCalledWith(null);
    });
  });

  describe('getCurrentUser', () => {
    it('should return current user when authenticated', () => {
      const mockUser = {
        uid: 'user-123',
        email: 'test@example.com',
        displayName: 'Test User',
      };

      // Mock the auth.currentUser property
      Object.defineProperty(authService['auth'], 'currentUser', {
        value: mockUser,
        writable: true,
      });

      const result = authService.getCurrentUser();

      expect(result).toEqual(mockUser);
    });

    it('should return null when not authenticated', () => {
      Object.defineProperty(authService['auth'], 'currentUser', {
        value: null,
        writable: true,
      });

      const result = authService.getCurrentUser();

      expect(result).toBeNull();
    });
  });

  describe('getErrorMessage', () => {
    it('should return localized error messages for known Firebase errors', () => {
      const testCases = [
        { code: 'auth/user-not-found', expected: 'utilisateur introuvable' },
        { code: 'auth/wrong-password', expected: 'mot de passe incorrect' },
        { code: 'auth/email-already-in-use', expected: 'adresse email est déjà utilisée' },
        { code: 'auth/weak-password', expected: 'mot de passe est trop faible' },
        { code: 'auth/invalid-email', expected: 'adresse email invalide' },
        { code: 'auth/popup-closed-by-user', expected: 'annulée par l\'utilisateur' },
        { code: 'auth/network-request-failed', expected: 'Erreur de connexion' },
      ];

      testCases.forEach(({ code, expected }) => {
        const message = authService['getErrorMessage']({ code } as any);
        expect(message).toContain(expected);
      });
    });

    it('should return generic error message for unknown error codes', () => {
      const message = authService['getErrorMessage']({ code: 'auth/unknown-error' } as any);
      expect(message).toContain('Erreur d\'authentification');
    });

    it('should handle errors without code property', () => {
      const message = authService['getErrorMessage']({ message: 'Some error' } as any);
      expect(message).toBe('Some error');
    });
  });
});