import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { getStorage, connectStorageEmulator } from "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyCIhMEWcFKzCeMvkFG2uxvEbmS5m6qUhiI",
  authDomain: "locrit.firebaseapp.com",
  projectId: "locrit",
  storageBucket: "locrit.firebasestorage.app",
  messagingSenderId: "150648923940",
  appId: "1:150648923940:web:26407f6900045bd23ff5b1",
  measurementId: "G-92CRH1S5QQ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);

// Connect to emulators in development (optional)
// if (process.env.NODE_ENV === 'development') {
//   connectFirestoreEmulator(db, 'localhost', 8080);
//   connectAuthEmulator(auth, 'http://localhost:9099');
//   connectStorageEmulator(storage, 'localhost', 9199);
// }

export default app;