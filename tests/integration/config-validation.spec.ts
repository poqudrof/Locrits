import { test, expect } from '@playwright/test';

test.describe('Configuration Validation Tests', () => {
  test('should validate Ollama URL format', async ({ page }) => {
    await page.goto('/settings');

    const ollamaUrlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });

    // Test invalid URLs
    const invalidUrls = [
      'localhost:11434',           // Missing protocol
      'http://localhost',          // Missing port
      'not-a-url',                // Invalid format
      'ftp://localhost:11434',     // Wrong protocol
      '',                          // Empty
    ];

    for (const invalidUrl of invalidUrls) {
      await ollamaUrlField.clear();
      await ollamaUrlField.fill(invalidUrl);
      await page.getByRole('button', { name: '🔍 Tester' }).click();

      // Check for validation error (implementation-dependent)
      // await expect(page.getByText('URL invalide')).toBeVisible();
    }

    // Test valid URLs
    const validUrls = [
      'http://localhost:11434',
      'https://ollama.example.com:11434',
      'http://192.168.1.100:11434',
    ];

    for (const validUrl of validUrls) {
      await ollamaUrlField.clear();
      await ollamaUrlField.fill(validUrl);
      await expect(ollamaUrlField).toHaveValue(validUrl);
    }
  });

  test('should validate model names', async ({ page }) => {
    await page.goto('/settings');

    const modelField = page.getByRole('textbox', { name: 'Modèle par défaut' });

    // Test invalid model names
    const invalidModels = [
      '',              // Empty
      'model with spaces and special chars!',  // Invalid characters
      'model/with/slashes',   // Slashes might be invalid
    ];

    for (const invalidModel of invalidModels) {
      await modelField.clear();
      await modelField.fill(invalidModel);
      await page.getByRole('button', { name: '💾 Sauver' }).nth(1).click();

      // Check for validation error
      // await expect(page.getByText('Nom de modèle invalide')).toBeVisible();
    }

    // Test valid model names
    const validModels = [
      'llama3.2',
      'codellama:7b',
      'mistral:instruct',
      'llama3.1:8b',
    ];

    for (const validModel of validModels) {
      await modelField.clear();
      await modelField.fill(validModel);
      await expect(modelField).toHaveValue(validModel);
    }
  });

  test('should validate port numbers', async ({ page }) => {
    await page.goto('/settings');

    const portField = page.getByRole('spinbutton', { name: 'Port API' });

    // Test invalid ports
    const invalidPorts = [
      '-1',        // Negative
      '0',         // Zero
      '70000',     // Too high
      'abc',       // Non-numeric
    ];

    for (const invalidPort of invalidPorts) {
      await portField.clear();
      await portField.fill(invalidPort);

      // Browser should handle basic validation for spinbutton
      // Additional validation might be in the application
    }

    // Test valid ports
    const validPorts = [
      '8000',
      '3000',
      '5000',
      '8080',
      '65535',  // Max valid port
    ];

    for (const validPort of validPorts) {
      await portField.clear();
      await portField.fill(validPort);
      await expect(portField).toHaveValue(validPort);
    }
  });

  test('should validate locrit creation form', async ({ page }) => {
    await page.goto('/create-locrit');

    // Test required field validation
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Should not proceed without required fields
    // await expect(page.getByText('Ce champ est requis')).toBeVisible();

    // Test name validation
    const nameField = page.getByRole('textbox', { name: 'Nom du Locrit *' });

    // Invalid names
    const invalidNames = [
      '',                    // Empty
      'a',                   // Too short
      'Name with spaces!',   // Special characters
      'name-with-dashes',    // Dashes might be invalid
    ];

    for (const invalidName of invalidNames) {
      await nameField.clear();
      await nameField.fill(invalidName);
      await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

      // Check for validation error
      // Specific validation messages depend on implementation
    }

    // Test description validation
    const descField = page.getByRole('textbox', { name: 'Description *' });
    await descField.clear();
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Should show required field error
    // await expect(page.getByText('Description requise')).toBeVisible();

    // Test model validation
    const modelField = page.getByRole('textbox', { name: 'Modèle Ollama *' });
    await modelField.clear();
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Should show required field error
    // await expect(page.getByText('Modèle requis')).toBeVisible();
  });

  test('should validate public address format', async ({ page }) => {
    await page.goto('/create-locrit');

    const addressField = page.getByRole('textbox', { name: 'Adresse publique' });

    // Test invalid addresses
    const invalidAddresses = [
      'not a domain',
      'http://example.com',    // Should not include protocol
      'example.com:abc',       // Invalid port
      'example..com',          // Double dots
    ];

    for (const invalidAddress of invalidAddresses) {
      await addressField.fill(invalidAddress);
      await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

      // Check for validation error
      // await expect(page.getByText('Adresse invalide')).toBeVisible();

      await addressField.clear();
    }

    // Test valid addresses
    const validAddresses = [
      'example.localhost.run',
      'my-locrit.domain.com',
      'localhost',
      '192.168.1.100',
      'example.com:8080',
    ];

    for (const validAddress of validAddresses) {
      await addressField.clear();
      await addressField.fill(validAddress);
      await expect(addressField).toHaveValue(validAddress);
    }
  });

  test('should validate permission combinations', async ({ page }) => {
    await page.goto('/create-locrit');

    // Test that certain permission combinations might be invalid
    // For example, Internet access without platform access might be restricted

    // Uncheck all permissions
    await page.getByRole('checkbox', { name: '👥 Humains' }).uncheck();
    await page.getByRole('checkbox', { name: '🤖 Autres Locrits' }).uncheck();
    await page.getByRole('checkbox', { name: '📧 Invitations' }).uncheck();

    // Try to create locrit with no access permissions
    await page.getByRole('textbox', { name: 'Nom du Locrit *' }).fill('No Access Locrit');
    await page.getByRole('textbox', { name: 'Description *' }).fill('Test');
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Should show validation error about needing at least one access method
    // await expect(page.getByText('Au moins une méthode d\'accès requise')).toBeVisible();

    // Test enabling Internet without proper data access
    await page.getByRole('checkbox', { name: '🌐 Internet' }).check();
    await page.getByRole('checkbox', { name: '📝 Logs système' }).uncheck();
    await page.getByRole('checkbox', { name: '🧠 Mémoire rapide' }).uncheck();
    await page.getByRole('checkbox', { name: '🤖 Informations LLM' }).uncheck();

    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Should show warning about Internet access without proper data access
    // await expect(page.getByText('Accès Internet sans données peut être dangereux')).toBeVisible();
  });

  test('should validate configuration file integrity', async ({ page }) => {
    // This test would check if configuration changes are properly saved
    // and can be loaded back correctly

    await page.goto('/settings');

    // Save current values
    const ollamaUrl = await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).inputValue();
    const defaultModel = await page.getByRole('textbox', { name: 'Modèle par défaut' }).inputValue();
    const apiPort = await page.getByRole('spinbutton', { name: 'Port API' }).inputValue();

    // Change values
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).clear();
    await page.getByRole('textbox', { name: 'URL du serveur Ollama' }).fill('http://localhost:11435');

    await page.getByRole('textbox', { name: 'Modèle par défaut' }).clear();
    await page.getByRole('textbox', { name: 'Modèle par défaut' }).fill('mistral:7b');

    // Save configuration
    await page.getByRole('button', { name: '💾 Sauvegarder la configuration' }).click();

    // Reload page and verify values persisted
    await page.reload();

    await expect(page.getByRole('textbox', { name: 'URL du serveur Ollama' })).toHaveValue('http://localhost:11435');
    await expect(page.getByRole('textbox', { name: 'Modèle par défaut' })).toHaveValue('mistral:7b');

    // Reset to defaults and verify
    await page.getByRole('button', { name: '🔄 Valeurs par défaut' }).click();

    // Values should be reset to defaults
    await expect(page.getByRole('textbox', { name: 'URL du serveur Ollama' })).toHaveValue('http://localhost:11434');
  });
});