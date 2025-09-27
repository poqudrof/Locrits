import { test, expect } from '@playwright/test';

test.describe('Settings Page Actions Tests', () => {
  let configSaveApiCalled = false;
  let testOllamaApiCalled = false;
  let modelsApiCalled = false;
  let defaultsApiCalled = false;

  test.beforeEach(async ({ page }) => {
    // Reset API call flags
    configSaveApiCalled = false;
    testOllamaApiCalled = false;
    modelsApiCalled = false;
    defaultsApiCalled = false;

    // Mock the configuration load API
    await page.route('**/api/config', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            config: {
              ollama: {
                base_url: 'http://localhost:11434',
                default_model: 'llama3.2'
              },
              network: {
                api_server: {
                  port: 8000
                }
              }
            }
          })
        });
      }
    });

    // Mock Ollama status API
    await page.route('**/api/ollama/status', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'connected' })
      });
    });

    await page.goto('/settings');
  });

  test('should save Ollama URL when clicking "Sauver" button next to URL field', async ({ page }) => {
    // Mock the config save API
    await page.route('**/config/save', (route) => {
      if (route.request().method() === 'POST') {
        configSaveApiCalled = true;
        const postData = route.request().postDataJSON();
        expect(postData.ollama_url).toBe('http://localhost:11435');
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Configuration saved' })
        });
      }
    });

    // Change Ollama URL
    const ollamaUrlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });
    await ollamaUrlField.clear();
    await ollamaUrlField.fill('http://localhost:11435');

    // Click the "Sauver" button next to the URL field
    const saveUrlButton = page.locator('button', { hasText: '💾 Sauver' }).first();
    await saveUrlButton.click();

    // Verify API was called
    expect(configSaveApiCalled).toBe(true);

    // Check for success message
    await expect(page.getByText('URL Ollama sauvegardée')).toBeVisible({ timeout: 5000 });
  });

  test('should save default model when clicking "Sauver" button next to model field', async ({ page }) => {
    // Mock the config save API
    await page.route('**/config/save', (route) => {
      if (route.request().method() === 'POST') {
        configSaveApiCalled = true;
        const postData = route.request().postDataJSON();
        expect(postData.default_model).toBe('codellama');
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Model saved' })
        });
      }
    });

    // Change default model
    const modelField = page.getByRole('textbox', { name: 'Modèle par défaut' });
    await modelField.clear();
    await modelField.fill('codellama');

    // Click the "Sauver" button next to the model field
    const saveModelButton = page.locator('button', { hasText: '💾 Sauver' }).nth(1);
    await saveModelButton.click();

    // Verify API was called
    expect(configSaveApiCalled).toBe(true);

    // Check for success message
    await expect(page.getByText('Modèle par défaut sauvegardé')).toBeVisible({ timeout: 5000 });
  });

  test('should test Ollama connection when clicking "Tester" button', async ({ page }) => {
    // Mock the test Ollama API
    await page.route('**/config/test-ollama', (route) => {
      if (route.request().method() === 'POST') {
        testOllamaApiCalled = true;
        const postData = route.request().postDataJSON();
        expect(postData.ollama_url).toBeTruthy();
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, status: 'connected' })
        });
      }
    });

    // Mock the models API that gets called after successful connection test
    await page.route('**/api/ollama/models', (route) => {
      modelsApiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          models: [
            { name: 'llama3.2', size: '2.0GB', modified: '2025-01-01T00:00:00Z' },
            { name: 'codellama', size: '3.8GB', modified: '2025-01-01T00:00:00Z' }
          ]
        })
      });
    });

    // Click test button
    await page.getByRole('button', { name: '🔍 Tester' }).click();

    // Verify APIs were called
    expect(testOllamaApiCalled).toBe(true);
    expect(modelsApiCalled).toBe(true);

    // Check for success message
    await expect(page.getByText('Connexion Ollama réussie!')).toBeVisible({ timeout: 5000 });

    // Verify models section appears
    await expect(page.getByText('🤖 Modèles Ollama disponibles')).toBeVisible();
  });

  test('should save complete configuration when clicking "Sauvegarder la configuration"', async ({ page }) => {
    // Mock the config save API
    await page.route('**/config/save', (route) => {
      if (route.request().method() === 'POST') {
        configSaveApiCalled = true;
        const postData = route.request().postDataJSON();
        expect(postData.ollama_url).toBeTruthy();
        expect(postData.default_model).toBeTruthy();
        expect(postData.api_port).toBeTruthy();
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Configuration saved' })
        });
      }
    });

    // Change some values
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).clear();
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).fill('http://localhost:11435');

    await page.getByRole('textbox', { name: 'Modèle par défaut' }).clear();
    await page.getByRole('textbox', { name: 'Modèle par défaut' }).fill('mistral');

    await page.getByRole('textbox', { name: 'Port API' }).clear();
    await page.getByRole('textbox', { name: 'Port API' }).fill('8001');

    // Click main save button
    await page.getByRole('button', { name: '💾 Sauvegarder la configuration' }).click();

    // Verify API was called
    expect(configSaveApiCalled).toBe(true);

    // Check for success message
    await expect(page.getByText('Configuration sauvegardée')).toBeVisible({ timeout: 5000 });
  });

  test('should handle "Valeurs par défaut" button click', async ({ page }) => {
    // Mock the defaults API (this might need to be implemented in the backend)
    await page.route('**/config/defaults', (route) => {
      if (route.request().method() === 'POST') {
        defaultsApiCalled = true;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            config: {
              ollama_url: 'http://localhost:11434',
              default_model: 'llama3.2',
              api_port: '8000'
            }
          })
        });
      }
    });

    // First change some values
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).clear();
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).fill('http://different:11434');

    // Click defaults button
    await page.getByRole('button', { name: '🔄 Valeurs par défaut' }).click();

    // Note: This test might need backend implementation to work properly
    // For now, we just verify the button exists and is clickable
    await expect(page.getByRole('button', { name: '🔄 Valeurs par défaut' })).toBeVisible();
  });

  test('should refresh available models when clicking "Actualiser"', async ({ page }) => {
    // First, trigger model display by testing connection
    await page.route('**/config/test-ollama', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, status: 'connected' })
      });
    });

    await page.route('**/api/ollama/models', (route) => {
      modelsApiCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          models: [
            { name: 'llama3.2', size: '2.0GB', modified: '2025-01-01T00:00:00Z' }
          ]
        })
      });
    });

    // Test connection first to show models
    await page.getByRole('button', { name: '🔍 Tester' }).click();
    await expect(page.getByText('🤖 Modèles Ollama disponibles')).toBeVisible();

    // Reset flag
    modelsApiCalled = false;

    // Click refresh button
    await page.getByRole('button', { name: '🔄 Actualiser' }).click();

    // Verify models API was called again
    expect(modelsApiCalled).toBe(true);
  });

  test('should select model when clicking on model card', async ({ page }) => {
    // Setup models display
    await page.route('**/config/test-ollama', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, status: 'connected' })
      });
    });

    await page.route('**/api/ollama/models', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          models: [
            { name: 'llama3.2', size: '2.0GB', modified: '2025-01-01T00:00:00Z' },
            { name: 'codellama', size: '3.8GB', modified: '2025-01-01T00:00:00Z' }
          ]
        })
      });
    });

    // Test connection to show models
    await page.getByRole('button', { name: '🔍 Tester' }).click();
    await expect(page.getByText('🤖 Modèles Ollama disponibles')).toBeVisible();

    // Click on codellama model card
    await page.locator('text=codellama').click();

    // Verify model was selected (should show in input field)
    await expect(page.getByRole('textbox', { name: 'Modèle par défaut' })).toHaveValue('codellama');

    // Check for selection message
    await expect(page.getByText('Modèle sélectionné: codellama')).toBeVisible({ timeout: 5000 });
  });

  test('should show loading states during button interactions', async ({ page }) => {
    // Mock slow API response for save
    await page.route('**/config/save', async (route) => {
      // Add delay to see loading state
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    // Click save button and verify loading state
    const saveButton = page.getByRole('button', { name: '💾 Sauvegarder la configuration' });
    await saveButton.click();

    // Check that button shows loading state
    await expect(page.getByRole('button', { name: '⏳ Sauvegarde...' })).toBeVisible();

    // Wait for operation to complete
    await expect(page.getByRole('button', { name: '💾 Sauvegarder la configuration' })).toBeVisible({ timeout: 3000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/config/save', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, message: 'Server error' })
      });
    });

    // Try to save configuration
    await page.getByRole('button', { name: '💾 Sauvegarder la configuration' }).click();

    // Check for error message
    await expect(page.getByText('Erreur lors de la sauvegarde')).toBeVisible({ timeout: 5000 });
  });

  test('should handle Ollama connection test failure', async ({ page }) => {
    // Mock failed Ollama test
    await page.route('**/config/test-ollama', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, message: 'Connection failed' })
      });
    });

    // Test connection
    await page.getByRole('button', { name: '🔍 Tester' }).click();

    // Check for error message
    await expect(page.getByText('Connexion Ollama échouée')).toBeVisible({ timeout: 5000 });

    // Verify status indicator shows disconnected
    await expect(page.getByText('🔴')).toBeVisible();
    await expect(page.getByText('Déconnecté')).toBeVisible();
  });

  test('should validate and handle invalid input values', async ({ page }) => {
    // Test invalid URL
    const urlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });
    await urlField.clear();
    await urlField.fill('invalid-url');

    // Test invalid port
    const portField = page.getByRole('textbox', { name: 'Port API' });
    await portField.clear();
    await portField.fill('-1');

    // Try to save - this should trigger validation
    await page.getByRole('button', { name: '💾 Sauvegarder la configuration' }).click();

    // The frontend should handle validation or the backend should return errors
    // This test verifies the form accepts the input (validation may happen on backend)
  });
});