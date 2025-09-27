import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function MyLocrits() {
  // Mock data - replace with actual API calls
  const locrits = [
    {
      name: 'Pixie Assistant',
      description: 'Assistant personnel intelligent et organisé',
      active: true,
      model: 'llama3.1:8b-instruct-q3_K_M',
      publicAddress: 'pixie.localhost.run',
      created: '2025-09-25',
      openTo: {
        humans: true,
        locrits: true,
        invitations: true,
        internet: false,
        platform: false
      },
      accessTo: {
        logs: true,
        quickMemory: true,
        fullMemory: false,
        llmInfo: true
      }
    },
    {
      name: 'Expert Technique',
      description: 'Spécialisé dans le développement web, programmation et architecture logicielle',
      active: true,
      model: 'codellama',
      publicAddress: 'expert-tech.localhost.run',
      created: '2025-09-24',
      openTo: {
        humans: true,
        locrits: false,
        invitations: false,
        internet: false,
        platform: false
      },
      accessTo: {
        logs: true,
        quickMemory: true,
        fullMemory: true,
        llmInfo: true
      }
    },
    {
      name: 'Analyste Data',
      description: 'Aide à l\'analyse de données, statistiques et visualisation',
      active: false,
      model: 'llama3.1',
      publicAddress: '',
      created: '2025-09-23',
      openTo: {
        humans: true,
        locrits: true,
        invitations: false,
        internet: false,
        platform: false
      },
      accessTo: {
        logs: false,
        quickMemory: true,
        fullMemory: false,
        llmInfo: false
      }
    }
  ]

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
        <div className="space-y-4">
          {locrits.map((locrit, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <span className="text-2xl">🤖</span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <CardTitle className="text-xl">{locrit.name}</CardTitle>
                        <Badge variant={locrit.active ? 'default' : 'secondary'}>
                          {locrit.active ? '🟢 Actif' : '🔴 Inactif'}
                        </Badge>
                      </div>
                      <CardDescription>{locrit.description}</CardDescription>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                        <span>Modèle: <code>{locrit.model}</code></span>
                        <span>Créé: {locrit.created}</span>
                        {locrit.publicAddress && (
                          <span>Adresse: <code>{locrit.publicAddress}</code></span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link to={`/chat/${locrit.name}`}>
                      <Button variant="outline" disabled={!locrit.active}>
                        💬 Chat
                      </Button>
                    </Link>
                    <Button
                      variant={locrit.active ? 'secondary' : 'default'}
                      size="sm"
                    >
                      {locrit.active ? '⏹️ Arrêter' : '▶️ Démarrer'}
                    </Button>
                    <Button variant="ghost" size="sm">
                      ⚙️ Configurer
                    </Button>
                    <Button variant="ghost" size="sm">
                      📄 Détails
                    </Button>
                    <Button variant="destructive" size="sm">
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
                        <span>{locrit.openTo.humans ? '✅' : '❌'}</span>
                        <span>👥 Humains</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.openTo.locrits ? '✅' : '❌'}</span>
                        <span>🤖 Autres Locrits</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.openTo.invitations ? '✅' : '❌'}</span>
                        <span>📧 Invitations</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.openTo.internet ? '✅' : '❌'}</span>
                        <span>🌐 Internet</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.openTo.platform ? '✅' : '❌'}</span>
                        <span>🏢 Plateforme</span>
                      </div>
                    </div>
                  </div>

                  {/* Data access */}
                  <div>
                    <h4 className="font-medium mb-2">📊 Accès aux données</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center space-x-2">
                        <span>{locrit.accessTo.logs ? '✅' : '❌'}</span>
                        <span>📝 Logs</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.accessTo.quickMemory ? '✅' : '❌'}</span>
                        <span>🧠 Mémoire rapide</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.accessTo.fullMemory ? '✅' : '❌'}</span>
                        <span>🗄️ Mémoire complète</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>{locrit.accessTo.llmInfo ? '✅' : '❌'}</span>
                        <span>🤖 Infos LLM</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
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