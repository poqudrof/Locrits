import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import { Toaster } from '@/components/ui/sonner'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Login from '@/pages/Login'
import MyLocrits from '@/pages/MyLocrits'
import LocritSettings from '@/pages/LocritSettings'
import CreateLocrit from '@/pages/CreateLocrit'
import Settings from '@/pages/Settings'
import Chat from '@/pages/Chat'
import CSSTest from '@/pages/CSSTest'
import '@/lib/firebase' // Initialize Firebase on app startup


function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Router>
        <div className="min-h-screen bg-background text-foreground">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="my-locrits" element={<MyLocrits />} />
              <Route path="my-locrits/:locritName/settings" element={<LocritSettings />} />
              <Route path="create-locrit" element={<CreateLocrit />} />
              <Route path="settings" element={<Settings />} />
              <Route path="chat/:locritName" element={<Chat />} />
              <Route path="css-test" element={<CSSTest />} />
            </Route>
          </Routes>
          <Toaster />
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App