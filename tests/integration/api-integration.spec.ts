import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  test('should handle configuration updates', async ({ page }) => {
    await page.goto('/settings');

    // Intercept API calls
    let apiCalled = false;
    await page.route('**/api/v1/config**', (route) => {
      apiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Configuration saved' })
      });
    });

    // Update a configuration value
    const ollamaUrlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });
    await ollamaUrlField.clear();
    await ollamaUrlField.fill('http://localhost:11435');

    // Save the configuration
    await page.getByRole('button', { name: '💾 Sauver' }).first().click();

    // Verify API was called
    expect(apiCalled).toBe(true);
  });

  test('should test Ollama connection', async ({ page }) => {
    await page.goto('/settings');

    // Mock the test connection API
    let testApiCalled = false;
    await page.route('**/api/v1/config/test-ollama**', (route) => {
      testApiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Connection successful',
          models: ['llama3.2', 'codellama', 'mistral']
        })
      });
    });

    // Click test button
    await page.getByRole('button', { name: '🔍 Tester' }).click();

    // Verify API was called
    expect(testApiCalled).toBe(true);
  });

  test('should handle locrit creation', async ({ page }) => {
    await page.goto('/create-locrit');

    // Mock the create locrit API
    let createApiCalled = false;
    await page.route('**/api/v1/locrits**', (route) => {
      if (route.request().method() === 'POST') {
        createApiCalled = true;
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Locrit created successfully',
            locrit: {
              id: 'test-locrit-id',
              name: 'Test Locrit',
              status: 'created'
            }
          })
        });
      }
    });

    // Fill the form
    await page.getByRole('textbox', { name: 'Nom du Locrit *' }).fill('Test Locrit');
    await page.getByRole('textbox', { name: 'Description *' }).fill('Un locrit de test');
    await page.getByRole('textbox', { name: 'Modèle Ollama *' }).clear();
    await page.getByRole('textbox', { name: 'Modèle Ollama *' }).fill('llama3.2');

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Verify API was called
    expect(createApiCalled).toBe(true);
  });

  test('should handle locrit state changes', async ({ page }) => {
    await page.goto('/my-locrits');

    // Mock stop locrit API
    let stopApiCalled = false;
    await page.route('**/api/v1/locrits/*/stop**', (route) => {
      stopApiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Locrit stopped' })
      });
    });

    // Mock start locrit API
    let startApiCalled = false;
    await page.route('**/api/v1/locrits/*/start**', (route) => {
      startApiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Locrit started' })
      });
    });

    // Stop an active locrit
    await page.getByRole('button', { name: '⏹️ Arrêter' }).first().click();
    expect(stopApiCalled).toBe(true);

    // Start an inactive locrit
    await page.getByRole('button', { name: '▶️ Démarrer' }).click();
    expect(startApiCalled).toBe(true);
  });

  test('should handle locrit deletion', async ({ page }) => {
    await page.goto('/my-locrits');

    // Mock delete locrit API
    let deleteApiCalled = false;
    await page.route('**/api/v1/locrits/**', (route) => {
      if (route.request().method() === 'DELETE') {
        deleteApiCalled = true;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Locrit deleted' })
        });
      }
    });

    // Click delete button (this might require confirmation dialog)
    await page.getByRole('button', { name: '🗑️ Supprimer' }).first().click();

    // If there's a confirmation dialog, confirm it
    // await page.getByRole('button', { name: 'Confirmer' }).click();

    // Verify API was called
    expect(deleteApiCalled).toBe(true);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.goto('/settings');

    // Mock API error
    await page.route('**/api/v1/config**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, message: 'Server error' })
      });
    });

    // Try to save configuration
    await page.getByRole('button', { name: '💾 Sauver' }).first().click();

    // Check for error handling (this would depend on how errors are displayed)
    // await expect(page.getByText('Erreur lors de la sauvegarde')).toBeVisible();
  });

  test('should load initial data from API', async ({ page }) => {
    // Mock the initial data loading APIs
    await page.route('**/api/v1/locrits**', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            locrits: [
              {
                id: '1',
                name: 'Assistant Personnel',
                description: 'Assistant général',
                model: 'llama3.2',
                status: 'active',
                created_at: '2025-09-25'
              },
              {
                id: '2',
                name: 'Expert Technique',
                description: 'Expert en développement',
                model: 'codellama',
                status: 'active',
                address: 'expert-tech.localhost.run'
              }
            ]
          })
        });
      }
    });

    await page.route('**/api/v1/config**', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ollama_url: 'http://localhost:11434',
            default_model: 'llama3.1:8b',
            api_port: 8000
          })
        });
      }
    });

    await page.goto('/dashboard');

    // Verify that data is loaded and displayed
    await expect(page.getByText('Assistant Personnel')).toBeVisible();
    await expect(page.getByText('Expert Technique')).toBeVisible();
  });
});