import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

export default function CSSTest() {
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-center">CSS Integration Test</h1>

      {/* Test Tailwind CSS classes */}
      <div className="bg-blue-100 border-2 border-blue-500 rounded-lg p-4">
        <h2 className="text-xl font-semibold text-blue-800 mb-2">Tailwind CSS Test</h2>
        <p className="text-blue-600">
          This box uses Tailwind CSS classes: bg-blue-100, border-2, border-blue-500, rounded-lg, p-4
        </p>
        <div className="mt-4 flex gap-2">
          <div className="w-4 h-4 bg-red-500 rounded-full"></div>
          <div className="w-4 h-4 bg-green-500 rounded-full"></div>
          <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
        </div>
      </div>

      {/* Test Shadcn/ui Button components */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Shadcn/ui Button Components</h2>
        <div className="flex gap-2 flex-wrap">
          <Button variant="default">Default Button</Button>
          <Button variant="secondary">Secondary Button</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button variant="destructive">Destructive Button</Button>
        </div>
      </div>

      {/* Test Shadcn/ui Card component */}
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Shadcn/ui Card Component</CardTitle>
          <CardDescription>This is a test card component from Shadcn/ui</CardDescription>
        </CardHeader>
        <CardContent>
          <p>The card component is working correctly with proper styling.</p>
        </CardContent>
      </Card>

      {/* Test Shadcn/ui Dropdown component */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Shadcn/ui Dropdown Component</h2>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">Open Dropdown</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56">
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
            <DropdownMenuItem>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Test CSS Variables */}
      <div className="bg-background text-foreground border border-border rounded-lg p-4">
        <h2 className="text-xl font-semibold mb-2">CSS Variables Test</h2>
        <p className="text-muted-foreground">
          This section uses CSS variables: bg-background, text-foreground, border-border, text-muted-foreground
        </p>
        <div className="mt-4 bg-card border border-border rounded p-3">
          <p className="text-card-foreground">Card background with card foreground text</p>
        </div>
      </div>
    </div>
  )
}