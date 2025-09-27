import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

const editFormSchema = z.object({
  name: z.string().min(1, 'Le nom est obligatoire').max(50, 'Le nom est trop long'),
  description: z.string().min(1, 'La description est obligatoire'),
  model: z.string().min(1, 'Le modèle est obligatoire'),
  publicAddress: z.string().optional(),
  active: z.boolean(),
  // Open to permissions
  humans: z.boolean(),
  locrits: z.boolean(),
  invitations: z.boolean(),
  internet: z.boolean(),
  platform: z.boolean(),
  // Access permissions
  logs: z.boolean(),
  quickMemory: z.boolean(),
  fullMemory: z.boolean(),
  llmInfo: z.boolean(),
})

type EditFormData = z.infer<typeof editFormSchema>

export default function MyLocrits() {
  const [searchParams] = useSearchParams()
  const [editingLocrit, setEditingLocrit] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [locrits, setLocrits] = useState<any[]>([])

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue
  } = useForm<EditFormData>({
    resolver: zodResolver(editFormSchema),
  })

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

  // Load data on component mount
  useEffect(() => {
    loadLocrits()
  }, [])

  // Handle auto-opening edit mode from query parameter
  useEffect(() => {
    const editParam = searchParams.get('edit')
    if (editParam && locrits.length > 0) {
      // Check if the Locrit exists
      const locritExists = locrits.some(([name]) => name === editParam)
      if (locritExists) {
        setEditingLocrit(editParam)
      }
    }
  }, [searchParams, locrits])

  const startEditing = (locritName: string) => {
    const locrit = locrits.find(([name]) => name === locritName)
    if (locrit) {
      const [name, settings] = locrit
      setEditingLocrit(locritName)

      // Reset form with current values
      reset({
        name,
        description: settings.description || '',
        model: settings.ollama_model || '',
        publicAddress: settings.public_address || '',
        active: settings.active || false,
        humans: settings.open_to?.humans || true,
        locrits: settings.open_to?.locrits || true,
        invitations: settings.open_to?.invitations || true,
        internet: settings.open_to?.internet || false,
        platform: settings.open_to?.platform || false,
        logs: settings.access_to?.logs || true,
        quickMemory: settings.access_to?.quick_memory || true,
        fullMemory: settings.access_to?.full_memory || false,
        llmInfo: settings.access_to?.llm_info || true,
      })
    }
  }

  const cancelEditing = () => {
    setEditingLocrit(null)
    reset()
  }

  const onSubmitEdit = async (data: EditFormData) => {
    if (!editingLocrit) return

    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${editingLocrit}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: data.description,
          ollama_model: data.model,
          public_address: data.publicAddress || '',
          active: data.active,
          open_to: {
            humans: data.humans,
            locrits: data.locrits,
            invitations: data.invitations,
            internet: data.internet,
            platform: data.platform,
          },
          access_to: {
            logs: data.logs,
            quick_memory: data.quickMemory,
            full_memory: data.fullMemory,
            llm_info: data.llmInfo,
          },
        })
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          toast.success('Configuration du Locrit mise à jour avec succès!')
          setEditingLocrit(null)
          reset()
          // Reload the configuration
          await loadLocrits()
        } else {
          throw new Error(result.error || 'Failed to save configuration')
        }
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde de la configuration')
      console.error('Error saving Locrit configuration:', error)
    } finally {
      setIsLoading(false)
    }
  }

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

  const [showDetails, setShowDetails] = useState<string | null>(null)

  const toggleDetails = (locritName: string) => {
    setShowDetails(showDetails === locritName ? null : locritName)
  }


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mes Locrits Locaux</h1>
          <p className="text-muted-foreground">
            Gérez vos Locrits créés localement
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
              {editingLocrit === locritName ? (
                <CardHeader>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium">Édition: {locritName}</h3>
                      <Button variant="outline" size="sm" onClick={cancelEditing}>
                        Annuler
                      </Button>
                    </div>

                    <form onSubmit={handleSubmit(onSubmitEdit)} className="space-y-4" data-testid="edit-form">
                      {/* Basic Information */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="edit-name">Nom du Locrit *</Label>
                          <Input
                            id="edit-name"
                            {...register('name')}
                            disabled
                            className="bg-muted"
                          />
                          {errors.name && (
                            <p className="text-sm text-destructive">{errors.name.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-model">Modèle Ollama *</Label>
                          <Input
                            id="edit-model"
                            {...register('model')}
                          />
                          {errors.model && (
                            <p className="text-sm text-destructive">{errors.model.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-description">Description *</Label>
                          <textarea
                            id="edit-description"
                            className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            {...register('description')}
                          />
                          {errors.description && (
                            <p className="text-sm text-destructive">{errors.description.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-publicAddress">Adresse publique</Label>
                          <Input
                            id="edit-publicAddress"
                            {...register('publicAddress')}
                          />
                        </div>
                      </div>

                      {/* Status */}
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="edit-active"
                          className="rounded border-input"
                          {...register('active')}
                        />
                        <Label htmlFor="edit-active">Actif</Label>
                      </div>

                      {/* Permissions sections */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Open to permissions */}
                        <div className="space-y-3">
                          <Label className="text-base font-medium">🔐 Ouvert à</Label>
                          <div className="space-y-2">
                            {['humans', 'locrits', 'invitations', 'internet', 'platform'].map((perm) => (
                              <div key={perm} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`edit-${perm}`}
                                  className="rounded border-input"
                                  {...register(perm as keyof EditFormData)}
                                />
                                <Label htmlFor={`edit-${perm}`} className="text-sm">
                                  {perm === 'humans' ? '👥 Humains' :
                                   perm === 'locrits' ? '🤖 Autres Locrits' :
                                   perm === 'invitations' ? '📧 Invitations' :
                                   perm === 'internet' ? '🌐 Internet' : '🏢 Plateforme'}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Access permissions */}
                        <div className="space-y-3">
                          <Label className="text-base font-medium">📊 Accès aux données</Label>
                          <div className="space-y-2">
                            {['logs', 'quickMemory', 'fullMemory', 'llmInfo'].map((perm) => (
                              <div key={perm} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`edit-${perm}`}
                                  className="rounded border-input"
                                  {...register(perm as keyof EditFormData)}
                                />
                                <Label htmlFor={`edit-${perm}`} className="text-sm">
                                  {perm === 'logs' ? '📝 Logs' :
                                   perm === 'quickMemory' ? '🧠 Mémoire rapide' :
                                   perm === 'fullMemory' ? '🗄️ Mémoire complète' : '🤖 Infos LLM'}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" type="button" onClick={cancelEditing}>
                          Annuler
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                          {isLoading ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
                        </Button>
                      </div>
                    </form>
                  </div>
                </CardHeader>
              ) : (
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
                      <Button variant="ghost" size="sm" onClick={() => startEditing(locritName)}>
                        ⚙️ Configurer
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => toggleDetails(locritName)}>
                        📄 Détails
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => deleteLocrit(locritName)}>
                        🗑️ Supprimer
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              )}

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
    </div>
  )
}