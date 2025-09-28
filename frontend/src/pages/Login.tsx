import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { authService, AuthUser } from '@/lib/auth'
import { syncService } from '@/lib/syncService'

// Login logic:  local login always on (everything saved to config.yaml)
// Login to Firebase for online sync (Google OAuth, or email/password).
// When logged in, data syncs from / to Firebase.

type SyncMode = 'local' | 'synced' | null

export default function Login() {
  const [isLoading, setIsLoading] = useState(false)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [syncMode, setSyncMode] = useState<SyncMode>('local') // Default to local
  const [isOnline, setIsOnline] = useState(false)
  const [syncStatus, setSyncStatus] = useState(syncService.getSyncStatus())
  const [isAuthInitializing, setIsAuthInitializing] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    let isMounted = true

    const initializeAuth = async () => {
      setIsAuthInitializing(true)

      try {
        // Wait for auth service to be initialized
        await authService.waitForAuthInitialization()

        if (isMounted) {
          const unsubscribe = authService.onAuthStateChange((user) => {
            if (isMounted) {
              setCurrentUser(user)
              setIsOnline(!!user)
              setSyncMode(user ? 'synced' : 'local')
              setSyncStatus(syncService.getSyncStatus())
              setIsAuthInitializing(false)
            }
          })

          return unsubscribe
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        if (isMounted) {
          setIsAuthInitializing(false)
        }
      }
    }

    const unsubscribePromise = initializeAuth()

    // Update sync status periodically
    const syncInterval = setInterval(() => {
      if (isMounted) {
        setSyncStatus(syncService.getSyncStatus())
      }
    }, 2000)

    return () => {
      isMounted = false
      clearInterval(syncInterval)
      unsubscribePromise.then(unsub => unsub?.())
    }
  }, [])

  const handleLocalMode = () => {
    // Local mode - always available, no authentication required
    setSyncMode('local')
    setIsOnline(false)
    // Don't auto-redirect, let user choose when to go to dashboard
  }

  const handleDisconnect = async () => {
    setIsLoading(true)
    try {
      await authService.signOutUser()
      setSyncMode('local')
      setIsOnline(false)
      setCurrentUser(null)
    } catch (error) {
      console.error('Disconnect failed:', error)
      alert('Disconnect failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleContinueToDashboard = () => {
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <span className="text-4xl">🏠</span>
          </div>
          <CardTitle className="text-2xl font-bold">Locrit</CardTitle>
          <CardDescription>
            Configuration de la synchronisation - Le mode local est activé par défaut
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {isAuthInitializing ? (
            <div className="flex items-center justify-center p-4">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
              <span className="text-sm text-muted-foreground">Chargement...</span>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-4">
                Pour configurer l'authentification Firebase et la synchronisation cloud,
                rendez-vous dans les paramètres.
              </p>
              <Button
                variant="outline"
                onClick={() => navigate('/settings')}
                disabled={isLoading}
              >
                ⚙️ Aller aux paramètres
              </Button>
            </div>
          )}
          {/* Show current sync status */}
          {isOnline && currentUser && (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    ✅ Synchronisation Firebase activée
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-300 mt-1">
                    Connecté: {currentUser.displayName || currentUser.email}
                  </p>
                </div>
                {syncStatus.inProgress && (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                    <span className="text-xs text-green-600 ml-2">Sync...</span>
                  </div>
                )}
              </div>
              <p className="text-xs text-green-600 dark:text-green-300 mt-2">
                📡 Les données se synchronisent automatiquement avec Firebase
              </p>
            </div>
          )}

          {syncMode === 'local' && (
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                💾 Mode local activé (par défaut)
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-300 mt-1">
                🔒 Toutes les données sont sauvegardées dans config.yaml
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-300 mt-1">
                📁 Fonctionne hors ligne - Aucune synchronisation cloud
              </p>
            </div>
          )}

          <div className="space-y-2">
            {syncMode === 'local' ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground text-center">
                  La synchronisation Firebase est disponible dans les paramètres
                </p>
              </div>
            ) : (
              <Button
                variant="destructive"
                className="w-full"
                onClick={handleDisconnect}
                disabled={isLoading}
              >
                {isLoading ? '⏳ Déconnexion...' : '🚪 Désactiver la synchronisation'}
              </Button>
            )}

            <Button
              variant="outline"
              className="w-full"
              onClick={handleLocalMode}
              disabled={isLoading}
            >
              💾 Mode local uniquement
            </Button>

            <Button
              className="w-full"
              onClick={handleContinueToDashboard}
              disabled={isLoading}
            >
              ⚡ Accéder au dashboard
            </Button>
          </div>
        </CardContent>

        <CardFooter>
          <div className="text-center text-xs text-muted-foreground w-full space-y-1">
            <p>
              💡 <strong>Mode local par défaut:</strong> Toutes les données sont automatiquement sauvegardées dans config.yaml
            </p>
            <p>
              🌐 <strong>Synchronisation Firebase:</strong> Activez pour synchroniser vos données avec le cloud
            </p>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}