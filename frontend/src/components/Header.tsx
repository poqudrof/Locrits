import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTheme } from 'next-themes'
import { Menu, Moon, Sun, User, LogOut, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

export default function Header() {
  const { theme, setTheme } = useTheme()
  const [isOpen, setIsOpen] = useState(false)

  // Mock user data - replace with actual auth context
  const user = {
    name: 'Utilisateur Local',
    email: 'user@locrit.local'
  }

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Logo and brand */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu trigger */}
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64">
              <SheetHeader>
                <SheetTitle>Navigation</SheetTitle>
                <SheetDescription>Accédez aux différentes sections de Locrit</SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4">
                <Link
                  to="/dashboard"
                  className="block py-2 text-sm font-medium hover:text-primary"
                  onClick={() => setIsOpen(false)}
                >
                  🏠 Tableau de bord
                </Link>
                <Link
                  to="/my-locrits"
                  className="block py-2 text-sm font-medium hover:text-primary"
                  onClick={() => setIsOpen(false)}
                >
                  🏠 Mes Locrits Locaux
                </Link>
                <Link
                  to="/create-locrit"
                  className="block py-2 text-sm font-medium hover:text-primary"
                  onClick={() => setIsOpen(false)}
                >
                  ➕ Créer Nouveau Locrit
                </Link>
                <Link
                  to="/settings"
                  className="block py-2 text-sm font-medium hover:text-primary"
                  onClick={() => setIsOpen(false)}
                >
                  ⚙️ Paramètres Application
                </Link>
              </div>
            </SheetContent>
          </Sheet>

          <Link to="/dashboard" className="flex items-center space-x-2">
            <span className="text-2xl">🏠</span>
            <span className="text-xl font-bold">Locrit</span>
          </Link>
        </div>

        {/* Desktop navigation - hidden on mobile, shown on larger screens */}
        <nav className="hidden md:flex md:items-center md:space-x-6">
          <Link
            to="/dashboard"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            Tableau de bord
          </Link>
          <Link
            to="/my-locrits"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            Mes Locrits
          </Link>
          <Link
            to="/create-locrit"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            Créer Locrit
          </Link>
        </nav>

        {/* Right side actions */}
        <div className="flex items-center space-x-2">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* User dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <div className="flex flex-col space-y-1 p-2">
                <p className="text-sm font-medium leading-none">{user.name}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user.email}
                </p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/settings">
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Paramètres</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Déconnexion</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}