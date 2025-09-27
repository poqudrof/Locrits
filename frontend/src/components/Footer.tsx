import { Badge } from '@/components/ui/badge'

export default function Footer() {
  return (
    <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-muted-foreground">
            © 2025 Locrit - Système de gestion de chatbots autonomes
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Status indicators */}
          <div className="flex items-center space-x-2">
            <Badge variant="secondary" className="text-xs">
              <span className="mr-1 h-2 w-2 rounded-full bg-green-500"></span>
              Interface Web
            </Badge>
            <Badge variant="outline" className="text-xs">
              <span className="mr-1 h-2 w-2 rounded-full bg-yellow-500"></span>
              Ollama
            </Badge>
          </div>

          {/* Version info */}
          <p className="text-xs text-muted-foreground">
            v1.0.0-beta
          </p>
        </div>
      </div>
    </footer>
  )
}