import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const navigationItems = [
  {
    title: 'Tableau de bord',
    href: '/dashboard',
    icon: '🏠',
    description: 'Vue d\'ensemble des Locrits'
  },
  {
    title: 'Mes Locrits Locaux',
    href: '/my-locrits',
    icon: '🏠',
    description: 'Gestion des Locrits locaux'
  },
  {
    title: 'Créer Nouveau Locrit',
    href: '/create-locrit',
    icon: '➕',
    description: 'Interface de création'
  },
  {
    title: 'Paramètres Application',
    href: '/settings',
    icon: '⚙️',
    description: 'Configuration globale'
  }
]

export default function Navigation() {
  const location = useLocation()

  return (
    <aside className="hidden w-64 flex-col border-r bg-background md:flex">
      <div className="flex-1 overflow-auto py-6">
        <nav className="grid gap-2 px-4">
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.href

            return (
              <Link key={item.href} to={item.href}>
                <Button
                  variant={isActive ? 'secondary' : 'ghost'}
                  className={cn(
                    'w-full justify-start text-left',
                    isActive && 'bg-secondary'
                  )}
                >
                  <span className="mr-3 text-lg">{item.icon}</span>
                  <div className="flex flex-col items-start">
                    <span className="text-sm font-medium">{item.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {item.description}
                    </span>
                  </div>
                </Button>
              </Link>
            )
          })}
        </nav>

        {/* Additional sections */}
        <div className="mt-8 px-4">
          <h3 className="mb-2 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Modes de fonctionnement
          </h3>
          <div className="space-y-1">
            <Button variant="ghost" className="w-full justify-start" disabled>
              <span className="mr-3">👥</span>
              <div className="flex flex-col items-start">
                <span className="text-sm">Locrits Amis En ligne</span>
                <Badge variant="secondary" className="text-xs">Bientôt</Badge>
              </div>
            </Button>
            <Button variant="ghost" className="w-full justify-start" disabled>
              <span className="mr-3">🔍</span>
              <div className="flex flex-col items-start">
                <span className="text-sm">Recherche Internet</span>
                <Badge variant="secondary" className="text-xs">Bientôt</Badge>
              </div>
            </Button>
            <Button variant="ghost" className="w-full justify-start" disabled>
              <span className="mr-3">🧠</span>
              <div className="flex flex-col items-start">
                <span className="text-sm">Mémoire Sémantique</span>
                <Badge variant="secondary" className="text-xs">Bientôt</Badge>
              </div>
            </Button>
          </div>
        </div>
      </div>
    </aside>
  )
}