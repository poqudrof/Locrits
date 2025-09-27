import { test, expect } from '@playwright/test'
import {
  verifyLocritExists,
  verifyLocritSettings,
  verifyConfigThroughAPI,
  waitForConfigChange,
  getLocritCount
} from '../utils/config-verifier'

test.describe('Create Locrit Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to Create Locrit page
    await page.goto('http://localhost:3000/create-locrit')
  })

  test('should display create locrit form with all required fields', async ({ page }) => {
    // Check main heading
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible()
    await expect(page.getByText('Configurez votre nouveau Locrit avec ses paramètres d\'accès')).toBeVisible()

    // Check form sections
    await expect(page.getByText('📝 Informations générales')).toBeVisible()
    await expect(page.getByText('🔐 Ouvert à')).toBeVisible()
    await expect(page.getByText('📊 Accès aux données')).toBeVisible()

    // Check required fields
    await expect(page.getByLabel('Nom du Locrit *')).toBeVisible()
    await expect(page.getByLabel('Description *')).toBeVisible()
    await expect(page.getByLabel('Modèle Ollama *')).toBeVisible()

    // Check permission checkboxes
    await expect(page.getByLabel('👥 Humains')).toBeVisible()
    await expect(page.getByLabel('🤖 Autres Locrits')).toBeVisible()
    await expect(page.getByLabel('📧 Invitations')).toBeVisible()
    await expect(page.getByLabel('🌐 Internet')).toBeVisible()
    await expect(page.getByLabel('🏢 Plateforme')).toBeVisible()
    await expect(page.getByLabel('📝 Logs système')).toBeVisible()
    await expect(page.getByLabel('🧠 Mémoire rapide')).toBeVisible()
    await expect(page.getByLabel('🗄️ Mémoire complète')).toBeVisible()
    await expect(page.getByLabel('🤖 Informations LLM')).toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Should show validation errors
    await expect(page.getByText('Le nom est obligatoire')).toBeVisible()
    await expect(page.getByText('La description est obligatoire')).toBeVisible()
    await expect(page.getByText('Le modèle est obligatoire')).toBeVisible()

    // Should not navigate away
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible()
  })

  test('should validate name length constraints', async ({ page }) => {
    // Test name too short
    const nameField = page.getByLabel('Nom du Locrit *')
    await nameField.fill('')
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()
    await expect(page.getByText('Le nom est obligatoire')).toBeVisible()

    // Test name too long (over 50 characters)
    const longName = 'a'.repeat(51)
    await nameField.fill(longName)
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()
    await expect(page.getByText('Le nom est trop long')).toBeVisible()
  })

  test('should create new Locrit and verify config.yaml changes', async ({ page }) => {
    // Get initial configuration
    const initialConfig = await verifyConfigThroughAPI(page)
    const initialLocritCount = Object.keys(initialConfig.instances).length

    // Fill in the form with valid data
    const testLocritName = `TestLocrit-${Date.now()}`
    const testDescription = 'Locrit de test créé par Playwright'
    const testModel = 'llama3.2'

    await page.getByLabel('Nom du Locrit *').fill(testLocritName)
    await page.getByLabel('Description *').fill(testDescription)
    await page.getByLabel('Modèle Ollama *').fill(testModel)
    await page.getByLabel('Adresse publique').fill('test.localhost.run')

    // Configure permissions
    await page.getByLabel('👥 Humains').check()
    await page.getByLabel('🤖 Autres Locrits').uncheck()
    await page.getByLabel('📧 Invitations').check()
    await page.getByLabel('🌐 Internet').uncheck()
    await page.getByLabel('🏢 Plateforme').uncheck()

    await page.getByLabel('📝 Logs système').check()
    await page.getByLabel('🧠 Mémoire rapide').check()
    await page.getByLabel('🗄️ Mémoire complète').uncheck()
    await page.getByLabel('🤖 Informations LLM').check()

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Wait for API response
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/create') &&
      response.status() === 200
    )

    // Wait for config.yaml to be updated
    await waitForConfigChange(page, initialConfig, 5000)

    // Check for success toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/créé avec succès/)

    // Verify navigation to MyLocrits page
    await expect(page).toHaveURL(/\/my-locrits/)

    // Verify Locrit was created in config.yaml
    const locritExists = await verifyLocritExists(page, testLocritName)
    expect(locritExists).toBe(true)

    // Verify Locrit has correct settings
    const configVerified = await verifyLocritSettings(page, testLocritName, {
      description: testDescription,
      ollama_model: testModel,
      active: false, // Should be inactive by default
      public_address: 'test.localhost.run',
      open_to: {
        humans: true,
        locrits: false,
        invitations: true,
        internet: false,
        platform: false
      },
      access_to: {
        logs: true,
        quick_memory: true,
        full_memory: false,
        llm_info: true
      }
    })
    expect(configVerified).toBe(true)

    // Verify total Locrit count increased
    const newLocritCount = await getLocritCount(page)
    expect(newLocritCount).toBe(initialLocritCount + 1)
  })

  test('should prevent creating Locrit with duplicate name', async ({ page }) => {
    // Get existing Locrit names
    const config = await verifyConfigThroughAPI(page)
    const existingLocrits = Object.keys(config.instances)

    if (existingLocrits.length === 0) {
      test.skip()
      return
    }

    const duplicateName = existingLocrits[0]

    // Fill form with duplicate name
    await page.getByLabel('Nom du Locrit *').fill(duplicateName)
    await page.getByLabel('Description *').fill('Test description')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Should show error message
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/existe déjà/)

    // Should not navigate away
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible()

    // Should not create duplicate in config
    const locritCountBefore = await getLocritCount(page)
    await page.waitForTimeout(1000) // Wait to ensure no async creation
    const locritCountAfter = await getLocritCount(page)
    expect(locritCountAfter).toBe(locritCountBefore)
  })

  test('should handle API errors during creation', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/locrits/create', route => {
      route.abort('failed')
    })

    // Fill in valid form data
    await page.getByLabel('Nom du Locrit *').fill('TestLocrit-Error')
    await page.getByLabel('Description *').fill('Test description')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Should show error toast
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/Erreur lors de la création/)

    // Should not navigate away
    await expect(page.getByRole('heading', { name: '➕ Créer un nouveau Locrit' })).toBeVisible()
  })

  test('should show loading state during form submission', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/locrits/create', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000))
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Locrit créé avec succès !',
          locrit: { name: 'TestLocrit', settings: {} }
        })
      })
    })

    // Fill in form data
    await page.getByLabel('Nom du Locrit *').fill('TestLocrit-Loading')
    await page.getByLabel('Description *').fill('Test description')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Click submit button
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Check loading state
    await expect(page.getByRole('button', { name: '⏳ Création en cours...' })).toBeVisible()
    await expect(page.getByRole('button', { name: '✅ Créer le Locrit' })).not.toBeVisible()

    // Wait for completion
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/créé avec succès/)
  })

  test('should navigate back to MyLocrits when clicking cancel', async ({ page }) => {
    // Click cancel button
    await page.getByRole('button', { name: 'Annuler' }).click()

    // Should navigate to MyLocrits page
    await expect(page).toHaveURL(/\/my-locrits/)
  })

  test('should navigate back to MyLocrits when clicking return button', async ({ page }) => {
    // Click return button in header
    await page.getByRole('button', { name: '← Retour à la liste' }).click()

    // Should navigate to MyLocrits page
    await expect(page).toHaveURL(/\/my-locrits/)
  })

  test('should handle network timeout during creation', async ({ page }) => {
    // Mock slow API that times out
    await page.route('**/api/locrits/create', async route => {
      await new Promise(resolve => setTimeout(resolve, 10000))
      route.abort('failed')
    })

    // Fill in form data
    await page.getByLabel('Nom du Locrit *').fill('TestLocrit-Timeout')
    await page.getByLabel('Description *').fill('Test description')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Wait for timeout and error
    await page.waitForTimeout(3000)

    // Should eventually show error
    await expect(page.locator('[data-sonner-toaster]')).toContainText(/Erreur lors de la création/)
  })

  test('should validate model field requirements', async ({ page }) => {
    // Fill name and description but leave model empty
    await page.getByLabel('Nom du Locrit *').fill('TestLocrit-Model')
    await page.getByLabel('Description *').fill('Test description')
    // Leave model field empty

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Should show model validation error
    await expect(page.getByText('Le modèle est obligatoire')).toBeVisible()
  })

  test('should validate description field requirements', async ({ page }) => {
    // Fill name and model but leave description empty
    await page.getByLabel('Nom du Locrit *').fill('TestLocrit-Desc')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')
    // Leave description field empty

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Should show description validation error
    await expect(page.getByText('La description est obligatoire')).toBeVisible()
  })

  test('should create Locrit with all permissions enabled', async ({ page }) => {
    // Get initial configuration
    const initialConfig = await verifyConfigThroughAPI(page)

    const testLocritName = `FullPerms-${Date.now()}`

    // Fill in basic information
    await page.getByLabel('Nom du Locrit *').fill(testLocritName)
    await page.getByLabel('Description *').fill('Locrit avec toutes les permissions')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Enable all permissions
    await page.getByLabel('👥 Humains').check()
    await page.getByLabel('🤖 Autres Locrits').check()
    await page.getByLabel('📧 Invitations').check()
    await page.getByLabel('🌐 Internet').check()
    await page.getByLabel('🏢 Plateforme').check()

    await page.getByLabel('📝 Logs système').check()
    await page.getByLabel('🧠 Mémoire rapide').check()
    await page.getByLabel('🗄️ Mémoire complète').check()
    await page.getByLabel('🤖 Informations LLM').check()

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Wait for API response and config update
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/create') &&
      response.status() === 200
    )
    await waitForConfigChange(page, initialConfig, 5000)

    // Verify all permissions are set correctly
    const configVerified = await verifyLocritSettings(page, testLocritName, {
      open_to: {
        humans: true,
        locrits: true,
        invitations: true,
        internet: true,
        platform: true
      },
      access_to: {
        logs: true,
        quick_memory: true,
        full_memory: true,
        llm_info: true
      }
    })
    expect(configVerified).toBe(true)
  })

  test('should create Locrit with minimal permissions', async ({ page }) => {
    // Get initial configuration
    const initialConfig = await verifyConfigThroughAPI(page)

    const testLocritName = `Minimal-${Date.now()}`

    // Fill in basic information
    await page.getByLabel('Nom du Locrit *').fill(testLocritName)
    await page.getByLabel('Description *').fill('Locrit avec permissions minimales')
    await page.getByLabel('Modèle Ollama *').fill('llama3.2')

    // Disable most permissions (keep only humans and basic memory)
    await page.getByLabel('👥 Humains').check()
    await page.getByLabel('🤖 Autres Locrits').uncheck()
    await page.getByLabel('📧 Invitations').uncheck()
    await page.getByLabel('🌐 Internet').uncheck()
    await page.getByLabel('🏢 Plateforme').uncheck()

    await page.getByLabel('📝 Logs système').uncheck()
    await page.getByLabel('🧠 Mémoire rapide').check()
    await page.getByLabel('🗄️ Mémoire complète').uncheck()
    await page.getByLabel('🤖 Informations LLM').uncheck()

    // Submit the form
    await page.getByRole('button', { name: '✅ Créer le Locrit' }).click()

    // Wait for API response and config update
    await page.waitForResponse(response =>
      response.url().includes('/api/locrits/create') &&
      response.status() === 200
    )
    await waitForConfigChange(page, initialConfig, 5000)

    // Verify minimal permissions are set correctly
    const configVerified = await verifyLocritSettings(page, testLocritName, {
      open_to: {
        humans: true,
        locrits: false,
        invitations: false,
        internet: false,
        platform: false
      },
      access_to: {
        logs: false,
        quick_memory: true,
        full_memory: false,
        llm_info: false
      }
    })
    expect(configVerified).toBe(true)
  })
})