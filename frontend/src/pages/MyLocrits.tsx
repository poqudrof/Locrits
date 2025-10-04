import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { syncService, LocritSyncStatus } from '@/lib/syncService'
import { firebaseService, FirebaseLocrit } from '@/lib/firebaseService'

export default function MyLocrits() {
  const [locrits, setLocrits] = useState<any[]>([])
  const [publishedLocrits, setPublishedLocrits] = useState<FirebaseLocrit[]>([])
  const [locritSyncStatuses, setLocritSyncStatuses] = useState<Record<string, LocritSyncStatus>>({})
  const [syncingLocrits, setSyncingLocrits] = useState<Set<string>>(new Set())
  const [showDetails, setShowDetails] = useState<string | null>(null)

  // Load Locrits data from API
  const loadLocrits = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/locrits')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.locrits) {
          setLocrits(Object.entries(data.locrits.instances || []))
        }
      } else {
        console.warn('Failed to load Locrits configuration')
      }
    } catch (error) {
      console.error('Error loading Locrits configuration:', error)
    }
  }

  // Load sync statuses for all locrits
  const loadSyncStatuses = () => {
    const statuses = syncService.getLocritSyncStatuses()
    setLocritSyncStatuses(statuses)
  }

  // Load published Locrits from Firebase
  const loadPublishedLocrits = async () => {
    try {
      const published = await firebaseService.getPublishedLocrits()
      setPublishedLocrits(published)
    } catch (error) {
      console.error('Error loading published Locrits:', error)
    }
  }

  // Sync a specific locrit to the cloud
  const syncLocritToCloud = async (locritName: string, locritData: any) => {
    if (syncingLocrits.has(locritName)) return

    setSyncingLocrits(prev => new Set(prev).add(locritName))

    try {
      await syncService.syncLocritToFirebase(locritName, locritData)
      loadSyncStatuses() // Refresh sync statuses
      toast.success(`Locrit "${locritName}" synchronisé avec le cloud`)
    } catch (error) {
      toast.error(`Erreur lors de la synchronisation de "${locritName}"`)
      console.error('Sync error:', error)
    } finally {
      setSyncingLocrits(prev => {
        const newSet = new Set(prev)
        newSet.delete(locritName)
        return newSet
      })
    }
  }

  // Remove a locrit from cloud sync
  const unsyncLocritFromCloud = async (locritName: string) => {
    if (syncingLocrits.has(locritName)) return

    setSyncingLocrits(prev => new Set(prev).add(locritName))

    try {
      await syncService.unsyncLocritFromFirebase(locritName)
      loadSyncStatuses() // Refresh sync statuses
      toast.success(`Locrit "${locritName}" retiré de la synchronisation cloud`)
    } catch (error) {
      toast.error(`Erreur lors de la désynchronisation de "${locritName}"`)
      console.error('Unsync error:', error)
    } finally {
      setSyncingLocrits(prev => {
        const newSet = new Set(prev)
        newSet.delete(locritName)
        return newSet
      })
    }
  }

  // Load data on component mount
  useEffect(() => {
    loadLocrits()
    loadSyncStatuses()
    loadPublishedLocrits()
  }, [])

  const toggleLocritStatus = async (locritName: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          toast.success(result.message)
          // Reload the configuration
          await loadLocrits()
        } else {
          throw new Error(result.error || 'Failed to toggle status')
        }
      } else {
        throw new Error('Failed to toggle status')
      }
    } catch (error) {
      toast.error('Erreur lors du changement de statut')
      console.error('Error toggling Locrit status:', error)
    }
  }

  const deleteLocrit = async (locritName: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le Locrit "${locritName}" ? Cette action est irréversible.`)) {
      return
    }

    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          toast.success(`Locrit "${locritName}" supprimé avec succès`)
          // Reload the configuration
          await loadLocrits()
        } else {
          throw new Error(result.error || 'Failed to delete Locrit')
        }
      } else {
        throw new Error('Failed to delete Locrit')
      }
    } catch (error) {
      toast.error('Erreur lors de la suppression du Locrit')
      console.error('Error deleting Locrit:', error)
    }
  }

  const toggleDetails = (locritName: string) => {
    setShowDetails(showDetails === locritName ? null : locritName)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mes Locrits</h1>
          <p className="text-muted-foreground">
            Gérez vos Locrits locaux - Publiez-les sur le cloud pour la synchronisation
          </p>
        </div>
        <Link to="/create-locrit">
          <Button>
            ➕ Nouveau Locrit
          </Button>
        </Link>
      </div>

      {/* Locrits List */}
      {locrits.length > 0 ? (
        <div className="space-y-4" data-testid="locrits-list">
          {locrits.map(([locritName, settings]) => (
            <Card key={locritName} data-testid="locrit-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <span className="text-2xl">🤖</span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <CardTitle className="text-xl">{locritName}</CardTitle>
                        <Badge variant={settings.active ? 'default' : 'secondary'}>
                          {settings.active ? '🟢 Actif' : '🔴 Inactif'}
                        </Badge>
                        {locritSyncStatuses[locritName]?.synced && (
                          <Badge variant="outline" className="text-green-600 border-green-600">
                            ☁️ Synchronisé
                          </Badge>
                        )}
                      </div>
                      <CardDescription>{settings.description}</CardDescription>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                        <span>Modèle: <code>{settings.ollama_model}</code></span>
                        <span>Créé: {new Date(settings.created_at).toLocaleDateString()}</span>
                        {settings.public_address && (
                          <span>Adresse: <code>{settings.public_address}</code></span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link to={`/chat/${locritName}`}>
                      <Button variant="outline" disabled={!settings.active}>
                        💬 Chat
                      </Button>
                    </Link>
                    <Button
                      variant={settings.active ? 'secondary' : 'default'}
                      size="sm"
                      onClick={() => toggleLocritStatus(locritName)}
                    >
                      {settings.active ? '⏹️ Arrêter' : '▶️ Démarrer'}
                    </Button>
                    <Link to={`/my-locrits/${locritName}/settings`}>
                      <Button variant="ghost" size="sm">
                        ⚙️ Configurer
                      </Button>
                    </Link>
                    {settings.access_to?.full_memory && (
                      <Link to={`/my-locrits/${locritName}/memory`}>
                        <Button variant="ghost" size="sm">
                          🧠 Mémoire
                        </Button>
                      </Link>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => toggleDetails(locritName)}>
                      📄 Détails
                    </Button>

                    {/* Cloud sync buttons */}
                    {locritSyncStatuses[locritName]?.synced ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => unsyncLocritFromCloud(locritName)}
                        disabled={syncingLocrits.has(locritName)}
                        className="text-orange-600 border-orange-600 hover:bg-orange-50"
                      >
                        {syncingLocrits.has(locritName) ? '⏳' : '☁️'} Retirer du cloud
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => syncLocritToCloud(locritName, settings)}
                        disabled={syncingLocrits.has(locritName)}
                        className="text-green-600 border-green-600 hover:bg-green-50"
                      >
                        {syncingLocrits.has(locritName) ? '⏳' : '☁️'} Publier sur le cloud
                      </Button>
                    )}

                    <Button variant="destructive" size="sm" onClick={() => deleteLocrit(locritName)}>
                      🗑️ Supprimer
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Access permissions */}
                  <div>
                    <h4 className="font-medium mb-2">🔐 Ouvert à</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center space-x-2">
                        <span>{settings.open_to?.humans ? '✅' : '❌'}</span>
                        <span>👥 Humains</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.open_to?.locrits ? '✅' : '❌'}</span>
                        <span>🤖 Autres Locrits</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.open_to?.invitations ? '✅' : '❌'}</span>
                        <span>📧 Invitations</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.open_to?.internet ? '✅' : '❌'}</span>
                        <span>🌐 Internet</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.open_to?.platform ? '✅' : '❌'}</span>
                        <span>🏢 Plateforme</span>
                      </div>
                    </div>
                  </div>

                  {/* Data access */}
                  <div>
                    <h4 className="font-medium mb-2">📊 Accès aux données</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center space-x-2">
                        <span>{settings.access_to?.logs ? '✅' : '❌'}</span>
                        <span>📝 Logs</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.access_to?.quick_memory ? '✅' : '❌'}</span>
                        <span>🧠 Mémoire rapide</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.access_to?.full_memory ? '✅' : '❌'}</span>
                        <span>🗄️ Mémoire complète</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{settings.access_to?.llm_info ? '✅' : '❌'}</span>
                        <span>🤖 Infos LLM</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>

              {/* Expandable Details Section */}
              {showDetails === locritName && (
                <div className="border-t bg-muted/50 px-6 py-4" data-testid="locrit-details">
                  <h4 className="font-medium mb-3">📋 Informations détaillées</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-muted-foreground">Date de création:</span>
                      <div>{new Date(settings.created_at).toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Dernière mise à jour:</span>
                      <div>{new Date(settings.updated_at).toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Adresse publique:</span>
                      <div className="font-mono text-xs break-all">
                        {settings.public_address || 'Non configurée'}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Modèle Ollama:</span>
                      <div className="font-mono">{settings.ollama_model}</div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Statut:</span>
                      <div>
                        <Badge variant={settings.active ? 'default' : 'secondary'}>
                          {settings.active ? 'Actif' : 'Inactif'}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Permissions d'édition:</span>
                      <div>
                        <Badge variant={(settings.access_to?.logs && settings.access_to?.full_memory) ? 'default' : 'outline'}>
                          {(settings.access_to?.logs && settings.access_to?.full_memory) ? 'Activées' : 'Désactivées'}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Statut de synchronisation:</span>
                      <div className="space-y-1">
                        <Badge variant={locritSyncStatuses[locritName]?.synced ? 'default' : 'outline'}>
                          {locritSyncStatuses[locritName]?.synced ? '☁️ Synchronisé avec le cloud' : '💾 Local uniquement'}
                        </Badge>
                        {locritSyncStatuses[locritName]?.lastSync && (
                          <div className="text-xs text-muted-foreground">
                            Dernière sync: {new Date(locritSyncStatuses[locritName].lastSync!).toLocaleString()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Raw JSON data for debugging */}
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
                      🔧 Données techniques (JSON)
                    </summary>
                    <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-auto max-h-40">
                      {JSON.stringify(settings, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <span className="text-6xl mb-4 block">🏠</span>
            <h3 className="text-xl font-medium mb-2">Aucun Locrit configuré</h3>
            <p className="text-muted-foreground mb-6">
              Vous n'avez pas encore créé de Locrit. Commencez par en créer un !
            </p>
            <Link to="/create-locrit">
              <Button size="lg">
                ➕ Créer mon premier Locrit
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Published Locrits Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Locrits Publiés</h2>
            <p className="text-muted-foreground">
              Découvrez les Locrits publiés sur la plateforme par d'autres utilisateurs
            </p>
          </div>
        </div>

        {publishedLocrits.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {publishedLocrits.map((locrit) => (
              <Card key={locrit.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <span className="text-xl">🤖</span>
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{locrit.name}</CardTitle>
                      <CardDescription className="text-sm">{locrit.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Adresse publique:</span>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {locrit.publicAddress}
                      </code>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Statut:</span>
                      <Badge variant={locrit.isOnline ? 'default' : 'secondary'}>
                        {locrit.isOnline ? '🟢 En ligne' : '🔴 Hors ligne'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Créé:</span>
                      <span>{locrit.createdAt?.toLocaleDateString()}</span>
                    </div>
                    <div className="pt-2">
                      <Button className="w-full" size="sm">
                        🌐 Visiter le Locrit
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <span className="text-4xl mb-4 block">🌐</span>
              <h3 className="text-lg font-medium mb-2">Aucun Locrit publié</h3>
              <p className="text-muted-foreground">
                Aucun Locrit n'a encore été publié sur la plateforme publique.
                Publiez votre premier Locrit pour qu'il apparaisse ici !
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}