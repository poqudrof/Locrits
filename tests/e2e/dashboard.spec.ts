import { test, expect } from '@playwright/test';

test.describe('Dashboard Tests', () => {
  test('should load dashboard and display main elements', async ({ page }) => {
    await page.goto('/');

    // Check main heading
    await expect(page.getByRole('heading', { name: 'Tableau de bord' })).toBeVisible();

    // Check navigation elements
    await expect(page.getByRole('link', { name: '🏠 Locrit' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Tableau de bord' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Mes Locrits' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Créer Locrit' })).toBeVisible();

    // Check sidebar navigation
    await expect(page.getByRole('link', { name: '🏠 Tableau de bord Vue d\'ensemble des Locrits' })).toBeVisible();
    await expect(page.getByRole('link', { name: '🏠 Mes Locrits Locaux Gestion des Locrits locaux' })).toBeVisible();
    await expect(page.getByRole('link', { name: '➕ Créer Nouveau Locrit Interface de création' })).toBeVisible();
    await expect(page.getByRole('link', { name: '⚙️ Paramètres Application Configuration globale' })).toBeVisible();

    // Check stats cards
    await expect(page.getByText('Total Locrits 🏠 3')).toBeVisible();
    await expect(page.getByText('Actifs 🟢 2')).toBeVisible();
    await expect(page.getByText('Inactifs 🔴 1')).toBeVisible();

    // Check Locrit cards
    await expect(page.getByRole('heading', { name: 'Assistant Personnel' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Expert Technique' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Analyste Data' })).toBeVisible();
  });

  test('should navigate to different sections from dashboard', async ({ page }) => {
    await page.goto('/');

    // Test navigation to My Locrits
    await page.getByRole('link', { name: 'Mes Locrits' }).click();
    await expect(page).toHaveURL('/my-locrits');
    await expect(page.getByRole('heading', { name: 'Mes Locrits Locaux' })).toBeVisible();

    // Test navigation to Create Locrit
    await page.getByRole('link', { name: 'Créer Locrit' }).click();
    await expect(page).toHaveURL('/create-locrit');
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible();

    // Test navigation to Settings
    await page.getByRole('link', { name: '⚙️ Paramètres Application Configuration globale' }).click();
    await expect(page).toHaveURL('/settings');
    await expect(page.getByRole('heading', { name: '⚙️ Paramètres Application' })).toBeVisible();
  });

  test('should have functional theme toggle', async ({ page }) => {
    await page.goto('/');

    // Check theme toggle button exists
    await expect(page.getByRole('button', { name: 'Toggle theme' })).toBeVisible();

    // Click theme toggle and verify some visual change occurs
    await page.getByRole('button', { name: 'Toggle theme' }).click();
    // Note: Specific theme verification would depend on CSS class changes
  });
});