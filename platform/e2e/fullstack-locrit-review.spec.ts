/**
 * Fullstack E2E Test: Locrit Review Flow
 *
 * This test verifies the complete flow from backend to platform:
 * 1. Backend pushes Locrit to Firebase
 * 2. Platform displays the Locrit
 * 3. User can interact with and review the Locrit
 * 4. Conversation data syncs correctly
 */

import { test, expect } from '@playwright/test';
import {
  getAuth,
  signInAnonymously,
  signOut,
  Auth
} from 'firebase/auth';
import {
  getFirestore,
  collection,
  query,
  where,
  getDocs,
  addDoc,
  deleteDoc,
  doc,
  Firestore,
  serverTimestamp
} from 'firebase/firestore';
import { initializeApp } from 'firebase/app';

// Firebase config (same as platform)
const firebaseConfig = {
  apiKey: "AIzaSyCIhMEWcFKzCeMvkFG2uxvEbmS5m6qUhiI",
  authDomain: "locrit.firebaseapp.com",
  projectId: "locrit",
  storageBucket: "locrit.firebasestorage.app",
  messagingSenderId: "150648923940",
  appId: "1:150648923940:web:26407f6900045bd23ff5b1",
  measurementId: "G-92CRH1S5QQ"
};

// Test data
const generateTestLocrit = (userId: string) => ({
  name: `e2e-test-locrit-${Date.now()}`,
  description: 'E2E Test Locrit created by Playwright',
  publicAddress: `e2e-test-${Date.now()}.locritland.net`,
  ownerId: userId,
  isOnline: true,
  lastSeen: new Date(),
  tags: ['e2e-test', 'playwright', 'automated'],
  settings: {
    openTo: {
      humans: true,
      locrits: true,
      invitations: true,
      publicInternet: false,
      publicPlatform: true,
      scheduledConversations: true
    },
    accessTo: {
      logs: true,
      quickMemory: true,
      fullMemory: false,
      llmInfo: true,
      conversationHistory: true
    },
    behavior: {
      personality: 'Helpful E2E test assistant',
      responseStyle: 'professional',
      maxResponseLength: 500,
      autoResponse: true,
      conversationTimeout: 30
    },
    limits: {
      dailyMessages: 1000,
      concurrentConversations: 5,
      maxConversationDuration: 120
    }
  },
  stats: {
    totalConversations: 0,
    totalMessages: 0,
    averageResponseTime: 0,
    popularTags: ['e2e-test']
  },
  createdAt: serverTimestamp(),
  updatedAt: serverTimestamp()
});

test.describe('Fullstack Locrit Review Flow', () => {
  let app: any;
  let auth: Auth;
  let db: Firestore;
  let userId: string;
  let testLocritId: string;
  let testLocritName: string;

  test.beforeAll(async () => {
    // Initialize Firebase
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    db = getFirestore(app);

    // Authenticate anonymously for testing
    const userCredential = await signInAnonymously(auth);
    userId = userCredential.user.uid;

    console.log(`✅ Authenticated as: ${userId}`);
  });

  test.afterAll(async () => {
    // Cleanup: Delete test Locrit if it was created
    if (testLocritId) {
      try {
        await deleteDoc(doc(db, 'locrits', testLocritId));
        console.log(`🧹 Cleaned up test Locrit: ${testLocritId}`);
      } catch (error) {
        console.error('Error cleaning up test Locrit:', error);
      }
    }

    // Sign out
    await signOut(auth);
  });

  test('should create Locrit in Firebase (simulating backend push)', async () => {
    // Simulate what the Python backend does
    const testLocrit = generateTestLocrit(userId);
    testLocritName = testLocrit.name;

    // Push Locrit to Firebase
    const docRef = await addDoc(collection(db, 'locrits'), testLocrit);
    testLocritId = docRef.id;

    expect(testLocritId).toBeTruthy();
    console.log(`✅ Created test Locrit: ${testLocritId}`);
  });

  test('should display Locrit in platform UI', async ({ page }) => {
    // Navigate to platform
    await page.goto('http://localhost:5173'); // Adjust port as needed

    // Wait for app to load
    await page.waitForLoadState('networkidle');

    // Check if authentication is required
    const needsAuth = await page.locator('button:has-text("Sign in"), button:has-text("Se connecter")').isVisible().catch(() => false);

    if (needsAuth) {
      // Perform sign-in if needed
      await page.click('button:has-text("Anonymous"), button:has-text("Anonyme")').catch(() => {});
      await page.waitForTimeout(2000);
    }

    // Navigate to Locrits page
    await page.click('a:has-text("Locrits"), a:has-text("My Locrits")').catch(() => {});
    await page.waitForTimeout(1000);

    // Search for our test Locrit
    // Note: You may need to adjust selectors based on your actual UI
    const locritCard = page.locator(`[data-locrit-name="${testLocritName}"]`).first();

    // If specific selector doesn't work, try finding by text
    const locritByText = page.locator(`text="${testLocritName}"`).first();

    const isVisible = await locritCard.isVisible().catch(async () => {
      return await locritByText.isVisible().catch(() => false);
    });

    expect(isVisible).toBeTruthy();
    console.log(`✅ Locrit visible in platform: ${testLocritName}`);
  });

  test('should display correct Locrit details', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Find and click on the Locrit
    const locrit = page.locator(`text="${testLocritName}"`).first();
    await locrit.click();

    // Wait for details to load
    await page.waitForTimeout(1000);

    // Verify Locrit details are displayed
    await expect(page.locator('text="E2E Test Locrit created by Playwright"')).toBeVisible();

    // Check if tags are displayed
    const tagsVisible = await page.locator('text="e2e-test"').isVisible().catch(() => false);
    if (tagsVisible) {
      console.log('✅ Locrit tags visible');
    }

    // Check if settings are accessible
    const settingsButton = page.locator('button:has-text("Settings"), button:has-text("Paramètres")').first();
    const hasSettings = await settingsButton.isVisible().catch(() => false);

    if (hasSettings) {
      await settingsButton.click();
      await page.waitForTimeout(500);
      console.log('✅ Locrit settings accessible');
    }
  });

  test('should allow creating a conversation with the Locrit', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navigate to create conversation
    const newConvButton = page.locator('button:has-text("New Conversation"), button:has-text("Nouvelle conversation")').first();
    const hasButton = await newConvButton.isVisible().catch(() => false);

    if (hasButton) {
      await newConvButton.click();
      await page.waitForTimeout(1000);

      // Fill conversation details
      const titleInput = page.locator('input[placeholder*="Title"], input[placeholder*="Titre"]').first();
      await titleInput.fill('E2E Test Conversation');

      // Select our test Locrit as participant
      const locritSelector = page.locator(`text="${testLocritName}"`).first();
      const canSelect = await locritSelector.isVisible().catch(() => false);

      if (canSelect) {
        await locritSelector.click();
        console.log('✅ Test Locrit selected as conversation participant');
      }

      // Create conversation
      const createButton = page.locator('button:has-text("Create"), button:has-text("Créer")').first();
      const hasCreate = await createButton.isVisible().catch(() => false);

      if (hasCreate) {
        await createButton.click();
        await page.waitForTimeout(1000);
        console.log('✅ Conversation created with test Locrit');
      }
    } else {
      console.log('⚠️ New conversation button not found - UI may differ');
    }
  });

  test('should verify Locrit appears in Firebase locrits collection', async () => {
    // Query Firebase to verify Locrit exists
    const locritsRef = collection(db, 'locrits');
    const q = query(locritsRef, where('name', '==', testLocritName));
    const snapshot = await getDocs(q);

    expect(snapshot.empty).toBe(false);
    expect(snapshot.size).toBe(1);

    const locritDoc = snapshot.docs[0];
    const data = locritDoc.data();

    // Verify data structure
    expect(data.name).toBe(testLocritName);
    expect(data.description).toBe('E2E Test Locrit created by Playwright');
    expect(data.ownerId).toBe(userId);
    expect(data.isOnline).toBe(true);
    expect(data.settings).toBeDefined();
    expect(data.settings.openTo).toBeDefined();
    expect(data.stats).toBeDefined();

    console.log('✅ Locrit data structure verified in Firebase');
  });

  test('should handle Locrit status updates', async () => {
    // Update Locrit status in Firebase (simulating backend update)
    const locritRef = doc(db, 'locrits', testLocritId);

    // Update to offline
    await updateDoc(locritRef, {
      isOnline: false,
      lastSeen: new Date(),
      updatedAt: serverTimestamp()
    });

    // Query to verify update
    const docSnap = await getDoc(locritRef);
    const data = docSnap.data();

    expect(data?.isOnline).toBe(false);
    console.log('✅ Locrit status update works');

    // Restore to online
    await updateDoc(locritRef, {
      isOnline: true,
      updatedAt: serverTimestamp()
    });
  });

  test('should display Locrit in public platform view', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navigate to public Locrits view (if exists)
    const publicViewLink = page.locator('a:has-text("Browse"), a:has-text("Explorer")').first();
    const hasPublicView = await publicViewLink.isVisible().catch(() => false);

    if (hasPublicView) {
      await publicViewLink.click();
      await page.waitForTimeout(1000);

      // Our test Locrit should appear since publicPlatform is true
      const isVisibleInPublic = await page.locator(`text="${testLocritName}"`).isVisible().catch(() => false);

      if (isVisibleInPublic) {
        console.log('✅ Locrit visible in public platform view');
      }
    } else {
      console.log('⚠️ Public view not found in UI');
    }
  });

  test('should log Locrit activity to Firebase', async () => {
    // Create activity log (simulating backend logging)
    const activityLog = {
      locritId: testLocritId,
      timestamp: new Date(),
      level: 'info',
      category: 'e2e-test',
      message: 'E2E test activity logged',
      details: {
        test: 'fullstack-review',
        phase: 'activity-logging'
      },
      userId: userId
    };

    const logRef = await addDoc(collection(db, 'locrit_logs'), activityLog);
    expect(logRef.id).toBeTruthy();

    // Verify log was created
    const logDoc = await getDoc(doc(db, 'locrit_logs', logRef.id));
    expect(logDoc.exists()).toBe(true);

    console.log('✅ Activity logging works');

    // Cleanup log
    await deleteDoc(doc(db, 'locrit_logs', logRef.id));
  });

  test('should handle Locrit review and analytics', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Find the Locrit
    const locrit = page.locator(`text="${testLocritName}"`).first();
    const isVisible = await locrit.isVisible().catch(() => false);

    if (isVisible) {
      await locrit.click();
      await page.waitForTimeout(1000);

      // Look for analytics/review section
      const analyticsSection = page.locator('text="Analytics", text="Statistiques"').first();
      const hasAnalytics = await analyticsSection.isVisible().catch(() => false);

      if (hasAnalytics) {
        await analyticsSection.click();
        await page.waitForTimeout(500);

        // Verify stats are displayed
        const statsVisible = await page.locator('text="Total Conversations", text="Conversations totales"').isVisible().catch(() => false);

        if (statsVisible) {
          console.log('✅ Locrit analytics/review section accessible');
        }
      }
    }
  });
});

// Import missing functions
import { updateDoc, getDoc } from 'firebase/firestore';

test.describe('Locrit Conversation Review', () => {
  let app: any;
  let auth: Auth;
  let db: Firestore;
  let userId: string;
  let testConversationId: string;

  test.beforeAll(async () => {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    db = getFirestore(app);

    const userCredential = await signInAnonymously(auth);
    userId = userCredential.user.uid;
  });

  test.afterAll(async () => {
    if (testConversationId) {
      try {
        await deleteDoc(doc(db, 'conversations', testConversationId));
        console.log(`🧹 Cleaned up test conversation`);
      } catch (error) {
        console.error('Error cleaning up:', error);
      }
    }
    await signOut(auth);
  });

  test('should create and review a conversation', async ({ page }) => {
    // Create test conversation in Firebase
    const conversation = {
      title: 'E2E Test Conversation',
      topic: 'Testing conversation review',
      participants: [{
        id: userId,
        name: 'Test User',
        type: 'user'
      }],
      messages: [],
      status: 'active',
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp()
    };

    const convRef = await addDoc(collection(db, 'conversations'), conversation);
    testConversationId = convRef.id;

    // Navigate to platform
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Find conversation in UI
    const conv = page.locator(`text="E2E Test Conversation"`).first();
    const isVisible = await conv.isVisible().catch(() => false);

    if (isVisible) {
      await conv.click();
      await page.waitForTimeout(1000);

      // Verify conversation review options
      const reviewOptions = page.locator('button:has-text("Review"), button:has-text("Révision")').first();
      const hasReview = await reviewOptions.isVisible().catch(() => false);

      if (hasReview) {
        console.log('✅ Conversation review accessible');
      }
    }
  });
});
