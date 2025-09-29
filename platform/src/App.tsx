import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Switch } from "./components/ui/switch";
import { Home, Users, Sparkles, LogOut, Heart, Eye, Database, Settings } from "lucide-react";

import { Dashboard } from "./components/Dashboard";
import { UserManagement } from "./components/UserManagement";
import { LocritCard } from "./components/LocritCard";
import { ChatInterface } from "./components/ChatInterface";
import { LocritSettings } from "./components/LocritSettings";
import { WildObservation } from "./components/WildObservation";
import { LoginForm } from "./components/LoginForm";
import { FirebaseDiagnostic } from "./components/FirebaseDiagnostic";

import { mockUsers, mockLocrits, mockMessages, mockConversations, mockConversationMessages } from "./data/mockData";
import { User, Locrit, ChatMessage, Conversation } from "./types";
import { useAuth } from "./hooks/useAuth";
import { userService, locritService, messageService, conversationService } from "./firebase/services";

type ViewMode = 'locrits' | 'dashboard' | 'users' | 'observations' | 'chat' | 'settings' | 'diagnostic';

// Fonction pour créer des Locrits par défaut pour un utilisateur
const createDefaultLocrits = (userId: string): Locrit[] => {
  return [
    {
      id: `${userId}-locrit-1`,
      name: "Pixie l'Organisateur",
      description: "Un Locrit magique qui adore ranger et planifier ! ✨",
      publicAddress: `pixie-${userId}.locritland.net`,
      ownerId: userId,
      isOnline: true,
      lastSeen: new Date(),
      settings: {
        openTo: {
          humans: true,
          locrits: true,
          invitations: true,
          publicInternet: false,
          publicPlatform: true,
        },
        accessTo: {
          logs: true,
          quickMemory: true,
          fullMemory: false,
          llmInfo: true,
        },
      },
    },
    {
      id: `${userId}-locrit-2`,
      name: "Nova la Curieuse",
      description: "Un Locrit brillant qui explore les données comme une étoile ! ⭐",
      publicAddress: `nova-${userId}.locritland.net`,
      ownerId: userId,
      isOnline: true,
      lastSeen: new Date(),
      settings: {
        openTo: {
          humans: true,
          locrits: true,
          invitations: true,
          publicInternet: false,
          publicPlatform: true,
        },
        accessTo: {
          logs: true,
          quickMemory: true,
          fullMemory: false,
          llmInfo: true,
        },
      },
    },
  ];
};

export default function App() {
  const { user, isLoading, signOut } = useAuth();
  const [currentView, setCurrentView] = useState<ViewMode>('locrits');
  const [useMockData, setUseMockData] = useState<boolean>(true);
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [locrits, setLocrits] = useState<Locrit[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>(mockConversations);
  const [conversationMessages, setConversationMessages] = useState<ChatMessage[]>(mockConversationMessages);
  const [selectedLocritId, setSelectedLocritId] = useState<string | null>(null);
  const [isLoadingData, setIsLoadingData] = useState<boolean>(false);

  // Gérer les données selon le mode (mockup ou Firebase)
  React.useEffect(() => {
    if (!user) {
      setLocrits([]);
      setMessages([]);
      return;
    }

    if (useMockData) {
      // Mode mockup : utiliser les données par défaut
      const userLocrits = createDefaultLocrits(user.uid);
      setLocrits(userLocrits);
      setMessages(mockMessages);
      setUsers(mockUsers);
      setConversations(mockConversations);
      setConversationMessages(mockConversationMessages);
    } else {
      // Mode Firebase : charger les données depuis Firebase
      loadFirebaseData();
    }
  }, [user, useMockData]);

  const loadFirebaseData = async () => {
    if (!user) return;

    setIsLoadingData(true);
    try {
      // Charger les Locrits de l'utilisateur depuis Firebase
      const userLocrits = await locritService.getUserLocrits(user.uid);
      setLocrits(userLocrits);

      // Charger tous les utilisateurs
      const allUsers = await userService.getUsers();
      setUsers(allUsers);

      // Charger les conversations actives
      const activeConversations = await conversationService.getActiveConversations();
      setConversations(activeConversations);

      // Si l'utilisateur n'a pas de Locrits, créer les Locrits par défaut
      if (userLocrits.length === 0) {
        const defaultLocrits = createDefaultLocrits(user.uid);
        for (const locrit of defaultLocrits) {
          const { id, ...locritData } = locrit;
          await locritService.createLocrit(locritData);
        }
        // Recharger les Locrits après création
        const newUserLocrits = await locritService.getUserLocrits(user.uid);
        setLocrits(newUserLocrits);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données Firebase:', error);
      // En cas d'erreur, revenir aux données mockup
      setUseMockData(true);
    } finally {
      setIsLoadingData(false);
    }
  };

  const selectedLocrit = selectedLocritId ? locrits.find(l => l.id === selectedLocritId) : null;
  const chatMessages = selectedLocritId ? messages.filter(m => m.locritId === selectedLocritId) : [];

  // Charger les messages quand un Locrit est sélectionné
  React.useEffect(() => {
    if (selectedLocritId && !useMockData) {
      loadLocritMessages(selectedLocritId);
    }
  }, [selectedLocritId, useMockData]);

  const loadLocritMessages = async (locritId: string) => {
    try {
      const locritMessages = await messageService.getLocritMessages(locritId);
      setMessages(prev => {
        // Remplacer les messages de ce Locrit tout en gardant les autres
        const otherMessages = prev.filter(m => m.locritId !== locritId);
        return [...otherMessages, ...locritMessages];
      });
    } catch (error) {
      console.error('Erreur lors du chargement des messages:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedLocritId) return;
    
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      locritId: selectedLocritId,
      content,
      timestamp: new Date(),
      sender: 'user',
      senderName: user?.displayName || 'Utilisateur actuel',
    };
    
    if (useMockData) {
      // Mode mockup : ajouter directement au state
      setMessages(prev => [...prev, newMessage]);
      
      // Simulate locrit response
      setTimeout(() => {
        const locritResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          locritId: selectedLocritId,
          content: "Merci pour votre message ! Je traite votre demande...",
          timestamp: new Date(),
          sender: 'locrit',
          senderName: selectedLocrit?.name || 'Locrit',
        };
        setMessages(prev => [...prev, locritResponse]);
      }, 1000);
    } else {
      // Mode Firebase : envoyer via le service
      try {
        const { id, ...messageData } = newMessage;
        await messageService.sendMessage(messageData);
        
        // Recharger les messages depuis Firebase
        const updatedMessages = await messageService.getLocritMessages(selectedLocritId);
        setMessages(updatedMessages);
        
        // Simulate locrit response
        setTimeout(async () => {
          const locritResponse = {
            locritId: selectedLocritId,
            content: "Merci pour votre message ! Je traite votre demande...",
            timestamp: new Date(),
            sender: 'locrit' as const,
            senderName: selectedLocrit?.name || 'Locrit',
          };
          await messageService.sendMessage(locritResponse);
          
          // Recharger les messages après la réponse
          const finalMessages = await messageService.getLocritMessages(selectedLocritId);
          setMessages(finalMessages);
        }, 1000);
      } catch (error) {
        console.error('Erreur lors de l\'envoi du message:', error);
        // En cas d'erreur, ajouter le message localement
        setMessages(prev => [...prev, newMessage]);
      }
    }
  };

  const handleLocritUpdate = async (updatedLocrit: Locrit) => {
    if (useMockData) {
      // Mode mockup : mettre à jour directement le state
      setLocrits(prev => prev.map(l => l.id === updatedLocrit.id ? updatedLocrit : l));
    } else {
      // Mode Firebase : mettre à jour via le service
      try {
        const { id, ...locritData } = updatedLocrit;
        await locritService.updateLocrit(id, locritData);
        
        // Recharger les Locrits depuis Firebase
        if (user) {
          const userLocrits = await locritService.getUserLocrits(user.uid);
          setLocrits(userLocrits);
        }
      } catch (error) {
        console.error('Erreur lors de la mise à jour du Locrit:', error);
        // En cas d'erreur, mettre à jour localement
        setLocrits(prev => prev.map(l => l.id === updatedLocrit.id ? updatedLocrit : l));
      }
    }
    setCurrentView('locrits');
  };

  const handleLogout = async () => {
    await signOut();
  };

  // Affichage du loader pendant la vérification de l'authentification
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center border">
            <Sparkles className="h-8 w-8 text-gray-600 animate-spin" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl text-gray-900">Chargement...</h2>
            <p className="text-gray-600">Connexion à la plateforme</p>
          </div>
        </div>
      </div>
    );
  }

  // Affichage du formulaire de connexion si l'utilisateur n'est pas connecté
  if (!user) {
    return <LoginForm />;
  }

  if (currentView === 'chat' && selectedLocrit) {
    return (
      <div className="min-h-screen p-4">
        <div className="max-w-4xl mx-auto">
          <ChatInterface
            locrit={selectedLocrit}
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            onBack={() => setCurrentView('locrits')}
          />
        </div>
      </div>
    );
  }

  if (currentView === 'settings' && selectedLocrit) {
    return (
      <div className="min-h-screen p-4">
        <div className="max-w-4xl mx-auto">
          <LocritSettings
            locrit={selectedLocrit}
            onSave={handleLocritUpdate}
            onBack={() => setCurrentView('locrits')}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-purple-200 bg-white/80 backdrop-blur-md shadow-lg">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">Monde des Locrits</h1>
              <p className="text-sm text-gray-600">
                Bienvenue {user.displayName || (user.isAnonymous ? "Visiteur Magique" : "Gardien des Locrits")} ! ✨
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              {/* Toggle pour le mode de données */}
              <div className="flex items-center gap-2 bg-white/80 backdrop-blur px-3 py-2 rounded-lg border border-purple-200 shadow-sm">
                <Database className={`w-4 h-4 text-gray-600 ${isLoadingData ? 'animate-spin' : ''}`} />
                <span className="text-sm text-gray-700">
                  {isLoadingData ? "Chargement..." : (useMockData ? "Mockup" : "Firebase")}
                </span>
                <Switch
                  checked={!useMockData}
                  onCheckedChange={(checked) => setUseMockData(!checked)}
                  disabled={isLoadingData}
                  className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-purple-500 data-[state=checked]:to-pink-500"
                />
              </div>
              
              <Badge className="bg-gradient-to-r from-green-400 to-blue-400 text-white border-0 shadow-lg">
                <Heart className="w-3 h-3 mr-1" />
                {locrits.filter(l => l.isOnline).length} Locrits éveillés
              </Badge>
            </div>
            <Badge className="bg-gradient-to-r from-emerald-400 to-teal-400 text-white border-0 shadow-lg">
              <Eye className="w-3 h-3 mr-1" />
              {conversations.filter(c => c.isActive).length} conversations actives
            </Badge>
            <div className="flex items-center gap-2">
              {user.isAnonymous && (
                <Badge className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white border-0 shadow-lg">
                  🎭 Visiteur
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={handleLogout} className="hover:bg-purple-100">
                <LogOut className="h-4 w-4 mr-2" />
                Au revoir
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={currentView} onValueChange={(value) => setCurrentView(value as ViewMode)}>
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-white/60 backdrop-blur p-1 rounded-2xl shadow-lg border border-purple-200">
            <TabsTrigger value="locrits" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-pink-500 data-[state=active]:text-white">
              <Sparkles className="h-4 w-4" />
              Mes Locrits
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-cyan-500 data-[state=active]:text-white">
              <Home className="h-4 w-4" />
              Vue d'ensemble
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-yellow-500 data-[state=active]:text-white">
              <Users className="h-4 w-4" />
              Amis
            </TabsTrigger>
            <TabsTrigger value="observations" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white">
              <Eye className="h-4 w-4" />
              Observations
            </TabsTrigger>
            <TabsTrigger value="diagnostic" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-gray-500 data-[state=active]:to-slate-500 data-[state=active]:text-white">
              <Settings className="h-4 w-4" />
              Diagnostic
            </TabsTrigger>
          </TabsList>

          <TabsContent value="locrits">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold gradient-text">Tes Locrits Magiques</h2>
                  <p className="text-gray-600 text-lg">
                    Découvre et joue avec tes Locrits enchantés ! ✨
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Button 
                    variant="outline"
                    onClick={() => setCurrentView('observations')}
                    className="bg-gradient-to-r from-green-100 to-emerald-100 hover:from-green-200 hover:to-emerald-200 border-green-300 text-green-700 shadow-lg rounded-xl px-4 py-3"
                  >
                    <Eye className="mr-2 h-5 w-5" />
                    Voir les Observations
                  </Button>
                  <Button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg rounded-xl px-6 py-3">
                    <Sparkles className="mr-2 h-5 w-5" />
                    Nouveau Locrit
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {locrits.map((locrit) => (
                  <LocritCard
                    key={locrit.id}
                    locrit={locrit}
                    onChat={(locritId) => {
                      setSelectedLocritId(locritId);
                      setCurrentView('chat');
                    }}
                    onSettings={(locritId) => {
                      setSelectedLocritId(locritId);
                      setCurrentView('settings');
                    }}
                  />
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="dashboard">
            <Dashboard users={users} locrits={locrits} />
          </TabsContent>

          <TabsContent value="users">
            <UserManagement
              users={users}
              locrits={locrits}
              onManageUser={(userId) => console.log('Manage user:', userId)}
            />
          </TabsContent>

          <TabsContent value="observations">
            <WildObservation 
              conversations={conversations}
              messages={conversationMessages}
              locrits={locrits}
            />
          </TabsContent>

          <TabsContent value="diagnostic">
            <FirebaseDiagnostic />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}