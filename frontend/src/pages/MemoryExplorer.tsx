import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import { ArrowLeft, Search, Edit, Trash2, Plus, Database, MessageSquare, Users, Brain, Clock, Lightbulb } from 'lucide-react';

interface MemoryStats {
  total_messages: number;
  total_sessions: number;
  total_concepts: number;
  total_users: number;
}

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: string;
  session_id: string;
  metadata?: any;
}

interface Session {
  id: string;
  name: string;
  topic?: string;
  created_at: string;
  user_id: string;
}

interface Concept {
  name: string;
  type: string;
  mentions: number;
}

interface Memory {
  id: string;
  content: string;
  importance: number;
  created_at: string;
  last_accessed: string;
}

const MemoryExplorer: React.FC = () => {
  const { locritName } = useParams<{ locritName: string }>();
  const navigate = useNavigate();

  // State management
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  // Dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addMemoryDialogOpen, setAddMemoryDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);

  // Form state
  const [newMemoryContent, setNewMemoryContent] = useState('');
  const [newMemoryImportance, setNewMemoryImportance] = useState([0.5]);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    if (locritName) {
      loadMemoryData();
    }
  }, [locritName]);

  const loadMemoryData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load memory summary for stats
      const summaryResponse = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/summary`);
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setStats(summaryData.statistics);
        setMessages(summaryData.recent_messages || []);
        setSessions(summaryData.sessions || []);
        setConcepts(summaryData.top_concepts || []);
      }

      // Load standalone memories
      const memoriesResponse = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/memories`);
      if (memoriesResponse.ok) {
        const memoriesData = await memoriesResponse.json();
        setMemories(memoriesData.memories || []);
      }

    } catch (err) {
      setError('Failed to load memory data');
      console.error('Error loading memory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/search?q=${encodeURIComponent(searchQuery)}&limit=50`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.results || []);
        setActiveTab('messages');
      }
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/sessions/${encodeURIComponent(sessionId)}/messages?limit=500`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setActiveTab('messages');
        setSearchQuery(`Session: ${sessionId}`);
      } else {
        setError('Failed to load session messages');
      }
    } catch (err) {
      setError('Error loading session messages');
      console.error('Error loading session messages:', err);
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/messages/${messageId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setMessages(messages.filter(m => m.id !== messageId));
        toast.success('Message deleted successfully');
      } else {
        setError('Failed to delete message');
        toast.error('Failed to delete message');
      }
    } catch (err) {
      setError('Error deleting message');
    }
  };

  const handleEditMessage = async () => {
    if (!editingItem || !editContent.trim()) return;

    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/messages/${editingItem.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent })
      });

      if (response.ok) {
        // Update the message in the list
        setMessages(messages.map(m =>
          m.id === editingItem.id ? { ...m, content: editContent } : m
        ));
        setEditDialogOpen(false);
        setEditingItem(null);
        setEditContent('');
        toast.success('Message edited successfully');
      } else {
        setError('Failed to edit message');
      }
    } catch (err) {
      setError('Error editing message');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/sessions/${sessionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSessions(sessions.filter(s => s.id !== sessionId));
        // Also remove messages from that session
        setMessages(messages.filter(m => m.session_id !== sessionId));
      } else {
        setError('Failed to delete session');
      }
    } catch (err) {
      setError('Error deleting session');
    }
  };

  const handleAddMemory = async () => {
    if (!newMemoryContent.trim()) return;

    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/memories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newMemoryContent,
          importance: newMemoryImportance[0]
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Reload memories
        loadMemoryData();
        setAddMemoryDialogOpen(false);
        setNewMemoryContent('');
        setNewMemoryImportance([0.5]);
        toast.success('Memory added successfully');
      } else {
        setError('Failed to add memory');
      }
    } catch (err) {
      setError('Error adding memory');
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/memories/${memoryId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setMemories(memories.filter(m => m.id !== memoryId));
        toast.success('Memory deleted successfully');
      } else {
        setError('Failed to delete memory');
        toast.error('Failed to delete memory');
      }
    } catch (err) {
      setError('Error deleting memory');
    }
  };

  const handleClearAllMemory = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/clear`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true })
      });

      if (response.ok) {
        // Reload all data
        loadMemoryData();
        toast.success('All memory cleared successfully');
      } else {
        setError('Failed to clear memory');
        toast.error('Failed to clear memory');
      }
    } catch (err) {
      setError('Error clearing memory');
    }
  };

  const openEditDialog = (item: any, type: string) => {
    setEditingItem({ ...item, type });
    setEditContent(item.content || '');
    setEditDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Database className="h-12 w-12 mx-auto mb-4 animate-pulse" />
          <p>Loading memory data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <h1 className="text-3xl font-bold">Memory Explorer</h1>
          <Badge variant="secondary">{locritName}</Badge>
        </div>

        <div className="flex items-center space-x-2">
          <Button onClick={loadMemoryData} variant="outline">
            Refresh
          </Button>
          <Dialog open={addMemoryDialogOpen} onOpenChange={setAddMemoryDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Memory
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Memory</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="memory-content">Memory Content</Label>
                  <Textarea
                    id="memory-content"
                    placeholder="Enter memory content..."
                    value={newMemoryContent}
                    onChange={(e) => setNewMemoryContent(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="importance">Importance: {newMemoryImportance[0]}</Label>
                  <Slider
                    id="importance"
                    min={0}
                    max={1}
                    step={0.1}
                    value={newMemoryImportance}
                    onValueChange={setNewMemoryImportance}
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setAddMemoryDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddMemory}>Add Memory</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex space-x-2">
            <Input
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="mb-6 border-red-200">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
            <Button variant="outline" onClick={() => setError(null)} className="mt-2">
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="messages">Messages</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="concepts">Concepts</TabsTrigger>
          <TabsTrigger value="memories">Memories</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_messages || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_sessions || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Concepts</CardTitle>
                <Brain className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_concepts || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Standalone Memories</CardTitle>
                <Lightbulb className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{memories.length}</div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Messages Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Messages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {messages.slice(0, 5).map((message, index) => (
                  <div key={message.id || `message-${index}`} className="flex items-start space-x-3 p-3 border rounded-lg">
                    <Badge variant={message.role === 'user' ? 'default' : 'secondary'}>
                      {message.role}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{message.content}</p>
                      <p className="text-xs text-muted-foreground">{new Date(message.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Messages ({messages.length})</CardTitle>
                {searchQuery.startsWith('Session:') && (
                  <Badge variant="outline" className="ml-2">
                    {searchQuery}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-4 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white ml-12'
                        : 'bg-gray-100 dark:bg-gray-800 mr-12'
                    }`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant={message.role === 'user' ? 'secondary' : 'outline'} className={
                              message.role === 'user' ? 'bg-blue-400 text-white' : ''
                            }>
                              {message.role === 'user' ? '👤 User' : '🤖 Assistant'}
                            </Badge>
                            <span className="text-xs opacity-70">
                              {new Date(message.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          {!searchQuery.startsWith('Session:') && (
                            <p className="text-xs opacity-70 mt-2">
                              Session: {message.session_id}
                            </p>
                          )}
                        </div>
                        <div className="flex space-x-1 ml-2">
                          <Button
                            key={`edit-${message.id}`}
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0 opacity-50 hover:opacity-100"
                            onClick={() => openEditDialog(message, 'message')}
                          >
                            <Edit className="h-3 w-3" />
                          </Button>
                          <AlertDialog key={`delete-${message.id}`}>
                            <AlertDialogTrigger asChild>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 w-6 p-0 opacity-50 hover:opacity-100"
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete Message</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete this message? This action cannot be undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => handleDeleteMessage(message.id)}>
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Conversation Sessions ({sessions.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sessions.map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h3 className="font-medium">{session.name || session.id}</h3>
                      <p className="text-sm text-muted-foreground">
                        Created: {new Date(session.created_at).toLocaleString()}
                      </p>
                      <p className="text-sm text-muted-foreground">User: {session.user_id}</p>
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => loadSessionMessages(session.id)}
                      >
                        View Messages
                      </Button>
                      <AlertDialog key={`delete-session-${session.id}`}>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="outline">
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Session</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete this session and all its messages? This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDeleteSession(session.id)}>
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Concepts Tab */}
        <TabsContent value="concepts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Learned Concepts ({concepts.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {concepts.map((concept, index) => (
                  <div key={`${concept.name}-${concept.type}-${index}`} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{concept.name}</h3>
                      <Badge variant="outline">{concept.mentions} mentions</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">Type: {concept.type}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Memories Tab */}
        <TabsContent value="memories" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Standalone Memories ({memories.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {memories.map((memory) => (
                  <div key={memory.id} className="flex items-start space-x-3 p-4 border rounded-lg">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">{memory.content}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant="outline">
                          Importance: {memory.importance.toFixed(1)}
                        </Badge>
                        <p className="text-xs text-muted-foreground">
                          Created: {new Date(memory.created_at).toLocaleString()}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Accessed: {new Date(memory.last_accessed).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <AlertDialog key={`delete-memory-${memory.id}`}>
                       <AlertDialogTrigger asChild>
                         <Button size="sm" variant="outline">
                           <Trash2 className="h-3 w-3" />
                         </Button>
                       </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete Memory</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to delete this memory? This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction onClick={() => handleDeleteMemory(memory.id)}>
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit {editingItem?.type || 'Item'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-content">Content</Label>
              <Textarea
                id="edit-content"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleEditMessage}>Save Changes</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Danger Zone */}
      <Card className="mt-8 border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Clear All Memory</h3>
              <p className="text-sm text-muted-foreground">
                Permanently delete all memory data for this Locrit
              </p>
            </div>
            <AlertDialog key="clear-all-memory">
               <AlertDialogTrigger asChild>
                 <Button variant="destructive">Clear All Memory</Button>
               </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Clear All Memory</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete ALL memory data for {locritName}, including messages, sessions, concepts, and memories. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleClearAllMemory} className="bg-red-600 hover:bg-red-700">
                    Yes, Clear All Memory
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MemoryExplorer;