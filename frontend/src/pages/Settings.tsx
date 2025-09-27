import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface OllamaModel {
  name: string
  size: string
  modified: string
}

export default function Settings() {
  const [isLoading, setIsLoading] = useState(false)
  const [isTestingOllama, setIsTestingOllama] = useState(false)
  const [isSavingUrl, setIsSavingUrl] = useState(false)
  const [isSavingModel, setIsSavingModel] = useState(false)
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434')
  const [defaultModel, setDefaultModel] = useState('llama3.2')
  const [apiPort, setApiPort] = useState('8000')
  const [ollamaStatus, setOllamaStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown')
  const [availableModels, setAvailableModels] = useState<OllamaModel[]>([])
  const [locrits, setLocrits] = useState<any[]>([])
  const [isLoadingLocrits, setIsLoadingLocrits] = useState(false)
  const [editingLocrit, setEditingLocrit] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<any>({})

  // Load configuration and check Ollama status on component mount
  useEffect(() => {
    loadConfig()
    checkOllamaStatus()
    loadLocritsConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/config')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.config) {
          // Update state with actual server configuration
          setOllamaUrl(data.config.ollama?.base_url || 'http://localhost:11434')
          setDefaultModel(data.config.ollama?.default_model || 'llama3.2')
          setApiPort(data.config.network?.api_server?.port?.toString() || '8000')
          console.log('Configuration loaded:', data.config)
        }
      } else {
        console.warn('Failed to load configuration from server')
      }
    } catch (error) {
      console.error('Error loading configuration:', error)
    }
  }

  const checkOllamaStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ollama/status')
      if (response.ok) {
        const data = await response.json()
        setOllamaStatus(data.status === 'connected' ? 'connected' : 'disconnected')
      } else {
        setOllamaStatus('disconnected')
      }
    } catch (error) {
      setOllamaStatus('disconnected')
    }
  }

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ollama/models')
      if (response.ok) {
        const data = await response.json()
        setAvailableModels(data.models || [])
        toast.success(`Trouvé ${data.models?.length || 0} modèles disponibles`)
      } else {
        throw new Error('Failed to fetch models')
      }
    } catch (error) {
      toast.error('Erreur lors de la récupération des modèles')
      setAvailableModels([])
    }
  }

  const handleSave = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:5000/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ollama_url: ollamaUrl,
          default_model: defaultModel,
          api_port: apiPort
        })
      })

      if (response.ok) {
        toast.success('Configuration sauvegardée')
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde')
    } finally {
      setIsLoading(false)
    }
  }

  const saveOllamaUrl = async () => {
    setIsSavingUrl(true)
    try {
      const response = await fetch('http://localhost:5000/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ollama_url: ollamaUrl,
          default_model: defaultModel,
          api_port: apiPort
        })
      })

      if (response.ok) {
        toast.success('URL Ollama sauvegardée')
      } else {
        throw new Error('Failed to save Ollama URL')
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde de l\'URL')
    } finally {
      setIsSavingUrl(false)
    }
  }

  const saveDefaultModel = async () => {
    console.log('saveDefaultModel called with:', { defaultModel, ollamaUrl, apiPort })
    setIsSavingModel(true)
    try {
      const response = await fetch('http://localhost:5000/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ollama_url: ollamaUrl,
          default_model: defaultModel,
          api_port: apiPort
        })
      })

      console.log('Response status:', response.status)
      const responseData = await response.json()
      console.log('Response data:', responseData)

      if (response.ok) {
        toast.success('Modèle par défaut sauvegardé')
      } else {
        throw new Error('Failed to save default model')
      }
    } catch (error) {
      console.error('Error saving default model:', error)
      toast.error('Erreur lors de la sauvegarde du modèle')
    } finally {
      setIsSavingModel(false)
    }
  }

  const selectModel = (modelName: string) => {
    setDefaultModel(modelName)
    toast.info(`Modèle sélectionné: ${modelName}`)
  }

  const testOllamaConnection = async () => {
    setIsTestingOllama(true)
    try {
      const response = await fetch('http://localhost:5000/config/test-ollama', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ollama_url: ollamaUrl
        })
      })

      if (response.ok) {
        const data = await response.json()
        setOllamaStatus('connected')
        toast.success('Connexion Ollama réussie!')

        // Fetch available models after successful connection
        await fetchAvailableModels()
      } else {
        setOllamaStatus('disconnected')
        throw new Error('Connection test failed')
      }
    } catch (error) {
      setOllamaStatus('disconnected')
      toast.error('Connexion Ollama échouée')
    } finally {
      setIsTestingOllama(false)
    }
  }

  const loadLocritsConfig = async () => {
    setIsLoadingLocrits(true)
    try {
      const response = await fetch('http://localhost:5000/api/locrits')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.locrits) {
          setLocrits(data.locrits.instances || [])
        }
      } else {
        console.warn('Failed to load Locrits configuration')
      }
    } catch (error) {
      console.error('Error loading Locrits configuration:', error)
    } finally {
      setIsLoadingLocrits(false)
    }
  }

  const startEditingLocrit = (locritName: string) => {
    const locrit = locrits.find(l => l[0] === locritName)
    if (locrit) {
      setEditingLocrit(locritName)
      setEditForm({ ...locrit[1] })
    }
  }

  const cancelEditingLocrit = () => {
    setEditingLocrit(null)
    setEditForm({})
  }

  const saveLocritConfig = async (locritName: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editForm)
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          toast.success('Configuration du Locrit sauvegardée')
          setEditingLocrit(null)
          setEditForm({})
          // Reload the configuration
          await loadLocritsConfig()
        } else {
          throw new Error(data.error || 'Failed to save configuration')
        }
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde de la configuration')
      console.error('Error saving Locrit configuration:', error)
    }
  }

  const toggleLocritEdit = async (locritName: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${locritName}/toggle-edit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          toast.success(data.message)
          // Reload the configuration
          await loadLocritsConfig()
        } else {
          throw new Error(data.error || 'Failed to toggle edit permissions')
        }
      } else {
        throw new Error('Failed to toggle edit permissions')
      }
    } catch (error) {
      toast.error('Erreur lors de la modification des permissions')
      console.error('Error toggling edit permissions:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">⚙️ Paramètres Application</h1>
        <p className="text-muted-foreground">
          Configurez les paramètres globaux de l'application
        </p>
      </div>

      {/* Ollama Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>🤖 Configuration Ollama</CardTitle>
          <CardDescription>
            Paramètres de connexion au serveur Ollama
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ollama-url">URL du serveur Ollama</Label>
            <div className="flex space-x-2">
              <Input
                id="ollama-url"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                placeholder="http://localhost:11434"
              />
              <Button
                variant="outline"
                onClick={testOllamaConnection}
                disabled={isTestingOllama}
              >
                {isTestingOllama ? '⏳ Test...' : '🔍 Tester'}
              </Button>
              <Button
                onClick={saveOllamaUrl}
                disabled={isSavingUrl}
              >
                {isSavingUrl ? '⏳ Sauvegarde...' : '💾 Sauver'}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              URL complète du serveur Ollama (inclut le protocole et le port)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="default-model">Modèle par défaut</Label>
            <div className="flex space-x-2">
              <Input
                id="default-model"
                value={defaultModel}
                onChange={(e) => setDefaultModel(e.target.value)}
                placeholder="llama3.2"
              />
              <Button
                onClick={() => {
                  console.log('Button clicked!')
                  saveDefaultModel()
                }}
                disabled={isSavingModel}
              >
                {isSavingModel ? '⏳ Sauvegarde...' : '💾 Sauver'}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Modèle utilisé par défaut pour les nouveaux Locrits
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Available Models */}
      {availableModels.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>🤖 Modèles Ollama disponibles</CardTitle>
            <CardDescription>
              Liste des modèles installés sur le serveur Ollama
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableModels.map((model, index) => (
                <div
                  key={index}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-accent hover:border-accent-foreground ${
                    model.name === defaultModel ? 'bg-primary/10 border-primary' : ''
                  }`}
                  onClick={() => selectModel(model.name)}
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm">{model.name}</h4>
                    <div className="flex items-center space-x-1">
                      {model.name === defaultModel && (
                        <Badge variant="default" className="text-xs">
                          Défaut
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {model.size}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Modifié: {new Date(model.modified).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchAvailableModels}
                disabled={isTestingOllama}
              >
                🔄 Actualiser
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Network Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>🌐 Configuration Réseau</CardTitle>
          <CardDescription>
            Paramètres du serveur API et de la connectivité
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-port">Port API</Label>
            <Input
              id="api-port"
              value={apiPort}
              onChange={(e) => setApiPort(e.target.value)}
              placeholder="8000"
              type="number"
            />
            <p className="text-sm text-muted-foreground">
              Port d'écoute du serveur API
            </p>
          </div>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Statut du système</CardTitle>
          <CardDescription>
            État des services et composants
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col items-center p-4 border rounded-lg">
              <span className="text-2xl mb-2">🟢</span>
              <h4 className="font-medium">Interface Web</h4>
              <Badge variant="default">Opérationnelle</Badge>
            </div>
            <div className="flex flex-col items-center p-4 border rounded-lg">
              <span className="text-2xl mb-2">
                {ollamaStatus === 'connected' ? '🟢' : ollamaStatus === 'disconnected' ? '🔴' : '❓'}
              </span>
              <h4 className="font-medium">Serveur Ollama</h4>
              <Badge variant={ollamaStatus === 'connected' ? 'default' : ollamaStatus === 'disconnected' ? 'destructive' : 'secondary'}>
                {ollamaStatus === 'connected' ? 'Connecté' : ollamaStatus === 'disconnected' ? 'Déconnecté' : 'Inconnu'}
              </Badge>
            </div>
            <div className="flex flex-col items-center p-4 border rounded-lg">
              <span className="text-2xl mb-2">📁</span>
              <h4 className="font-medium">Configuration</h4>
              <Badge variant="outline">Prête</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Memory Configuration (Read-only) */}
      <Card>
        <CardHeader>
          <CardTitle>🧠 Configuration Mémoire</CardTitle>
          <CardDescription>
            Paramètres de stockage et de mémoire (lecture seule)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Base de données</Label>
            <Input
              value="data/locrit_memory.db"
              readOnly
              className="bg-muted"
            />
            <p className="text-sm text-muted-foreground">
              Chemin vers la base de données de mémoire (non modifiable via l'interface)
            </p>
          </div>

          <div className="space-y-2">
            <Label>Messages maximum</Label>
            <Input
              value="10000"
              readOnly
              className="bg-muted"
            />
            <p className="text-sm text-muted-foreground">
              Nombre maximum de messages en mémoire (non modifiable via l'interface)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Locrits Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>🤖⚙️ Configuration des Locrits</CardTitle>
          <CardDescription>
            Gérez les paramètres et permissions de vos Locrits
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingLocrits ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-muted-foreground">Chargement des Locrits...</div>
            </div>
          ) : locrits.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-muted-foreground">Aucun Locrit configuré</div>
            </div>
          ) : (
            <div className="space-y-4">
              {locrits.map(([locritName, settings]) => (
                <div key={locritName} className="border rounded-lg p-4">
                  {editingLocrit === locritName ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Édition: {locritName}</h4>
                        <Button variant="outline" size="sm" onClick={cancelEditingLocrit}>
                          Annuler
                        </Button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Description</Label>
                          <Input
                            value={editForm.description || ''}
                            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                            placeholder="Description du Locrit"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>Modèle Ollama</Label>
                          <Input
                            value={editForm.ollama_model || ''}
                            onChange={(e) => setEditForm({ ...editForm, ollama_model: e.target.value })}
                            placeholder="Nom du modèle"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>Adresse publique</Label>
                          <Input
                            value={editForm.public_address || ''}
                            onChange={(e) => setEditForm({ ...editForm, public_address: e.target.value })}
                            placeholder="Adresse publique (optionnel)"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>Statut</Label>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={`active-${locritName}`}
                              checked={editForm.active || false}
                              onChange={(e) => setEditForm({ ...editForm, active: e.target.checked })}
                              className="rounded"
                            />
                            <Label htmlFor={`active-${locritName}`}>
                              {editForm.active ? 'Actif' : 'Inactif'}
                            </Label>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Label>Permissions d'accès</Label>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {['logs', 'quick_memory', 'full_memory', 'llm_info'].map((perm) => (
                            <div key={perm} className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                id={`${perm}-${locritName}`}
                                checked={editForm.access_to?.[perm] || false}
                                onChange={(e) => setEditForm({
                                  ...editForm,
                                  access_to: {
                                    ...editForm.access_to,
                                    [perm]: e.target.checked
                                  }
                                })}
                                className="rounded"
                              />
                              <Label htmlFor={`${perm}-${locritName}`} className="text-sm">
                                {perm === 'logs' ? 'Logs' :
                                 perm === 'quick_memory' ? 'Mémoire rapide' :
                                 perm === 'full_memory' ? 'Mémoire complète' : 'Info LLM'}
                              </Label>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Label>Ouverture</Label>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {['humans', 'locrits', 'invitations', 'internet', 'platform'].map((target) => (
                            <div key={target} className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                id={`${target}-${locritName}`}
                                checked={editForm.open_to?.[target] || false}
                                onChange={(e) => setEditForm({
                                  ...editForm,
                                  open_to: {
                                    ...editForm.open_to,
                                    [target]: e.target.checked
                                  }
                                })}
                                className="rounded"
                              />
                              <Label htmlFor={`${target}-${locritName}`} className="text-sm">
                                {target === 'humans' ? 'Humains' :
                                 target === 'locrits' ? 'Locrits' :
                                 target === 'invitations' ? 'Invitations' :
                                 target === 'internet' ? 'Internet' : 'Plateforme'}
                              </Label>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={cancelEditingLocrit}>
                          Annuler
                        </Button>
                        <Button onClick={() => saveLocritConfig(locritName)}>
                          💾 Sauvegarder
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <h4 className="font-medium">{locritName}</h4>
                          <Badge variant={settings.active ? 'default' : 'secondary'}>
                            {settings.active ? 'Actif' : 'Inactif'}
                          </Badge>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleLocritEdit(locritName)}
                          >
                            {settings.access_to?.logs && settings.access_to?.full_memory ? '🔓' : '🔒'} Édition
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => startEditingLocrit(locritName)}
                          >
                            ✏️ Modifier
                          </Button>
                        </div>
                      </div>

                      <div className="text-sm text-muted-foreground mb-2">
                        {settings.description}
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                        <div>
                          <span className="font-medium">Modèle:</span> {settings.ollama_model}
                        </div>
                        <div>
                          <span className="font-medium">Adresse:</span> {settings.public_address || 'Non définie'}
                        </div>
                        <div>
                          <span className="font-medium">Accès logs:</span>
                          <Badge variant={settings.access_to?.logs ? 'default' : 'outline'} className="ml-1">
                            {settings.access_to?.logs ? 'Oui' : 'Non'}
                          </Badge>
                        </div>
                        <div>
                          <span className="font-medium">Mémoire complète:</span>
                          <Badge variant={settings.access_to?.full_memory ? 'default' : 'outline'} className="ml-1">
                            {settings.access_to?.full_memory ? 'Oui' : 'Non'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline">
          🔄 Valeurs par défaut
        </Button>
        <Button onClick={handleSave} disabled={isLoading}>
          {isLoading ? '⏳ Sauvegarde...' : '💾 Sauvegarder la configuration'}
        </Button>
      </div>
    </div>
  )
}