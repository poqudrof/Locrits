import { test, expect } from '@playwright/test';

test.describe('Locrits Management Tests', () => {
  test('should display locrits list with all information', async ({ page }) => {
    await page.goto('/my-locrits');

    // Check main heading
    await expect(page.getByRole('heading', { name: 'Mes Locrits Locaux' })).toBeVisible();
    await expect(page.getByText('Gérez vos Locrits créés localement')).toBeVisible();

    // Check new locrit button
    await expect(page.getByRole('link', { name: '➕ Nouveau Locrit' })).toBeVisible();

    // Check Assistant Personnel locrit card
    await expect(page.getByText('🤖 Assistant Personnel')).toBeVisible();
    await expect(page.getByText('🟢 Actif')).toBeVisible();
    await expect(page.getByText('Assistant général pour les tâches quotidiennes')).toBeVisible();
    await expect(page.getByText('llama3.2')).toBeVisible();
    await expect(page.getByText('Créé: 2025-09-25')).toBeVisible();

    // Check Expert Technique locrit card
    await expect(page.getByText('🤖 Expert Technique')).toBeVisible();
    await expect(page.getByText('Spécialisé dans le développement web')).toBeVisible();
    await expect(page.getByText('codellama')).toBeVisible();
    await expect(page.getByText('expert-tech.localhost.run')).toBeVisible();

    // Check Analyste Data locrit card
    await expect(page.getByText('🤖 Analyste Data')).toBeVisible();
    await expect(page.getByText('🔴 Inactif')).toBeVisible();
    await expect(page.getByText('Aide à l\'analyse de données')).toBeVisible();

    // Check action buttons for each locrit
    await expect(page.getByRole('button', { name: '💬 Chat' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '⏹️ Arrêter' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '⚙️ Configurer' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '📄 Détails' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '🗑️ Supprimer' }).first()).toBeVisible();
  });

  test('should display permission settings for each locrit', async ({ page }) => {
    await page.goto('/my-locrits');

    // Check "Ouvert à" permissions for Assistant Personnel
    const assistantSection = page.locator('text=🤖 Assistant Personnel').locator('..').locator('..');
    await expect(assistantSection.getByText('🔐 Ouvert à')).toBeVisible();
    await expect(assistantSection.getByText('✅ 👥 Humains')).toBeVisible();
    await expect(assistantSection.getByText('✅ 🤖 Autres Locrits')).toBeVisible();
    await expect(assistantSection.getByText('✅ 📧 Invitations')).toBeVisible();
    await expect(assistantSection.getByText('❌ 🌐 Internet')).toBeVisible();
    await expect(assistantSection.getByText('❌ 🏢 Plateforme')).toBeVisible();

    // Check "Accès aux données" permissions
    await expect(assistantSection.getByText('📊 Accès aux données')).toBeVisible();
    await expect(assistantSection.getByText('✅ 📝 Logs')).toBeVisible();
    await expect(assistantSection.getByText('✅ 🧠 Mémoire rapide')).toBeVisible();
    await expect(assistantSection.getByText('✅ 🤖 Infos LLM')).toBeVisible();
  });

  test('should handle locrit state changes', async ({ page }) => {
    await page.goto('/my-locrits');

    // Check that active locrits have stop button
    const activeLocrit = page.locator('text=🟢 Actif').first().locator('..').locator('..');
    await expect(activeLocrit.getByRole('button', { name: '⏹️ Arrêter' })).toBeVisible();
    await expect(activeLocrit.getByRole('button', { name: '💬 Chat' })).toBeEnabled();

    // Check that inactive locrits have start button
    const inactiveLocrit = page.locator('text=🔴 Inactif').locator('..').locator('..');
    await expect(inactiveLocrit.getByRole('button', { name: '▶️ Démarrer' })).toBeVisible();
    await expect(inactiveLocrit.getByRole('button', { name: '💬 Chat' })).toBeDisabled();
  });

  test('should navigate to chat from locrit cards', async ({ page }) => {
    await page.goto('/my-locrits');

    // Click chat button for Assistant Personnel
    await page.getByRole('link', { name: '💬 Chat' }).first().click();
    await expect(page).toHaveURL('/chat/Assistant Personnel');
  });
});