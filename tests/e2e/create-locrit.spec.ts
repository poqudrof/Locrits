import { test, expect } from '@playwright/test';

test.describe('Create Locrit Tests', () => {
  test('should display create locrit form with all fields', async ({ page }) => {
    await page.goto('/create-locrit');

    // Check main heading and description
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible();
    await expect(page.getByText('Configurez votre nouveau Locrit avec ses paramètres d\'accès')).toBeVisible();

    // Check back button
    await expect(page.getByRole('link', { name: '← Retour à la liste' })).toBeVisible();

    // Check general information section
    await expect(page.getByText('📝 Informations générales')).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Nom du Locrit *' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Description *' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Modèle Ollama *' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Adresse publique' })).toBeVisible();

    // Check default model value
    await expect(page.getByRole('textbox', { name: 'Modèle Ollama *' })).toHaveValue('llama3.2');

    // Check "Ouvert à" section
    await expect(page.getByText('🔐 Ouvert à')).toBeVisible();
    await expect(page.getByRole('checkbox', { name: '👥 Humains' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🤖 Autres Locrits' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: '📧 Invitations' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🌐 Internet' })).not.toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🏢 Plateforme' })).not.toBeChecked();

    // Check "Accès aux données" section
    await expect(page.getByText('📊 Accès aux données')).toBeVisible();
    await expect(page.getByRole('checkbox', { name: '📝 Logs système' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🧠 Mémoire rapide' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🗄️ Mémoire complète' })).not.toBeChecked();
    await expect(page.getByRole('checkbox', { name: '🤖 Informations LLM' })).toBeChecked();

    // Check action buttons
    await expect(page.getByRole('link', { name: 'Annuler' })).toBeVisible();
    await expect(page.getByRole('button', { name: '✅ Créer le Locrit' })).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/create-locrit');

    // Try to submit with empty required fields
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click();

    // Check that form validation prevents submission
    // (This would need to be implemented in the actual form)
    const nameField = page.getByRole('textbox', { name: 'Nom du Locrit *' });
    await expect(nameField).toBeFocused(); // Or check for validation message
  });

  test('should allow filling and modifying form fields', async ({ page }) => {
    await page.goto('/create-locrit');

    // Fill in the form
    await page.getByRole('textbox', { name: 'Nom du Locrit *' }).fill('Test Locrit');
    await page.getByRole('textbox', { name: 'Description *' }).fill('Un locrit de test pour validation');
    await page.getByRole('textbox', { name: 'Modèle Ollama *' }).clear();
    await page.getByRole('textbox', { name: 'Modèle Ollama *' }).fill('mistral:7b');
    await page.getByRole('textbox', { name: 'Adresse publique' }).fill('test.localhost.run');

    // Verify values were set
    await expect(page.getByRole('textbox', { name: 'Nom du Locrit *' })).toHaveValue('Test Locrit');
    await expect(page.getByRole('textbox', { name: 'Description *' })).toHaveValue('Un locrit de test pour validation');
    await expect(page.getByRole('textbox', { name: 'Modèle Ollama *' })).toHaveValue('mistral:7b');
    await expect(page.getByRole('textbox', { name: 'Adresse publique' })).toHaveValue('test.localhost.run');

    // Test checkbox interactions
    await page.getByRole('checkbox', { name: '🌐 Internet' }).check();
    await expect(page.getByRole('checkbox', { name: '🌐 Internet' })).toBeChecked();

    await page.getByRole('checkbox', { name: '👥 Humains' }).uncheck();
    await expect(page.getByRole('checkbox', { name: '👥 Humains' })).not.toBeChecked();

    await page.getByRole('checkbox', { name: '🗄️ Mémoire complète' }).check();
    await expect(page.getByRole('checkbox', { name: '🗄️ Mémoire complète' })).toBeChecked();
  });

  test('should navigate back to locrits list', async ({ page }) => {
    await page.goto('/create-locrit');

    // Test back button navigation
    await page.getByRole('link', { name: '← Retour à la liste' }).click();
    await expect(page).toHaveURL('/my-locrits');

    // Test cancel button navigation
    await page.goto('/create-locrit');
    await page.getByRole('link', { name: 'Annuler' }).click();
    await expect(page).toHaveURL('/my-locrits');
  });

  test('should have proper field descriptions and help text', async ({ page }) => {
    await page.goto('/create-locrit');

    // Check help text for various fields
    await expect(page.getByText('Le nom doit être unique et servira d\'identifiant.')).toBeVisible();
    await expect(page.getByText('Une description claire aide à comprendre le rôle du Locrit.')).toBeVisible();
    await expect(page.getByText('Le modèle Ollama à utiliser (ex: llama3.2, codellama, mistral...).')).toBeVisible();
    await expect(page.getByText('Optionnel. Adresse pour accéder au Locrit depuis l\'extérieur.')).toBeVisible();

    // Check permission descriptions
    await expect(page.getByText('Permettre aux utilisateurs humains de se connecter')).toBeVisible();
    await expect(page.getByText('Permettre aux autres Locrits de se connecter')).toBeVisible();
    await expect(page.getByText('Accepter les invitations externes')).toBeVisible();
    await expect(page.getByText('Accès autonome à Internet (expérimental)')).toBeVisible();
    await expect(page.getByText('Interactions avec la plateforme Locrit')).toBeVisible();

    // Check data access descriptions
    await expect(page.getByText('Accès aux journaux d\'activité du système')).toBeVisible();
    await expect(page.getByText('Accès à la mémoire de conversation récente')).toBeVisible();
    await expect(page.getByText('Accès à toute la mémoire historique (sensible)')).toBeVisible();
    await expect(page.getByText('Accès aux métadonnées du modèle de langage')).toBeVisible();
  });
});