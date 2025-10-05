import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { toast } from 'sonner'

const editFormSchema = z.object({
  name: z.string().min(1, 'Le nom est obligatoire').max(50, 'Le nom est trop long'),
  description: z.string().min(1, 'La description est obligatoire'),
  model: z.string().min(1, 'Le modèle est obligatoire'),
  publicAddress: z.string().optional(),
  active: z.boolean(),
  memoryService: z.enum(['kuzu_graph', 'plaintext_file', 'basic_memory', 'lancedb_langchain', 'lancedb_mcp', 'disabled']).optional(),
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

export default function LocritSettings() {
  const { locritName } = useParams<{ locritName: string }>()
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [locritData, setLocritData] = useState<any>(null)
  const [memoryData, setMemoryData] = useState<any>(null)
  const [isLoadingMemory, setIsLoadingMemory] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedMemoryService, setSelectedMemoryService] = useState<string>('')
  const [showMemoryWarning, setShowMemoryWarning] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EditFormData>({
    resolver: zodResolver(editFormSchema),
  })

  // Load Locrit data
  const loadLocritData = async () => {
    if (!locritName) return

    try {
      const response = await fetch('http://localhost:5000/api/locrits')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.locrits?.instances) {
          const locrit = data.locrits.instances[locritName]
          if (locrit) {
            setLocritData(locrit)
            // Reset form with current values
            const memService = locrit.memory_service || 'plaintext_file'
            setSelectedMemoryService(memService)
            reset({
              name: locritName,
              description: locrit.description || '',
              model: locrit.ollama_model || '',
              publicAddress: locrit.public_address || '',
              active: locrit.active || false,
              memoryService: memService,
              humans: locrit.open_to?.humans || true,
              locrits: locrit.open_to?.locrits || true,
              invitations: locrit.open_to?.invitations || true,
              internet: locrit.open_to?.internet || false,
              platform: locrit.open_to?.platform || false,
              logs: locrit.access_to?.logs || true,
              quickMemory: locrit.access_to?.quick_memory || true,
              fullMemory: locrit.access_to?.full_memory || false,
              llmInfo: locrit.access_to?.llm_info || true,
            })
          } else {
            toast.error('Locrit non trouvé')
            navigate('/my-locrits')
          }
        }
      }
    } catch (error) {
      console.error('Error loading Locrit data:', error)
      toast.error('Erreur lors du chargement des données')
    }
  }

  // Load memory data
  const loadMemoryData = async () => {
    if (!locritName) return

    setIsLoadingMemory(true)
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/memory/summary`)
      if (response.ok) {
        const data = await response.json()
        setMemoryData(data)
      } else {
        const errorData = await response.json()
        if (response.status === 403) {
          setMemoryData({ error: 'Accès à la mémoire non autorisé' })
        } else {
          setMemoryData({ error: errorData.error || 'Erreur lors du chargement de la mémoire' })
        }
      }
    } catch (error) {
      setMemoryData({ error: 'Erreur de connexion' })
    } finally {
      setIsLoadingMemory(false)
    }
  }

  useEffect(() => {
    loadLocritData()
  }, [locritName])

  useEffect(() => {
    if (activeTab === 'memory') {
      loadMemoryData()
    }
  }, [activeTab, locritName])

  const onSubmitEdit = async (data: EditFormData) => {
    if (!locritName) return

    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/config`, {
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
          memory_service: data.memoryService,
        })
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          toast.success('Configuration du Locrit mise à jour avec succès!')
          await loadLocritData() // Reload data
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

  const toggleLocritStatus = async () => {
    if (!locritName) return

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
          await loadLocritData()
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

  if (!locritData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link to="/my-locrits">
            <Button variant="outline" size="sm">
              ← Retour
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Chargement...</h1>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/my-locrits">
            <Button variant="outline" size="sm">
              ← Retour
            </Button>
          </Link>
          <div className="flex items-center space-x-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{locritName}</h1>
              <div className="flex items-center space-x-2">
                <Badge variant={locritData.active ? 'default' : 'secondary'}>
                  {locritData.active ? '🟢 Actif' : '🔴 Inactif'}
                </Badge>
                <span className="text-muted-foreground">{locritData.description}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Link to={`/chat/${locritName}`}>
            <Button variant="outline" disabled={!locritData.active}>
              💬 Chat
            </Button>
          </Link>
          <Button
            variant={locritData.active ? 'secondary' : 'default'}
            onClick={toggleLocritStatus}
          >
            {locritData.active ? '⏹️ Arrêter' : '▶️ Démarrer'}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">📊 Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="configuration">⚙️ Configuration</TabsTrigger>
          <TabsTrigger value="memory">🧠 Mémoire</TabsTrigger>
          <TabsTrigger value="advanced">🔧 Avancé</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>ℹ️ Informations générales</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-muted-foreground">Modèle:</span>
                    <div className="font-mono">{locritData.ollama_model}</div>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">Statut:</span>
                    <div>
                      <Badge variant={locritData.active ? 'default' : 'secondary'}>
                        {locritData.active ? 'Actif' : 'Inactif'}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">Créé:</span>
                    <div>{new Date(locritData.created_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="font-medium text-muted-foreground">Modifié:</span>
                    <div>{new Date(locritData.updated_at).toLocaleString()}</div>
                  </div>
                </div>
                {locritData.public_address && (
                  <div>
                    <span className="font-medium text-muted-foreground">Adresse publique:</span>
                    <div className="font-mono text-xs break-all">{locritData.public_address}</div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>⚡ Actions rapides</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link to={`/chat/${locritName}`}>
                  <Button className="w-full" disabled={!locritData.active}>
                    💬 Commencer une conversation
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setActiveTab('memory')}
                  disabled={!locritData.access_to?.quick_memory && !locritData.access_to?.full_memory}
                >
                  🧠 Voir la mémoire
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setActiveTab('configuration')}
                >
                  ⚙️ Modifier la configuration
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Permissions Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>🔐 Ouvert à</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <span>{locritData.open_to?.humans ? '✅' : '❌'}</span>
                    <span>👥 Humains</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.open_to?.locrits ? '✅' : '❌'}</span>
                    <span>🤖 Autres Locrits</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.open_to?.invitations ? '✅' : '❌'}</span>
                    <span>📧 Invitations</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.open_to?.internet ? '✅' : '❌'}</span>
                    <span>🌐 Internet</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.open_to?.platform ? '✅' : '❌'}</span>
                    <span>🏢 Plateforme</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📊 Accès aux données</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <span>{locritData.access_to?.logs ? '✅' : '❌'}</span>
                    <span>📝 Logs</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.access_to?.quick_memory ? '✅' : '❌'}</span>
                    <span>🧠 Mémoire rapide</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.access_to?.full_memory ? '✅' : '❌'}</span>
                    <span>🗄️ Mémoire complète</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{locritData.access_to?.llm_info ? '✅' : '❌'}</span>
                    <span>🤖 Infos LLM</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>⚙️ Configuration du Locrit</CardTitle>
              <CardDescription>
                Modifiez les paramètres et permissions de votre Locrit
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmitEdit)} className="space-y-6">
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

                  <div className="space-y-2 md:col-span-2">
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

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="edit-memoryService">💾 Type de mémoire</Label>
                    <Select
                      value={selectedMemoryService}
                      onValueChange={(value) => {
                        if (value !== selectedMemoryService) {
                          setShowMemoryWarning(true)
                        }
                        setSelectedMemoryService(value)
                      }}
                    >
                      <SelectTrigger id="edit-memoryService">
                        <SelectValue placeholder="Choisir un type de mémoire" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="plaintext_file">📄 Fichiers texte (Recommandé)</SelectItem>
                        <SelectItem value="lancedb_langchain">⚡ LanceDB LangChain</SelectItem>
                        <SelectItem value="basic_memory">✨ Basic Memory (MCP)</SelectItem>
                        <SelectItem value="lancedb_mcp">🔌 LanceDB MCP</SelectItem>
                        <SelectItem value="kuzu_graph">🗄️ Base de données Kuzu</SelectItem>
                        <SelectItem value="disabled">❌ Désactivé</SelectItem>
                      </SelectContent>
                    </Select>

                    {showMemoryWarning && selectedMemoryService !== locritData?.memory_service && (
                      <Alert className="border-orange-500 bg-orange-50 dark:bg-orange-950/20">
                        <AlertDescription className="text-orange-800 dark:text-orange-200">
                          ⚠️ <strong>Attention :</strong> Changer le type de mémoire rendra les anciennes mémoires inaccessibles.
                          Les données ne seront pas supprimées mais ne seront plus utilisées par ce type de mémoire.
                          Cette action est réversible en revenant à l'ancien type de mémoire.
                        </AlertDescription>
                      </Alert>
                    )}
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
                  <Button variant="outline" type="button" onClick={() => setActiveTab('overview')}>
                    Annuler
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Memory Tab */}
        <TabsContent value="memory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>🧠 Mémoire du Locrit</CardTitle>
              <CardDescription>
                Vue d'ensemble de la mémoire et des conversations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingMemory ? (
                <div className="flex items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
                  <span>Chargement de la mémoire...</span>
                </div>
              ) : memoryData ? (
                <div className="space-y-6">
                  {/* Error state */}
                  {memoryData.error ? (
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                      <p className="text-sm font-medium text-red-800 dark:text-red-200">
                        ❌ {memoryData.error}
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Statistics */}
                      {memoryData.statistics && (
                        <div>
                          <h4 className="font-medium mb-3">📊 Statistiques</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="p-3 border rounded">
                              <div className="text-2xl font-bold">{memoryData.statistics.total_messages}</div>
                              <div className="text-xs text-muted-foreground">Messages</div>
                            </div>
                            <div className="p-3 border rounded">
                              <div className="text-2xl font-bold">{memoryData.statistics.total_sessions}</div>
                              <div className="text-xs text-muted-foreground">Sessions</div>
                            </div>
                            <div className="p-3 border rounded">
                              <div className="text-2xl font-bold">{memoryData.statistics.total_concepts}</div>
                              <div className="text-xs text-muted-foreground">Concepts</div>
                            </div>
                            <div className="p-3 border rounded">
                              <div className="text-2xl font-bold">{memoryData.statistics.total_users}</div>
                              <div className="text-xs text-muted-foreground">Utilisateurs</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Recent Messages */}
                      {memoryData.recent_messages && memoryData.recent_messages.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3">💬 Messages récents</h4>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {memoryData.recent_messages.map((message: any, index: number) => (
                              <div key={index} className="p-3 border rounded text-sm">
                                <div className="flex items-center justify-between mb-1">
                                  <Badge variant={message.role === 'user' ? 'default' : 'secondary'}>
                                    {message.role}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    {new Date(message.timestamp).toLocaleString()}
                                  </span>
                                </div>
                                <div className="text-muted-foreground">
                                  {message.content}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  Session: {message.session_id}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Sessions */}
                      {memoryData.sessions && memoryData.sessions.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3">🗂️ Sessions de conversation</h4>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {memoryData.sessions.map((session: any, index: number) => (
                              <div key={index} className="p-3 border rounded text-sm">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="font-medium">{session.id}</div>
                                    <div className="text-xs text-muted-foreground">
                                      Utilisateur: {session.user_id}
                                    </div>
                                  </div>
                                  <div className="text-xs text-muted-foreground">
                                    {new Date(session.created_at).toLocaleString()}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Top Concepts */}
                      {memoryData.top_concepts && memoryData.top_concepts.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3">🧩 Concepts principaux</h4>
                          <div className="flex flex-wrap gap-2">
                            {memoryData.top_concepts.map((concept: any, index: number) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {concept.name} ({concept.mentions})
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <div className="text-center p-8 text-muted-foreground">
                  Aucune donnée de mémoire disponible
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>🔧 Paramètres avancés</CardTitle>
              <CardDescription>
                Options avancées et données techniques
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Raw JSON data */}
              <div>
                <h4 className="font-medium mb-3">📋 Configuration JSON</h4>
                <pre className="p-3 bg-muted rounded-md text-xs overflow-auto max-h-96">
                  {JSON.stringify(locritData, null, 2)}
                </pre>
              </div>

              {/* Danger Zone */}
              <div className="border border-destructive/20 rounded-lg p-4">
                <h4 className="font-medium mb-3 text-destructive">⚠️ Zone dangereuse</h4>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Ces actions sont irréversibles. Procédez avec prudence.
                  </p>
                  <div className="flex space-x-2">
                    <Button variant="destructive" size="sm" onClick={() => {
                      if (confirm(`Êtes-vous sûr de vouloir supprimer le Locrit "${locritName}" ? Cette action est irréversible.`)) {
                        // Handle delete
                        navigate('/my-locrits')
                      }
                    }}>
                      🗑️ Supprimer le Locrit
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}