import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form on initial load', async ({ page }) => {
    await expect(page.getByText('Connexion à Locrits')).toBeVisible();
    await expect(page.getByPlaceholder('Votre email')).toBeVisible();
    await expect(page.getByPlaceholder('Votre mot de passe')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Se connecter' })).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page.getByText('Email requis')).toBeVisible();
    await expect(page.getByText('Mot de passe requis')).toBeVisible();
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.getByPlaceholder('Votre email').fill('invalid-email');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page.getByText('Email invalide')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.getByPlaceholder('Votre email').fill('invalid@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('wrongpassword');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page.getByText(/Identifiants invalides/)).toBeVisible();
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Mock Firebase auth success
    await page.route('**/identitytoolkit.googleapis.com/**', async route => {
      if (route.request().url().includes('signInWithPassword')) {
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
      }
    });

    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Bienvenue, Test User')).toBeVisible();
  });

  test('should switch to signup form', async ({ page }) => {
    await page.getByText('Créer un compte').click();

    await expect(page.getByText('Créer votre compte Locrits')).toBeVisible();
    await expect(page.getByPlaceholder('Votre nom')).toBeVisible();
    await expect(page.getByPlaceholder('Votre email')).toBeVisible();
    await expect(page.getByPlaceholder('Votre mot de passe')).toBeVisible();
    await expect(page.getByPlaceholder('Confirmer le mot de passe')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Créer le compte' })).toBeVisible();
  });

  test('should successfully create account', async ({ page }) => {
    // Mock Firebase auth success for signup
    await page.route('**/identitytoolkit.googleapis.com/**', async route => {
      if (route.request().url().includes('signUp')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            kind: 'identitytoolkit#SignupNewUserResponse',
            localId: 'new-user-id',
            email: 'newuser@example.com',
            displayName: 'New User',
            idToken: 'mock-new-id-token',
            refreshToken: 'mock-new-refresh-token',
            expiresIn: '3600',
          }),
        });
      }
    });

    await page.getByText('Créer un compte').click();

    await page.getByPlaceholder('Votre nom').fill('New User');
    await page.getByPlaceholder('Votre email').fill('newuser@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByPlaceholder('Confirmer le mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Créer le compte' }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Bienvenue, New User')).toBeVisible();
  });

  test('should show error for password mismatch', async ({ page }) => {
    await page.getByText('Créer un compte').click();

    await page.getByPlaceholder('Votre nom').fill('Test User');
    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByPlaceholder('Confirmer le mot de passe').fill('differentpassword');
    await page.getByRole('button', { name: 'Créer le compte' }).click();

    await expect(page.getByText('Les mots de passe ne correspondent pas')).toBeVisible();
  });

  test('should handle Google OAuth login', async ({ page }) => {
    // Mock Google OAuth flow
    await page.route('**/identitytoolkit.googleapis.com/**', async route => {
      if (route.request().url().includes('signInWithIdp')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            kind: 'identitytoolkit#VerifyAssertionResponse',
            localId: 'google-user-id',
            email: 'google@example.com',
            displayName: 'Google User',
            idToken: 'mock-google-id-token',
            refreshToken: 'mock-google-refresh-token',
            expiresIn: '3600',
            photoUrl: 'https://example.com/avatar.jpg',
          }),
        });
      }
    });

    await page.getByRole('button', { name: /Continuer avec Google/ }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Bienvenue, Google User')).toBeVisible();
  });

  test('should handle logout', async ({ page }) => {
    // First login
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

    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page).toHaveURL(/\/dashboard/);

    // Now logout
    await page.getByRole('button', { name: 'Déconnexion' }).click();

    // Should redirect back to login
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Connexion à Locrits')).toBeVisible();
  });

  test('should persist authentication across page refreshes', async ({ page }) => {
    // Login first
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

    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page).toHaveURL(/\/dashboard/);

    // Refresh page
    await page.reload();

    // Should still be logged in
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Bienvenue, Test User')).toBeVisible();
  });

  test('should handle authentication state loading', async ({ page }) => {
    // Simulate slow auth state resolution
    await page.route('**/identitytoolkit.googleapis.com/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
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

    await page.getByPlaceholder('Votre email').fill('test@example.com');
    await page.getByPlaceholder('Votre mot de passe').fill('password123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    // Should show loading state
    await expect(page.getByText('Connexion en cours...')).toBeVisible();

    // Then redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 });
  });
});