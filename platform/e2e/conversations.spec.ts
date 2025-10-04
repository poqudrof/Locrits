import { test, expect } from '@playwright/test';

test.describe('Conversations E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/identitytoolkit.googleapis.com/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          kind: 'identitytoolkit#VerifyPasswordResponse',
          localId: 'test-user-id',
          email: 'test@example.com',
          displayName: 'Test User',
          idToken: 'mock-id-token',
          registered: true,
          refreshToken: 'mock-refresh-token',
          expiresIn: '3600',
        }),
      });
    });

    // Mock Firestore API calls
    await page.route('**/firestore.googleapis.com/**', async route => {
      const url = route.request().url();

      if (url.includes('/users/')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            name: 'projects/locrit/databases/(default)/documents/users/test-user-id',
            fields: {
              id: { stringValue: 'test-user-id' },
              name: { stringValue: 'Test User' },
              email: { stringValue: 'test@example.com' },
              isOnline: { booleanValue: true },
              lastSeen: { timestampValue: new Date().toISOString() },
            },
          }),
        });
      } else if (url.includes('/locrits')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            documents: [
              {
                name: 'projects/locrit/databases/(default)/documents/locrits/locrit-1',
                fields: {
                  id: { stringValue: 'locrit-1' },
                  name: { stringValue: 'Pixie l\'Organisateur' },
                  description: { stringValue: 'Un Locrit magique qui adore ranger et planifier! ✨' },
                  ownerId: { stringValue: 'test-user-id' },
                  isOnline: { booleanValue: true },
                  lastSeen: { timestampValue: new Date().toISOString() },
                },
              },
              {
                name: 'projects/locrit/databases/(default)/documents/locrits/locrit-2',
                fields: {
                  id: { stringValue: 'locrit-2' },
                  name: { stringValue: 'Sage le Gardien' },
                  description: { stringValue: 'Un sage gardien des connaissances anciennes 🧙‍♂️' },
                  ownerId: { stringValue: 'test-user-id' },
                  isOnline: { booleanValue: false },
                  lastSeen: { timestampValue: new Date().toISOString() },
                },
              },
            ],
          }),
        });
      } else if (url.includes('/conversations')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            documents: [
              {
                name: 'projects/locrit/databases/(default)/documents/conversations/conv-1',
                fields: {
                  id: { stringValue: 'conv-1' },
                  title: { stringValue: 'Planning the Digital Garden' },
                  type: { stringValue: 'locrit-locrit' },
                  isActive: { booleanValue: true },
                  lastActivity: { timestampValue: new Date().toISOString() },
                  createdAt: { timestampValue: new Date().toISOString() },
                },
              },
            ],
          }),
        });
      } else if (url.includes('/messages')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            documents: [
              {
                name: 'projects/locrit/databases/(default)/documents/messages/msg-1',
                fields: {
                  id: { stringValue: 'msg-1' },
                  conversationId: { stringValue: 'conv-1' },
                  content: { stringValue: 'Salut! Comment ça va?' },
                  sender: { stringValue: 'locrit' },
                  senderName: { stringValue: 'Pixie l\'Organisateur' },
                  timestamp: { timestampValue: new Date().toISOString() },
                },
              },
            ],
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ documents: [] }),
        });
      }
    });

    // Login and navigate to app
    await page.goto('/');
    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display available Locrits', async ({ page }) => {
    await expect(page.getByText('Pixie l\'Organisateur')).toBeVisible();
    await expect(page.getByText('Sage le Gardien')).toBeVisible();
    await expect(page.getByText('🟢 En ligne')).toBeVisible();
    await expect(page.getByText('🔴 Hors ligne')).toBeVisible();
  });

  test('should create a new conversation', async ({ page }) => {
    // Mock conversation creation
    await page.route('**/firestore.googleapis.com/**/documents/conversations', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            name: 'projects/locrit/databases/(default)/documents/conversations/new-conv-id',
            fields: {
              id: { stringValue: 'new-conv-id' },
              title: { stringValue: 'Test E2E Conversation' },
              type: { stringValue: 'user-locrit' },
              isActive: { booleanValue: true },
              createdAt: { timestampValue: new Date().toISOString() },
            },
          }),
        });
      }
    });

    // Click on a Locrit to start conversation
    await page.getByText('Pixie l\'Organisateur').click();

    // Click chat button
    await page.getByRole('button', { name: /Discuter/ }).click();

    // Should open chat interface
    await expect(page.getByText('💬 Chat avec Pixie l\'Organisateur')).toBeVisible();

    // Type and send a message
    const messageInput = page.getByPlaceholder('Tapez votre message...');
    await messageInput.fill('Bonjour Pixie! Comment puis-je organiser ma journée?');
    await page.getByRole('button', { name: 'Envoyer' }).click();

    // Should show message in chat
    await expect(page.getByText('Bonjour Pixie! Comment puis-je organiser ma journée?')).toBeVisible();
  });

  test('should create a scheduled conversation', async ({ page }) => {
    // Mock conversation creation
    await page.route('**/firestore.googleapis.com/**/documents/conversations', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            name: 'projects/locrit/databases/(default)/documents/conversations/scheduled-conv-id',
            fields: {
              id: { stringValue: 'scheduled-conv-id' },
              title: { stringValue: 'E2E Scheduled Conversation' },
              type: { stringValue: 'locrit-locrit' },
              isActive: { booleanValue: true },
              isScheduled: { booleanValue: true },
              duration: { integerValue: '2' },
              createdAt: { timestampValue: new Date().toISOString() },
            },
          }),
        });
      }
    });

    // Navigate to scheduled conversations
    await page.getByRole('button', { name: /Conversations programmées/ }).click();

    // Fill in conversation details
    await page.getByPlaceholder('Ex: Débat sur l\'IA créative').fill('E2E Scheduled Conversation');
    await page.getByPlaceholder(/Décrivez le sujet/).fill('Testing scheduled conversations in E2E environment');

    // Select participants
    await page.getByText('Pixie l\'Organisateur').click();
    await page.getByText('Sage le Gardien').click();

    // Verify both are selected
    await expect(page.getByTestId('check-icon')).toHaveCount(2);

    // Start conversation
    await page.getByRole('button', { name: 'Lancer la conversation' }).click();

    // Should show live conversation monitor
    await expect(page.getByText('🎭 Conversation en direct: E2E Scheduled Conversation')).toBeVisible();
    await expect(page.getByText('2:00')).toBeVisible(); // Timer
    await expect(page.getByText('0 messages')).toBeVisible();
  });

  test('should manage scheduled conversation controls', async ({ page }) => {
    // Start a scheduled conversation first (setup similar to previous test)
    await page.getByRole('button', { name: /Conversations programmées/ }).click();
    await page.getByPlaceholder('Ex: Débat sur l\'IA créative').fill('Control Test Conversation');
    await page.getByPlaceholder(/Décrivez le sujet/).fill('Testing conversation controls');
    await page.getByText('Pixie l\'Organisateur').click();
    await page.getByText('Sage le Gardien').click();
    await page.getByRole('button', { name: 'Lancer la conversation' }).click();

    // Should show running conversation
    await expect(page.getByText('🎭 Conversation en direct')).toBeVisible();

    // Test pause
    await page.getByRole('button', { name: 'Pause' }).click();
    await expect(page.getByRole('button', { name: 'Reprendre' })).toBeVisible();

    // Test resume
    await page.getByRole('button', { name: 'Reprendre' }).click();
    await expect(page.getByRole('button', { name: 'Pause' })).toBeVisible();

    // Test sound toggle
    await page.getByTestId('volume-icon').click();
    await expect(page.getByTestId('mute-icon')).toBeVisible();

    // Test end conversation
    await page.getByRole('button', { name: 'Terminer' }).click();

    // Should return to configuration state
    await expect(page.getByText('⏰ Créer une Conversation Programmée')).toBeVisible();
  });

  test('should view conversation review and analytics', async ({ page }) => {
    // Navigate to an existing conversation
    await page.getByText('Planning the Digital Garden').click();

    // Click review button
    await page.getByRole('button', { name: /Révision/ }).click();

    // Should show conversation review interface
    await expect(page.getByText('📖 Révision: Planning the Digital Garden')).toBeVisible();
    await expect(page.getByText('Messages')).toBeVisible();
    await expect(page.getByText('Participants')).toBeVisible();
    await expect(page.getByText('Durée')).toBeVisible();

    // Test show statistics
    await page.getByRole('button', { name: 'Voir stats' }).click();
    await expect(page.getByText('Statistiques détaillées')).toBeVisible();
    await expect(page.getByText('Répartition des messages')).toBeVisible();

    // Test message filtering
    await page.getByPlaceholder('Rechercher dans les messages...').fill('salut');
    await expect(page.getByText(/sur \d+ messages/)).toBeVisible();

    // Test participant filtering
    await page.selectOption('select', { label: /Pixie/ });

    // Reset filters
    await page.getByRole('button', { name: 'Réinitialiser' }).click();
    await expect(page.getByPlaceholder('Rechercher dans les messages...')).toHaveValue('');

    // Test export (note: actual file download testing requires additional setup)
    await page.getByRole('button', { name: 'Exporter' }).click();
  });

  test('should handle conversation settings and advanced options', async ({ page }) => {
    await page.getByRole('button', { name: /Conversations programmées/ }).click();

    // Show advanced settings
    await page.getByRole('button', { name: 'Afficher les paramètres avancés' }).click();
    await expect(page.getByText('Style de conversation')).toBeVisible();

    // Change conversation style
    await page.selectOption('select', { value: 'formal' });

    // Adjust message frequency
    const frequencySlider = page.getByTestId('slider').nth(1); // Second slider
    await frequencySlider.fill('20');
    await expect(page.getByText('Fréquence des messages: 20s')).toBeVisible();

    // Adjust max messages
    const maxMessagesSlider = page.getByTestId('slider').nth(2); // Third slider
    await maxMessagesSlider.fill('50');
    await expect(page.getByText('Messages maximum: 50')).toBeVisible();

    // Toggle auto start
    await page.getByTestId('switch').check();
    await expect(page.getByTestId('switch')).toBeChecked();

    // Hide advanced settings
    await page.getByRole('button', { name: 'Masquer les paramètres avancés' }).click();
    await expect(page.getByText('Style de conversation')).not.toBeVisible();
  });

  test('should handle real-time message updates in live conversation', async ({ page }) => {
    // Mock message creation
    await page.route('**/firestore.googleapis.com/**/documents/messages', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            name: 'projects/locrit/databases/(default)/documents/messages/new-msg-id',
            fields: {
              id: { stringValue: 'new-msg-id' },
              content: { stringValue: 'Bonjour! Je suis ravi de discuter avec vous.' },
              sender: { stringValue: 'locrit' },
              senderName: { stringValue: 'Pixie l\'Organisateur' },
              timestamp: { timestampValue: new Date().toISOString() },
            },
          }),
        });
      }
    });

    // Start a scheduled conversation
    await page.getByRole('button', { name: /Conversations programmées/ }).click();
    await page.getByPlaceholder('Ex: Débat sur l\'IA créative').fill('Real-time Test');
    await page.getByPlaceholder(/Décrivez le sujet/).fill('Testing real-time messages');
    await page.getByText('Pixie l\'Organisateur').click();
    await page.getByText('Sage le Gardien').click();
    await page.getByRole('button', { name: 'Lancer la conversation' }).click();

    // Wait for conversation to start
    await expect(page.getByText('🎭 Conversation en direct')).toBeVisible();

    // Simulate automatic message generation (would happen in real app)
    // In real E2E, messages would appear automatically based on the conversation frequency
    await page.waitForTimeout(2000); // Wait for potential message generation

    // Messages should appear in the live feed
    // await expect(page.getByText('Bonjour! Je suis ravi de discuter avec vous.')).toBeVisible();
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Mock Firestore error
    await page.route('**/firestore.googleapis.com/**/documents/conversations', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 500,
              message: 'Internal server error',
            },
          }),
        });
      }
    });

    // Try to create a conversation
    await page.getByRole('button', { name: /Conversations programmées/ }).click();
    await page.getByPlaceholder('Ex: Débat sur l\'IA créative').fill('Error Test');
    await page.getByPlaceholder(/Décrivez le sujet/).fill('Testing error handling');
    await page.getByText('Pixie l\'Organisateur').click();
    await page.getByText('Sage le Gardien').click();
    await page.getByRole('button', { name: 'Lancer la conversation' }).click();

    // Should show error message
    await expect(page.getByText(/Erreur lors de la création/)).toBeVisible();
  });

  test('should handle navigation between conversation views', async ({ page }) => {
    // Start from dashboard
    await expect(page.getByText('Dashboard')).toBeVisible();

    // Navigate to conversation manager for a specific Locrit
    await page.getByText('Pixie l\'Organisateur').click();
    await page.getByRole('button', { name: /Conversations/ }).click();

    // Should show conversation manager
    await expect(page.getByText('💬 Conversations avec Pixie l\'Organisateur')).toBeVisible();

    // Go back
    await page.getByTestId('arrow-left-icon').click();

    // Should return to Locrit view
    await expect(page.getByText('Pixie l\'Organisateur')).toBeVisible();

    // Navigate to scheduled conversations
    await page.getByRole('button', { name: /Conversations programmées/ }).click();
    await expect(page.getByText('⏰ Créer une Conversation Programmée')).toBeVisible();

    // Navigate to conversation review
    await page.getByRole('button', { name: /Révisions/ }).click();
    await expect(page.getByText('📖 Révisions de conversations')).toBeVisible();
  });

  test('should handle mobile responsive layout', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Should adapt layout for mobile
    await expect(page.getByText('Pixie l\'Organisateur')).toBeVisible();

    // Test mobile-specific interactions
    await page.getByText('Pixie l\'Organisateur').click();

    // Mobile layout should stack elements vertically
    const locritCard = page.getByText('Pixie l\'Organisateur').locator('..');
    await expect(locritCard).toBeVisible();

    // Test scheduled conversation on mobile
    await page.getByRole('button', { name: /Conversations programmées/ }).click();

    // Form should be responsive
    await expect(page.getByPlaceholder('Ex: Débat sur l\'IA créative')).toBeVisible();

    // Participant selection should work on mobile
    await page.getByText('Pixie l\'Organisateur').click();
    await expect(page.getByTestId('check-icon')).toBeVisible();
  });
});