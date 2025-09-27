/**
 * Configuration verification utilities for end-to-end tests
 * These utilities help verify that backend operations actually modify config.yaml
 */

export interface LocritConfig {
  name: string
  description: string
  active: boolean
  ollama_model: string
  public_address: string
  open_to: {
    humans: boolean
    locrits: boolean
    invitations: boolean
    internet: boolean
    platform: boolean
  }
  access_to: {
    logs: boolean
    quick_memory: boolean
    full_memory: boolean
    llm_info: boolean
  }
  created_at: string
  updated_at: string
}

export interface ConfigData {
  locrits: {
    instances: Record<string, LocritConfig>
    default_settings: any
  }
  ollama: {
    base_url: string
    default_model: string
    timeout: number
  }
  network: {
    api_server: {
      port: number
      host: string
    }
  }
}

/**
 * Verify configuration changes by reading config.yaml through API
 * This approach works within the Playwright test environment
 */
export async function verifyConfigThroughAPI(page: any): Promise<ConfigData['locrits']> {
  const response = await page.request.get('http://localhost:5000/api/locrits')
  if (!response.ok()) {
    throw new Error(`Failed to fetch config: ${response.status()}`)
  }
  const data = await response.json()
  return data.locrits as ConfigData['locrits']
}

/**
 * Verify that a Locrit exists in the configuration
 */
export async function verifyLocritExists(page: any, locritName: string): Promise<boolean> {
  const config = await verifyConfigThroughAPI(page)
  return locritName in config.instances
}

/**
 * Verify that a Locrit has specific settings
 */
export async function verifyLocritSettings(
  page: any,
  locritName: string,
  expectedSettings: Partial<LocritConfig>
): Promise<boolean> {
  const config = await verifyConfigThroughAPI(page)

  if (!verifyLocritExists(page, locritName)) {
    throw new Error(`Locrit "${locritName}" does not exist`)
  }

  const actualSettings = config.instances[locritName]

  // Check each expected setting
  for (const [key, expectedValue] of Object.entries(expectedSettings)) {
    const actualValue = (actualSettings as any)[key]

    if (actualValue !== expectedValue) {
      console.error(`Setting "${key}" mismatch:`, {
        expected: expectedValue,
        actual: actualValue,
        locrit: locritName
      })
      return false
    }
  }

  return true
}

/**
 * Verify that a Locrit was deleted
 */
export async function verifyLocritDeleted(page: any, locritName: string): Promise<boolean> {
  const config = await verifyConfigThroughAPI(page)
  return !(locritName in config.instances)
}

/**
 * Get the current active status of a Locrit
 */
export async function getLocritActiveStatus(page: any, locritName: string): Promise<boolean> {
  const config = await verifyConfigThroughAPI(page)
  if (!verifyLocritExists(page, locritName)) {
    throw new Error(`Locrit "${locritName}" does not exist`)
  }
  return config.instances[locritName].active
}

/**
 * Wait for configuration change by polling the API
 */
export async function waitForConfigChange(
  page: any,
  initialConfig: ConfigData['locrits'],
  timeout: number = 5000
): Promise<ConfigData['locrits']> {
  const startTime = Date.now()

  while (Date.now() - startTime < timeout) {
    await page.waitForTimeout(100)

    try {
      const currentConfig = await verifyConfigThroughAPI(page)

      // Check if configuration has changed
      const initialLocrits = Object.keys(initialConfig.instances)
      const currentLocrits = Object.keys(currentConfig.instances)

      if (initialLocrits.length !== currentLocrits.length) {
        return currentConfig
      }

      // Check if any Locrit settings have changed
      for (const name of initialLocrits) {
        if (name in currentConfig.instances) {
          const initialSettings = initialConfig.instances[name]
          const currentSettings = currentConfig.instances[name]

          if (JSON.stringify(initialSettings) !== JSON.stringify(currentSettings)) {
            return currentConfig
          }
        }
      }
    } catch (error) {
      // Continue polling if API call fails
      continue
    }
  }

  throw new Error(`Configuration was not updated within ${timeout}ms`)
}

/**
 * Get all Locrit names from configuration
 */
export async function getAllLocritNames(page: any): Promise<string[]> {
  const config = await verifyConfigThroughAPI(page)
  return Object.keys(config.instances)
}

/**
 * Count total number of Locrits
 */
export async function getLocritCount(page: any): Promise<number> {
  const names = await getAllLocritNames(page)
  return names.length
}

/**
 * Get count of active Locrits
 */
export async function getActiveLocritCount(page: any): Promise<number> {
  const config = await verifyConfigThroughAPI(page)
  return Object.values(config.instances).filter(locrit => locrit.active).length
}

/**
 * Get count of inactive Locrits
 */
export async function getInactiveLocritCount(page: any): Promise<number> {
  const config = await verifyConfigThroughAPI(page)
  return Object.values(config.instances).filter(locrit => !locrit.active).length
}
