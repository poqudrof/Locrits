import React, { useState, useCallback } from "react";
import { Routes, Route, useNavigate, useLocation, Navigate, useParams } from "react-router-dom";
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
import { PublicLocritChat } from "./components/PublicLocritChat";
import { PublicLocritsDirectory } from "./components/PublicLocritsDirectory";

import { User, Locrit, ChatMessage, Conversation } from "./types";
import { useAuth } from "./hooks/useAuth";
import { userService, locritService, messageService, conversationService as firebaseConversationService } from "./firebase/services";
import { firebaseService, FirebaseLocrit } from "./lib/firebaseService";
import { locritBackendService } from "./lib/locritBackendService";
import { locritWebSocketService } from "./lib/locritWebSocketService";
import { conversationService } from "./lib/conversationService";

type ViewMode = 'locrits' | 'published' | 'dashboard' | 'users' | 'observations' | 'chat' | 'settings' | 'diagnostic';


export default function App() {
  const { user, isLoading, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [users, setUsers] = useState<User[]>([]);
  const [locrits, setLocrits] = useState<Locrit[]>([]);
  const [publishedLocrits, setPublishedLocrits] = useState<FirebaseLocrit[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationMessages, setConversationMessages] = useState<ChatMessage[]>([]);
  const [isLoadingData, setIsLoadingData] = useState<boolean>(false);
  const loadedMessagesRef = React.useRef<Set<string>>(new Set());
  // Map of locritId -> conversationId for server-side context management
  const [locritConversations, setLocritConversations] = useState<Map<string, string>>(new Map());

  // Charger les données depuis Firebase
  React.useEffect(() => {
    if (!user) {
      setLocrits([]);
      setMessages([]);
      return;
    }

    // Charger les données depuis Firebase
    loadFirebaseData();
  }, [user]);

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

      // Charger les Locrits publiés
      const published = await firebaseService.getPublishedLocrits();
      setPublishedLocrits(published);

      // Si l'utilisateur n'a pas de Locrits, créer les Locrits par défaut
      if (userLocrits.length === 0) {
        const defaultLocrits = [
          {
            name: "Pixie l'Organisateur",
            description: "Un Locrit magique qui adore ranger et planifier ! ✨",
            publicAddress: `pixie-${user.uid}.locritland.net`,
            ownerId: user.uid,
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
            name: "Nova la Curieuse",
            description: "Un Locrit brillant qui explore les données comme une étoile ! ⭐",
            publicAddress: `nova-${user.uid}.locritland.net`,
            ownerId: user.uid,
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

        for (const locritData of defaultLocrits) {
          await locritService.createLocrit(locritData);
        }
        // Recharger les Locrits après création
        const newUserLocrits = await locritService.getUserLocrits(user.uid);
        setLocrits(newUserLocrits);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données Firebase:', error);
      // En cas d'erreur, garder les données vides
    } finally {
      setIsLoadingData(false);
    }
  };

  const loadLocritMessages = useCallback(async (locritId: string) => {
    try {
      // Check if we have a conversation ID for this Locrit
      const conversationId = locritConversations.get(locritId);

      if (conversationId) {
        // Load messages from conversation API (server-side context)
        const history = await conversationService.getConversationHistory(conversationId, 50);

        // Convert to ChatMessage format
        const chatMessages: ChatMessage[] = history.messages.map((msg, idx) => ({
          id: `${conversationId}-${idx}`,
          locritId: locritId,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          sender: msg.role === 'user' ? 'user' : 'locrit',
          senderName: msg.role === 'user' ? (user?.displayName || 'Utilisateur') : history.locrit_name,
        }));

        setMessages(prev => {
          // Replace messages for this Locrit
          const otherMessages = prev.filter(m => m.locritId !== locritId);
          return [...otherMessages, ...chatMessages];
        });

        console.log(`✅ Loaded ${chatMessages.length} messages from conversation ${conversationId}`);
      } else {
        // Fallback to Firebase messages if no conversation exists
        const locritMessages = await messageService.getLocritMessages(locritId);
        setMessages(prev => {
          const otherMessages = prev.filter(m => m.locritId !== locritId);
          return [...otherMessages, ...locritMessages];
        });
      }
    } catch (error) {
      console.error('Erreur lors du chargement des messages:', error);
    }
  }, [locritConversations, user]);

  const handleSendMessage = useCallback(async (locritId: string, content: string) => {
    const selectedLocrit = locrits.find(l => l.id === locritId);
    if (!selectedLocrit) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      locritId: locritId,
      content,
      timestamp: new Date(),
      sender: 'user',
      senderName: user?.displayName || 'Utilisateur actuel',
    };

    // Ajouter le message utilisateur immédiatement (optimistic update)
    setMessages(prev => [...prev, newMessage]);

    try {
      // Get or create conversation ID for this Locrit
      let conversationId = locritConversations.get(locritId);

      if (!conversationId) {
        // Create a new conversation
        const conversation = await conversationService.createConversation(
          selectedLocrit.name,
          user?.uid || 'anonymous',
          {
            locrit_id: locritId,
            source: 'platform',
          }
        );
        conversationId = conversation.conversation_id;

        // Store the conversation ID
        setLocritConversations(prev => new Map(prev).set(locritId, conversationId!));

        console.log(`✅ Created conversation ${conversationId} for ${selectedLocrit.name}`);
      }

      // Send message using conversation API - context is managed server-side!
      const response = await conversationService.sendMessage(conversationId, content);

      if (response.success) {
        const locritResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          locritId: locritId,
          content: response.response,
          timestamp: new Date(response.timestamp),
          sender: 'locrit',
          senderName: selectedLocrit.name,
        };

        setMessages(prev => [...prev, locritResponse]);
        console.log(`✅ Message sent, conversation has ${response.message_count} messages`);
      }
    } catch (error) {
      console.error('❌ Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        locritId: locritId,
        content: `Erreur: ${error instanceof Error ? error.message : 'Erreur de connexion'}`,
        timestamp: new Date(),
        sender: 'locrit',
        senderName: 'Système',
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [locrits, user, locritConversations]);

  const handleLocritUpdate = async (updatedLocrit: Locrit) => {
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
    navigate('/locrits');
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

  // Routes wrapper components
  const ChatPage = () => {
    const { locritId } = useParams();
    const selectedLocrit = React.useMemo(
      () => locritId ? locrits.find(l => l.id === locritId) : null,
      [locritId, locrits]
    );
    const chatMessages = React.useMemo(
      () => locritId ? messages.filter(m => m.locritId === locritId) : [],
      [locritId, messages]
    );

    // Charger les messages quand on entre dans le chat (seulement une fois par locritId)
    React.useEffect(() => {
      if (locritId && !loadedMessagesRef.current.has(locritId)) {
        console.log('Loading messages for locritId:', locritId);
        loadLocritMessages(locritId);
        loadedMessagesRef.current.add(locritId);
      }
    }, [locritId]);

    if (!selectedLocrit) {
      return <Navigate to="/locrits" replace />;
    }

    return (
      <div className="min-h-screen p-4">
        <div className="max-w-4xl mx-auto">
          <ChatInterface
            locrit={selectedLocrit}
            messages={chatMessages}
            onSendMessage={(content) => handleSendMessage(selectedLocrit.id, content)}
            onBack={() => navigate('/locrits')}
          />
        </div>
      </div>
    );
  };

  const SettingsPage = () => {
    const { locritId } = useParams();
    const selectedLocrit = locritId ? locrits.find(l => l.id === locritId) : null;

    if (!selectedLocrit) {
      return <Navigate to="/locrits" replace />;
    }

    return (
      <div className="min-h-screen p-4">
        <div className="max-w-4xl mx-auto">
          <LocritSettings
            locrit={selectedLocrit}
            onSave={handleLocritUpdate}
            onBack={() => navigate('/locrits')}
          />
        </div>
      </div>
    );
  };

  // Main layout with tabs navigation
  const MainLayout = () => {
    const currentPath = location.pathname;
    const currentTab = currentPath.split('/')[1] || 'locrits';

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
              <Badge className="bg-gradient-to-r from-green-400 to-blue-400 text-white border-0 shadow-lg">
                <Heart className="w-3 h-3 mr-1" />
                {locrits.filter(l => l.isOnline).length} Locrits éveillés
              </Badge>
              <Badge className="bg-gradient-to-r from-indigo-400 to-blue-400 text-white border-0 shadow-lg">
                <Eye className="w-3 h-3 mr-1" />
                {publishedLocrits.length} Locrits publiés
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
        <Tabs value={currentTab} onValueChange={(value) => navigate(`/${value}`)}>
          <TabsList className="grid w-full grid-cols-6 mb-6 bg-white/60 backdrop-blur p-1 rounded-2xl shadow-lg border border-purple-200">
            <TabsTrigger value="locrits" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-pink-500 data-[state=active]:text-white">
              <Sparkles className="h-4 w-4" />
              Mes Locrits
            </TabsTrigger>
            <TabsTrigger value="published" className="flex items-center gap-2 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-blue-500 data-[state=active]:text-white">
              <Eye className="h-4 w-4" />
              Locrits Publiés
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

          {/* Routes content */}
          <Routes>
            <Route index element={<Navigate to="/locrits" replace />} />
            <Route path="/locrits" element={
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
                      onClick={() => navigate('/observations')}
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
                    <div key={locrit.id}>
                      <LocritCard
                        locrit={locrit}
                        onChat={(locritId) => navigate(`/chat/${locritId}`)}
                        onSettings={(locritId) => navigate(`/settings/${locritId}`)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            } />

            <Route path="/published" element={
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold gradient-text">Locrits Publiés</h2>
                  <p className="text-gray-600 text-lg">
                    Découvrez les Locrits publiés par d'autres utilisateurs ✨
                  </p>
                </div>
              </div>

              {publishedLocrits.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {publishedLocrits.map((locrit) => (
                    <div key={locrit.id} className="bg-white rounded-xl shadow-lg border border-purple-200 p-6 hover:shadow-xl transition-shadow">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-400 to-blue-400 rounded-full flex items-center justify-center">
                          <span className="text-white text-xl">🤖</span>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900">{locrit.name}</h3>
                          <p className="text-gray-600 text-sm">{locrit.description}</p>
                        </div>
                      </div>

                      <div className="space-y-3 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Adresse publique:</span>
                          <code className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
                            {locrit.publicAddress}
                          </code>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Statut:</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${locrit.isOnline ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {locrit.isOnline ? '🟢 En ligne' : '🔴 Hors ligne'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Créé:</span>
                          <span className="text-gray-800">{locrit.createdAt?.toLocaleDateString()}</span>
                        </div>
                      </div>

                      <button className="w-full bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                        🌐 Visiter le Locrit
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-br from-indigo-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <span className="text-4xl">🌐</span>
                  </div>
                  <h3 className="text-xl font-medium text-gray-900 mb-2">Aucun Locrit publié</h3>
                  <p className="text-gray-600 mb-6">
                    Aucun Locrit n'a encore été publié sur la plateforme publique.
                    Publiez votre premier Locrit pour qu'il apparaisse ici !
                  </p>
                </div>
              )}
            </div>
            } />

            <Route path="/dashboard" element={<Dashboard users={users} locrits={locrits} />} />

            <Route path="/users" element={
              <UserManagement
                users={users}
                locrits={locrits}
                onManageUser={(userId) => console.log('Manage user:', userId)}
              />
            } />

            <Route path="/observations" element={
              <WildObservation
                conversations={conversations}
                messages={conversationMessages}
                locrits={locrits}
              />
            } />

            <Route path="/diagnostic" element={<FirebaseDiagnostic />} />
          </Routes>
        </Tabs>
      </div>
    </div>
  );
  };

  // Main app with top-level routing
  return (
    <Routes>
      {/* Routes publiques (accessibles sans authentification) */}
      <Route path="/public" element={<PublicLocritsDirectory />} />
      <Route path="/public/:locritName" element={<PublicLocritChat />} />

      {/* Routes privées (nécessitent authentification) */}
      <Route path="/chat/:locritId" element={<ChatPage />} />
      <Route path="/settings/:locritId" element={<SettingsPage />} />
      <Route path="/*" element={<MainLayout />} />
    </Routes>
  );
}