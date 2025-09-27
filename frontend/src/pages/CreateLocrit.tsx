import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'

const formSchema = z.object({
  name: z.string().min(1, 'Le nom est obligatoire').max(50, 'Le nom est trop long'),
  description: z.string().min(1, 'La description est obligatoire'),
  model: z.string().min(1, 'Le modèle est obligatoire'),
  publicAddress: z.string().optional(),
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

type FormData = z.infer<typeof formSchema>

export default function CreateLocrit() {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      description: '',
      model: 'llama3.2',
      publicAddress: '',
      humans: true,
      locrits: true,
      invitations: true,
      internet: false,
      platform: false,
      logs: true,
      quickMemory: true,
      fullMemory: false,
      llmInfo: true,
    }
  })

  const onSubmit = async (data: FormData) => {
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000/api/create-locrit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: data.name,
          description: data.description,
          model: data.model,
          public_address: data.publicAddress || '',
          humans: data.humans,
          locrits: data.locrits,
          invitations: data.invitations,
          internet: data.internet,
          platform: data.platform,
          logs: data.logs,
          quick_memory: data.quickMemory,
          full_memory: data.fullMemory,
          llm_info: data.llmInfo,
        })
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          toast.success(result.message)
          navigate('/my-locrits')
        } else {
          throw new Error(result.error || 'Failed to create Locrit')
        }
      } else {
        throw new Error('Failed to create Locrit')
      }
    } catch (error) {
      toast.error('Erreur lors de la création du Locrit')
      console.error('Error creating Locrit:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">➕ Créer un nouveau Locrit</h1>
          <p className="text-muted-foreground">
            Configurez votre nouveau Locrit avec ses paramètres d'accès
          </p>
        </div>
        <Link to="/my-locrits">
          <Button variant="outline">
            ← Retour à la liste
          </Button>
        </Link>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>📝 Informations générales</CardTitle>
            <CardDescription>
              Définissez les informations de base de votre Locrit
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nom du Locrit *</Label>
              <Input
                id="name"
                placeholder="Ex: Pixie Assistant, Bob Technique..."
                {...register('name')}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Le nom doit être unique et servira d'identifiant.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <textarea
                id="description"
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Décrivez le rôle et les capacités de ce Locrit..."
                {...register('description')}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description.message}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Une description claire aide à comprendre le rôle du Locrit.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">Modèle Ollama *</Label>
              <Input
                id="model"
                placeholder="llama3.2"
                {...register('model')}
              />
              {errors.model && (
                <p className="text-sm text-destructive">{errors.model.message}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Le modèle Ollama à utiliser (ex: llama3.2, codellama, mistral...).
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="publicAddress">Adresse publique</Label>
              <Input
                id="publicAddress"
                placeholder="mon-locrit.localhost.run"
                {...register('publicAddress')}
              />
              <p className="text-sm text-muted-foreground">
                Optionnel. Adresse pour accéder au Locrit depuis l'extérieur.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Access Permissions */}
        <Card>
          <CardHeader>
            <CardTitle>🔐 Ouvert à</CardTitle>
            <CardDescription>
              Qui peut se connecter à ce Locrit ?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="humans"
                className="rounded border-input"
                {...register('humans')}
              />
              <Label htmlFor="humans" className="flex items-center space-x-2">
                <span>👥 Humains</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Permettre aux utilisateurs humains de se connecter
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="locrits"
                className="rounded border-input"
                {...register('locrits')}
              />
              <Label htmlFor="locrits" className="flex items-center space-x-2">
                <span>🤖 Autres Locrits</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Permettre aux autres Locrits de se connecter
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="invitations"
                className="rounded border-input"
                {...register('invitations')}
              />
              <Label htmlFor="invitations" className="flex items-center space-x-2">
                <span>📧 Invitations</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accepter les invitations externes
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="internet"
                className="rounded border-input"
                {...register('internet')}
              />
              <Label htmlFor="internet" className="flex items-center space-x-2">
                <span>🌐 Internet</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accès autonome à Internet (expérimental)
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="platform"
                className="rounded border-input"
                {...register('platform')}
              />
              <Label htmlFor="platform" className="flex items-center space-x-2">
                <span>🏢 Plateforme</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Interactions avec la plateforme Locrit
            </p>
          </CardContent>
        </Card>

        {/* Data Access */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Accès aux données</CardTitle>
            <CardDescription>
              Quelles données ce Locrit peut-il consulter ?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="logs"
                className="rounded border-input"
                {...register('logs')}
              />
              <Label htmlFor="logs" className="flex items-center space-x-2">
                <span>📝 Logs système</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accès aux journaux d'activité du système
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="quickMemory"
                className="rounded border-input"
                {...register('quickMemory')}
              />
              <Label htmlFor="quickMemory" className="flex items-center space-x-2">
                <span>🧠 Mémoire rapide</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accès à la mémoire de conversation récente
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="fullMemory"
                className="rounded border-input"
                {...register('fullMemory')}
              />
              <Label htmlFor="fullMemory" className="flex items-center space-x-2">
                <span>🗄️ Mémoire complète</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accès à toute la mémoire historique (sensible)
            </p>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="llmInfo"
                className="rounded border-input"
                {...register('llmInfo')}
              />
              <Label htmlFor="llmInfo" className="flex items-center space-x-2">
                <span>🤖 Informations LLM</span>
              </Label>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              Accès aux métadonnées du modèle de langage
            </p>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          <Link to="/my-locrits">
            <Button variant="outline" type="button">
              Annuler
            </Button>
          </Link>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? '⏳ Création en cours...' : '✅ Créer le Locrit'}
          </Button>
        </div>
      </form>
    </div>
  )
}