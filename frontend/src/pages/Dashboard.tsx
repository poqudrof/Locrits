import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function Dashboard() {
  const navigate = useNavigate()
  const [locrits, setLocrits] = useState<any[]>([])

  // Load Locrits data from API
  const loadLocrits = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/locrits')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.locrits) {
          const locritsArray = Object.entries(data.locrits.instances || [])
          setLocrits(locritsArray.slice(0, 3)) // Show only first 3 for dashboard
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

  const handleConfigureLocrit = (locritName: string) => {
    // Navigate to MyLocrits page with query parameter to auto-open edit mode
    navigate(`/my-locrits?edit=${encodeURIComponent(locritName)}`)
  }

  // Mock data - replace with actual API calls
  const stats = {
    totalLocrits: 3,
    activeLocrits: 2,
    inactiveLocrits: 1
  }


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
          {locrits.length > 0 ? (
            <div className="space-y-4">
              {locrits.map(([locritName, settings]) => (
                <div key={locritName} className="flex items-center justify-between p-4 rounded-lg border">
                  <div className="flex items-center space-x-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <span className="text-xl">🤖</span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium">{locritName}</h3>
                        <Badge variant={settings.active ? 'default' : 'secondary'}>
                          {settings.active ? '🟢 Actif' : '🔴 Inactif'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {settings.description}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Modèle: {settings.ollama_model}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link to={`/chat/${locritName}`}>
                      <Button variant="outline" size="sm" disabled={!settings.active}>
                        💬 Chat
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleConfigureLocrit(locritName)}
                      title="Configurer ce Locrit"
                    >
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