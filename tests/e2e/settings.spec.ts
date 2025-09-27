import { test, expect } from '@playwright/test';

test.describe('Settings Page Tests', () => {
  test('should display settings page with all configuration sections', async ({ page }) => {
    await page.goto('/settings');

    // Check main heading
    await expect(page.getByRole('heading', { name: '⚙️ Paramètres Application' })).toBeVisible();
    await expect(page.getByText('Configurez les paramètres globaux de l\'application')).toBeVisible();

    // Check Ollama configuration section
    await expect(page.getByText('🤖 Configuration Ollama')).toBeVisible();
    await expect(page.getByText('Paramètres de connexion au serveur Ollama')).toBeVisible();

    // Check Ollama URL field
    const ollamaUrlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });
    await expect(ollamaUrlField).toBeVisible();
    await expect(ollamaUrlField).toHaveValue('http://localhost:11434');

    // Check test and save buttons for Ollama URL
    await expect(page.getByRole('button', { name: '🔍 Tester' })).toBeVisible();
    await expect(page.getByRole('button', { name: '💾 Sauver' }).first()).toBeVisible();

    // Check default model field
    const defaultModelField = page.getByRole('textbox', { name: 'Modèle par défaut' });
    await expect(defaultModelField).toBeVisible();
    await expect(defaultModelField).toHaveValue('llama3.1:8b');

    // Check network configuration section
    await expect(page.getByText('🌐 Configuration Réseau')).toBeVisible();
    await expect(page.getByText('Paramètres du serveur API et de la connectivité')).toBeVisible();

    const portField = page.getByRole('spinbutton', { name: 'Port API' });
    await expect(portField).toBeVisible();
    await expect(portField).toHaveValue('8000');

    // Check system status section
    await expect(page.getByText('📊 Statut du système')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Interface Web' })).toBeVisible();
    await expect(page.getByText('Opérationnelle')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Serveur Ollama' })).toBeVisible();
    await expect(page.getByText('Connecté')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Configuration' })).toBeVisible();
    await expect(page.getByText('Prête')).toBeVisible();
  });

  test('should display memory configuration section', async ({ page }) => {
    await page.goto('/settings');

    // Check memory configuration section
    await expect(page.getByText('🧠 Configuration Mémoire')).toBeVisible();
    await expect(page.getByText('Paramètres de stockage et de mémoire (lecture seule)')).toBeVisible();

    // Check database path field (should be read-only)
    const dbField = page.locator('input[value="data/locrit_memory.db"]');
    await expect(dbField).toBeVisible();

    // Check max messages field (should be read-only)
    const maxMessagesField = page.locator('input[value="10000"]');
    await expect(maxMessagesField).toBeVisible();

    // Check action buttons
    await expect(page.getByRole('button', { name: '🔄 Valeurs par défaut' })).toBeVisible();
    await expect(page.getByRole('button', { name: '💾 Sauvegarder la configuration' })).toBeVisible();
  });

  test('should allow editing configuration fields', async ({ page }) => {
    await page.goto('/settings');

    // Test editing Ollama URL
    const ollamaUrlField = page.getByRole('textbox', { name: 'URL du serveur Ollama' });
    await ollamaUrlField.clear();
    await ollamaUrlField.fill('http://localhost:11435');
    await expect(ollamaUrlField).toHaveValue('http://localhost:11435');

    // Test editing default model
    const defaultModelField = page.getByRole('textbox', { name: 'Modèle par défaut' });
    await defaultModelField.clear();
    await defaultModelField.fill('codellama:7b');
    await expect(defaultModelField).toHaveValue('codellama:7b');

    // Test editing API port
    const portField = page.getByRole('spinbutton', { name: 'Port API' });
    await portField.clear();
    await portField.fill('8001');
    await expect(portField).toHaveValue('8001');
  });

  test('should have functional action buttons', async ({ page }) => {
    await page.goto('/settings');

    // Test Ollama connection test button
    await expect(page.getByRole('button', { name: '🔍 Tester' })).toBeVisible();
    await expect(page.getByRole('button', { name: '🔍 Tester' })).toBeEnabled();

    // Test save buttons
    const saveButtons = page.getByRole('button', { name: '💾 Sauver' });
    await expect(saveButtons.first()).toBeVisible();
    await expect(saveButtons.first()).toBeEnabled();

    // Test reset to defaults button
    await expect(page.getByRole('button', { name: '🔄 Valeurs par défaut' })).toBeVisible();
    await expect(page.getByRole('button', { name: '🔄 Valeurs par défaut' })).toBeEnabled();

    // Test main save configuration button
    await expect(page.getByRole('button', { name: '💾 Sauvegarder la configuration' })).toBeVisible();
    await expect(page.getByRole('button', { name: '💾 Sauvegarder la configuration' })).toBeEnabled();
  });

  test('should display proper help text and descriptions', async ({ page }) => {
    await page.goto('/settings');

    // Check field descriptions
    await expect(page.getByText('URL complète du serveur Ollama (inclut le protocole et le port)')).toBeVisible();
    await expect(page.getByText('Modèle utilisé par défaut pour les nouveaux Locrits')).toBeVisible();
    await expect(page.getByText('Port d\'écoute du serveur API')).toBeVisible();
    await expect(page.getByText('Chemin vers la base de données de mémoire (non modifiable via l\'interface)')).toBeVisible();
    await expect(page.getByText('Nombre maximum de messages en mémoire (non modifiable via l\'interface)')).toBeVisible();
  });

  test('should show system status indicators', async ({ page }) => {
    await page.goto('/settings');

    // Check for status indicators (🟢 green circles)
    await expect(page.getByText('🟢').first()).toBeVisible();
    await expect(page.getByText('📁')).toBeVisible(); // File icon for configuration

    // Verify status text
    await expect(page.getByText('État des services et composants')).toBeVisible();
  });
});