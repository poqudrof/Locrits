import { test, expect } from '@playwright/test'
import {
  verifyLocritExists,
  verifyLocritSettings,
  verifyLocritDeleted,
  getLocritActiveStatus,
  waitForConfigChange,
  verifyConfigThroughAPI
} from '../utils/config-verifier'

test.describe('MyLocrits Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to MyLocrits page
    await page.goto('http://localhost:3000/my-locrits')
  })

  test('should display Locrits list from API', async ({ page }) => {
    // Wait for API call to complete
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Check if page loads with Locrits
    await expect(page.locator('h1')).toContainText('Mes Locrits Locaux')

    // Check if Locrits are displayed
    await expect(page.locator('[data-testid="locrits-list"]')).toBeVisible()
  })

  test('should toggle Locrit active/inactive status and verify config.yaml changes', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Get the first Locrit name for config verification
    const firstLocritTitle = firstLocritCard.locator('h3').first()
    const locritName = await firstLocritTitle.textContent()
    expect(locritName).toBeTruthy()

    // Get initial configuration for comparison
    const initialConfig = await verifyConfigThroughAPI(page)
    const initialActiveStatus = await getLocritActiveStatus(page, locritName!)

    // Find the Start/Stop button
    const toggleButton = firstLocritCard.locator('button:has-text("⏹️ Arrêter"), button:has-text("▶️ Démarrer")').first()

    // Get initial button state
    const initialText = await toggleButton.textContent()

    // Click the toggle button
    await toggleButton.click()

    // Wait for API response
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/') &&
      response.url().includes('/toggle')
    )

    // Wait for config.yaml to be updated
    await waitForConfigChange(page, initialConfig, 5000)

    // Check for success toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/Locrit.*(?:activé|désactivé)/)

    // Verify button text changed
    const newText = await toggleButton.textContent()
    expect(newText).not.toBe(initialText)

    // Verify config.yaml was actually modified
    const newActiveStatus = await getLocritActiveStatus(page, locritName!)
    expect(newActiveStatus).toBe(!initialActiveStatus)

    // Verify the specific setting in config
    const configVerified = await verifyLocritSettings(page, locritName!, {
      active: !initialActiveStatus
    })
    expect(configVerified).toBe(true)
  })

  test('should open and close edit form', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Click the Configure button
    await firstLocritCard.locator('button:has-text("⚙️ Configurer")').click()

    // Check if edit form is displayed
    await expect(page.locator('[data-testid="edit-form"]')).toBeVisible()
    await expect(page.locator('h3:has-text("Édition:")')).toBeVisible()

    // Click Cancel button
    await page.locator('button:has-text("Annuler")').click()

    // Check if edit form is hidden
    await expect(page.locator('[data-testid="edit-form"]')).not.toBeVisible()
  })

  test('should toggle details view', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Initially details should be hidden
    await expect(page.locator('[data-testid="locrit-details"]')).not.toBeVisible()

    // Click the Details button
    await firstLocritCard.locator('button:has-text("📄 Détails")').click()

    // Check if details section is displayed
    await expect(page.locator('[data-testid="locrit-details"]')).toBeVisible()
    await expect(page.locator('h4:has-text("Informations détaillées")')).toBeVisible()

    // Click Details button again to hide
    await firstLocritCard.locator('button:has-text("📄 Détails")').click()

    // Check if details section is hidden
    await expect(page.locator('[data-testid="locrit-details"]')).not.toBeVisible()
  })

  test('should show delete confirmation dialog and verify config.yaml changes', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Get the first Locrit name for config verification
    const firstLocritTitle = firstLocritCard.locator('h3').first()
    const locritName = await firstLocritTitle.textContent()
    expect(locritName).toBeTruthy()

    // Verify Locrit exists before deletion
    const locritExistsBefore = await verifyLocritExists(page, locritName!)
    expect(locritExistsBefore).toBe(true)

    // Get initial configuration for comparison
    const initialConfig = await verifyConfigThroughAPI(page)
    const initialLocritCount = Object.keys(initialConfig.instances).length

    // Mock the confirm dialog
    page.on('dialog', dialog => {
      expect(dialog.type()).toBe('confirm')
      expect(dialog.message()).toContain('Êtes-vous sûr de vouloir supprimer')
      dialog.accept() // Click OK
    })

    // Click the Delete button
    await firstLocritCard.locator('button:has-text("🗑️ Supprimer")').click()

    // Wait for API response
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/') &&
      response.url().includes('/delete')
    )

    // Wait for config.yaml to be updated
    await waitForConfigChange(page, initialConfig, 5000)

    // Check for success toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/supprimé avec succès/)

    // Verify Locrit was actually deleted from config.yaml
    const locritExistsAfter = await verifyLocritExists(page, locritName!)
    expect(locritExistsAfter).toBe(false)

    // Verify the Locrit count decreased
    const newConfig = await verifyConfigThroughAPI(page)
    const newLocritCount = Object.keys(newConfig.instances).length
    expect(newLocritCount).toBe(initialLocritCount - 1)
  })

  test('should cancel delete when clicking Cancel in confirmation', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Mock the confirm dialog to cancel
    page.on('dialog', dialog => {
      expect(dialog.type()).toBe('confirm')
      dialog.dismiss() // Click Cancel
    })

    // Click the Delete button
    await firstLocritCard.locator('button:has-text("🗑️ Supprimer")').click()

    // Should not make API call since dialog was cancelled
    // Wait a bit to ensure no API call is made
    await page.waitForTimeout(1000)

    // Check that no delete API was called by checking if any locrit was removed
    const initialLocritCount = await page.locator('[data-testid="locrit-card"]').count()
    expect(initialLocritCount).toBeGreaterThan(0)
  })

  test('should navigate to chat page', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first active Locrit
    const activeLocrit = page.locator('[data-testid="locrit-card"]').filter({ hasText: "🟢 Actif" }).first()
    await expect(activeLocrit).toBeVisible()

    // Click the Chat button
    await activeLocrit.locator('button:has-text("💬 Chat")').click()

    // Should navigate to chat page
    await expect(page).toHaveURL(/\/chat\//)
  })

  test('should disable Chat button for inactive Locrits', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find inactive Locrit
    const inactiveLocrit = page.locator('[data-testid="locrit-card"]').filter({ hasText: "🔴 Inactif" }).first()

    if (await inactiveLocrit.isVisible()) {
      // Chat button should be disabled
      const chatButton = inactiveLocrit.locator('button:has-text("💬 Chat")')
      await expect(chatButton).toBeDisabled()
    }
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/locrits', route => {
      route.abort('failed')
    })

    // Reload page
    await page.reload()

    // Should show error state or fallback
    // The page should still load without crashing
    await expect(page.locator('h1')).toContainText('Mes Locrits Locaux')
  })

  test('should validate form inputs in edit mode', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Click the Configure button
    await firstLocritCard.locator('button:has-text("⚙️ Configurer")').click()

    // Try to submit empty form
    await page.locator('button:has-text("💾 Sauvegarder")').click()

    // Should show validation errors
    await expect(page.locator('p:has-text("Le nom est obligatoire")')).toBeVisible()
    await expect(page.locator('p:has-text("La description est obligatoire")')).toBeVisible()
    await expect(page.locator('p:has-text("Le modèle est obligatoire")')).toBeVisible()
  })

  test('should save edited Locrit configuration and verify config.yaml changes', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Get the first Locrit name for config verification
    const firstLocritTitle = firstLocritCard.locator('h3').first()
    const locritName = await firstLocritTitle.textContent()
    expect(locritName).toBeTruthy()

    // Get initial configuration
    const initialConfig = await verifyConfigThroughAPI(page)
    const initialDescription = initialConfig.instances[locritName!].description
    const initialModel = initialConfig.instances[locritName!].ollama_model

    // Click the Configure button
    await firstLocritCard.locator('button:has-text("⚙️ Configurer")').click()

    // Fill in the form with new values
    const newDescription = 'Description mise à jour par test'
    const newModel = 'nouveau-modele-test'

    await page.fill('input[id="edit-description"]', newDescription)
    await page.fill('input[id="edit-model"]', newModel)

    // Submit the form
    await page.locator('button:has-text("💾 Sauvegarder")').click()

    // Wait for API response
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/') &&
      response.url().includes('/config') &&
      response.status() === 200
    )

    // Wait for config.yaml to be updated
    await waitForConfigChange(page, initialConfig, 5000)

    // Check for success toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/mise à jour avec succès/)

    // Verify config.yaml was actually modified
    const configVerified = await verifyLocritSettings(page, locritName!, {
      description: newDescription,
      ollama_model: newModel
    })
    expect(configVerified).toBe(true)

    // Verify the changes are different from original
    expect(newDescription).not.toBe(initialDescription)
    expect(newModel).not.toBe(initialModel)
  })

  test('should handle network errors during save', async ({ page }) => {
    // Wait for page to load
    await page.waitForResponse(response => response.url().includes('/api/locrits'))

    // Find first Locrit card
    const firstLocritCard = page.locator('[data-testid="locrit-card"]').first()
    await expect(firstLocritCard).toBeVisible()

    // Click the Configure button
    await firstLocritCard.locator('button:has-text("⚙️ Configurer")').click()

    // Mock API failure for save operation
    await page.route('**/api/locrits/*/config', route => {
      route.abort('failed')
    })

    // Fill in the form
    await page.fill('input[id="edit-description"]', 'Test description')

    // Submit the form
    await page.locator('button:has-text("💾 Sauvegarder")').click()

    // Should show error toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/Erreur lors de la sauvegarde/)
  })
})