import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function Dashboard() {
  // Mock data - replace with actual API calls
  const stats = {
    totalLocrits: 3,
    activeLocrits: 2,
    inactiveLocrits: 1
  }

  const recentLocrits = [
    {
      name: 'Pixie Assistant',
      description: 'Assistant général pour les tâches quotidiennes',
      active: true,
      model: 'llama3.2'
    },
    {
      name: 'Expert Technique',
      description: 'Spécialisé dans le développement et la programmation',
      active: true,
      model: 'codellama'
    },
    {
      name: 'Analyste Data',
      description: 'Aide à l\'analyse de données et statistiques',
      active: false,
      model: 'llama3.1'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tableau de bord</h1>
          <p className="text-muted-foreground">
            Vue d'ensemble de vos Locrits et de leur activité
          </p>
        </div>
        <Link to="/create-locrit">
          <Button>
            ➕ Nouveau Locrit
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Locrits</CardTitle>
            <span className="text-2xl">🏠</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalLocrits}</div>
            <p className="text-xs text-muted-foreground">
              Locrits configurés
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Actifs</CardTitle>
            <span className="text-2xl">🟢</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.activeLocrits}</div>
            <p className="text-xs text-muted-foreground">
              En cours d'exécution
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inactifs</CardTitle>
            <span className="text-2xl">🔴</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.inactiveLocrits}</div>
            <p className="text-xs text-muted-foreground">
              Arrêtés
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Locrits */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Mes Locrits récents</CardTitle>
              <CardDescription>
                Activité récente de vos Locrits
              </CardDescription>
            </div>
            <Link to="/my-locrits">
              <Button variant="outline" size="sm">
                Voir tout
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {recentLocrits.length > 0 ? (
            <div className="space-y-4">
              {recentLocrits.map((locrit, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg border">
                  <div className="flex items-center space-x-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <span className="text-xl">🤖</span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium">{locrit.name}</h3>
                        <Badge variant={locrit.active ? 'default' : 'secondary'}>
                          {locrit.active ? '🟢 Actif' : '🔴 Inactif'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {locrit.description}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Modèle: {locrit.model}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link to={`/chat/${locrit.name}`}>
                      <Button variant="outline" size="sm" disabled={!locrit.active}>
                        💬 Chat
                      </Button>
                    </Link>
                    <Button variant="ghost" size="sm">
                      ⚙️
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <span className="text-4xl mb-4 block">🏠</span>
              <h3 className="text-lg font-medium mb-2">Aucun Locrit configuré</h3>
              <p className="text-muted-foreground mb-4">
                Commencez par créer votre premier Locrit !
              </p>
              <Link to="/create-locrit">
                <Button>
                  ➕ Créer mon premier Locrit
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>Statut du système</CardTitle>
          <CardDescription>
            État des services et composants
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Badge variant="default">
                <span className="mr-2 h-2 w-2 rounded-full bg-green-500"></span>
                🟢 Interface Web
              </Badge>
              <span className="text-sm text-muted-foreground">Opérationnelle</span>
            </div>
            <Link to="/settings">
              <Button variant="outline" size="sm">
                ⚙️ Configuration
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}