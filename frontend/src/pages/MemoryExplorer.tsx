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

interface ContextExample {
  content: string;
  role: string;
  timestamp: string;
}

interface RelatedConcept {
  name: string;
  type: string;
  description?: string;
}

interface ConceptDetails extends Concept {
  description?: string;
  related_concepts?: RelatedConcept[];
  first_mentioned?: string;
  last_mentioned?: string;
  context_examples?: ContextExample[];
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
  const [conceptDetails, setConceptDetails] = useState<ConceptDetails | null>(null);
  const [conceptDetailsLoading, setConceptDetailsLoading] = useState(false);
  const [memoryServiceType, setMemoryServiceType] = useState<string>('plaintext_file');

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  // Dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addMemoryDialogOpen, setAddMemoryDialogOpen] = useState(false);
  const [conceptDialogOpen, setConceptDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);

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

      // Load Locrit config to get memory service type
      const configResponse = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/config`);
      if (configResponse.ok) {
        const configData = await configResponse.json();
        if (configData.success && configData.settings) {
          setMemoryServiceType(configData.settings.memory_service || 'plaintext_file');
        }
      }

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
        setSelectedSessionId(sessionId);
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

  const clearSessionFilter = () => {
    setSelectedSessionId(null);
    setSearchQuery('');
    loadMemoryData(); // Reload all messages
  };

  // Group messages by session for display
  const groupedMessages = React.useMemo(() => {
    if (selectedSessionId) {
      // If a specific session is selected, return messages as a single group
      return [{ sessionId: selectedSessionId, messages }];
    }

    // Group messages by session_id
    const grouped = messages.reduce((acc, message) => {
      const sessionId = message.session_id || 'unknown';
      if (!acc[sessionId]) {
        acc[sessionId] = [];
      }
      acc[sessionId].push(message);
      return acc;
    }, {} as Record<string, Message[]>);

    // Convert to array and sort by most recent message in each session
    return Object.entries(grouped)
      .map(([sessionId, sessionMessages]) => ({
        sessionId,
        messages: sessionMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      }))
      .sort((a, b) => {
        const aLatest = Math.max(...a.messages.map(m => new Date(m.timestamp).getTime()));
        const bLatest = Math.max(...b.messages.map(m => new Date(m.timestamp).getTime()));
        return bLatest - aLatest; // Most recent sessions first
      });
  }, [messages, selectedSessionId]);

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

  const loadConceptDetails = async (conceptName: string, conceptType: string) => {
    try {
      setConceptDetailsLoading(true);
      setError(null);

      const params = new URLSearchParams({
        name: conceptName,
        type: conceptType
      });

      const response = await fetch(`http://localhost:5000/api/locrits/${encodeURIComponent(locritName!)}/memory/concepts/details?${params}`);
      if (response.ok) {
        const data = await response.json();
        setConceptDetails(data);
        setSelectedConcept(data);
        setConceptDialogOpen(true);
      } else {
        setError('Failed to load concept details');
      }
    } catch (err) {
      setError('Error loading concept details');
      console.error('Error loading concept details:', err);
    } finally {
      setConceptDetailsLoading(false);
    }
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
          <Badge variant="outline">
            {memoryServiceType === 'plaintext_file' && '📄 Plain Text'}
            {memoryServiceType === 'kuzu_graph' && '🗄️ Kuzu Graph'}
            {memoryServiceType === 'lancedb_langchain' && '⚡ LanceDB LangChain'}
            {memoryServiceType === 'lancedb_mcp' && '🔌 LanceDB MCP'}
            {memoryServiceType === 'basic_memory' && '✨ Basic Memory'}
            {memoryServiceType === 'disabled' && '❌ Disabled'}
          </Badge>
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
            {/* Messages - shown for all conversation-based memory types */}
            {(memoryServiceType === 'plaintext_file' || memoryServiceType === 'kuzu_graph') && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_messages || 0}</div>
                </CardContent>
              </Card>
            )}

            {/* Sessions - shown for all conversation-based memory types */}
            {(memoryServiceType === 'plaintext_file' || memoryServiceType === 'kuzu_graph') && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_sessions || 0}</div>
                </CardContent>
              </Card>
            )}

            {/* Concepts - shown only for graph-based memory */}
            {memoryServiceType === 'kuzu_graph' && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Concepts</CardTitle>
                  <Brain className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_concepts || 0}</div>
                </CardContent>
              </Card>
            )}

            {/* Standalone Memories - shown for vector/basic memory types */}
            {(memoryServiceType === 'lancedb_langchain' || memoryServiceType === 'lancedb_mcp' || memoryServiceType === 'basic_memory') && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {memoryServiceType.startsWith('lancedb') ? 'Vector Memories' : 'Stored Memories'}
                  </CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{memories.length}</div>
                </CardContent>
              </Card>
            )}

            {/* Memory Service Info Card */}
            <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Service</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-sm font-semibold">
                  {memoryServiceType === 'plaintext_file' && '📄 Plain Text'}
                  {memoryServiceType === 'kuzu_graph' && '🗄️ Kuzu Graph'}
                  {memoryServiceType === 'lancedb_langchain' && '⚡ LanceDB LangChain'}
                  {memoryServiceType === 'lancedb_mcp' && '🔌 LanceDB MCP'}
                  {memoryServiceType === 'basic_memory' && '✨ Basic Memory'}
                  {memoryServiceType === 'disabled' && '❌ Disabled'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {memoryServiceType === 'plaintext_file' && 'Conversation logs'}
                  {memoryServiceType === 'kuzu_graph' && 'Graph database'}
                  {memoryServiceType === 'lancedb_langchain' && 'Vector embeddings'}
                  {memoryServiceType === 'lancedb_mcp' && 'MCP vector store'}
                  {memoryServiceType === 'basic_memory' && 'MCP key-value'}
                  {memoryServiceType === 'disabled' && 'No storage'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Sessions Preview - Only for conversation-based memory */}
          {(memoryServiceType === 'plaintext_file' || memoryServiceType === 'kuzu_graph') && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>💬 Recent Conversations</CardTitle>
                  <Button variant="outline" size="sm" onClick={() => setActiveTab('messages')}>
                    View All
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {groupedMessages.slice(0, 3).map((group, idx) => {
                    const firstMsg = group.messages[0];
                    const lastMsg = group.messages[group.messages.length - 1];
                    const sessionName = group.sessionId.length > 40
                      ? `${group.sessionId.substring(0, 40)}...`
                      : group.sessionId;

                    return (
                      <div
                        key={group.sessionId}
                        className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                        onClick={() => loadSessionMessages(group.sessionId)}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${idx === 0 ? 'bg-green-500' : idx === 1 ? 'bg-blue-500' : 'bg-gray-400'}`} />
                            <h3 className="font-medium text-sm">{sessionName}</h3>
                          </div>
                          <Badge variant="outline" className="ml-2">
                            {group.messages.length} messages
                          </Badge>
                        </div>

                        <div className="space-y-2">
                          {/* Show first and last message preview */}
                          <div className="flex items-start space-x-2 bg-blue-50 dark:bg-blue-950 p-2 rounded">
                            <Badge variant="default" className="text-xs shrink-0">👤</Badge>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs line-clamp-2">{firstMsg.content}</p>
                            </div>
                          </div>

                          {group.messages.length > 1 && (
                            <div className="flex items-start space-x-2 bg-gray-50 dark:bg-gray-900 p-2 rounded">
                              <Badge variant="secondary" className="text-xs shrink-0">🤖</Badge>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs line-clamp-2">{lastMsg.content}</p>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                          <span>
                            <Clock className="inline h-3 w-3 mr-1" />
                            {new Date(firstMsg.timestamp).toLocaleDateString()}
                          </span>
                          <span className="text-blue-600 dark:text-blue-400 font-medium">
                            View conversation →
                          </span>
                        </div>
                      </div>
                    );
                  })}

                  {groupedMessages.length === 0 && (
                    <div className="text-center p-8">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-muted-foreground text-sm">No conversations yet</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Start chatting to see conversations here
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  {selectedSessionId ? '💬 Conversation' : '📨 All Messages'} ({messages.length})
                </CardTitle>
                <div className="flex items-center space-x-2">
                  {selectedSessionId && (
                    <Button variant="outline" size="sm" onClick={clearSessionFilter}>
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Show All Conversations
                    </Button>
                  )}
                  {searchQuery.startsWith('Session:') && (
                    <Badge variant="outline" className="max-w-xs truncate">
                      {searchQuery}
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {groupedMessages.map((group, groupIndex) => {
                  const sessionDate = new Date(group.messages[0]?.timestamp).toLocaleDateString();
                  const sessionTime = new Date(group.messages[0]?.timestamp).toLocaleTimeString();

                  return (
                    <div key={group.sessionId} className="space-y-4">
                      {/* Session Header (only show if not viewing a specific session) */}
                      {!selectedSessionId && (
                        <div
                          className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg border-2 border-blue-200 dark:border-blue-800 hover:border-blue-400 dark:hover:border-blue-600 transition-colors cursor-pointer"
                          onClick={() => loadSessionMessages(group.sessionId)}
                        >
                          <div className="flex items-center space-x-3">
                            <div className="bg-blue-500 text-white rounded-full p-2">
                              <MessageSquare className="h-4 w-4" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                                Conversation Session
                              </h3>
                              <div className="flex items-center gap-3 mt-1">
                                <Badge variant="outline" className="bg-white dark:bg-gray-900">
                                  {group.messages.length} messages
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {sessionDate} at {sessionTime}
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1 max-w-md truncate">
                                Session ID: {group.sessionId}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="default"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                loadSessionMessages(group.sessionId);
                              }}
                            >
                              View Full Thread
                            </Button>
                          </div>
                        </div>
                      )}

                    {/* Messages in this session */}
                    <div className="space-y-4 pl-2">
                      {group.messages.map((message, msgIdx) => (
                        <div key={message.id} className={`flex group ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[75%] rounded-lg shadow-sm border transition-all hover:shadow-md ${
                            message.role === 'user'
                              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white border-blue-400 ml-16'
                              : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 mr-16'
                          }`}>
                            <div className="p-4">
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1">
                                  {/* Header with role badge and timestamp */}
                                  <div className="flex items-center gap-2 mb-3">
                                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                      message.role === 'user'
                                        ? 'bg-blue-400 bg-opacity-30 text-white'
                                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                    }`}>
                                      <span>{message.role === 'user' ? '👤' : '🤖'}</span>
                                      <span>{message.role === 'user' ? 'You' : 'Assistant'}</span>
                                    </div>
                                    <span className={`text-xs ${
                                      message.role === 'user'
                                        ? 'text-blue-100'
                                        : 'text-gray-500 dark:text-gray-400'
                                    }`}>
                                      {new Date(message.timestamp).toLocaleTimeString([], {
                                        hour: '2-digit',
                                        minute: '2-digit'
                                      })}
                                    </span>
                                  </div>

                                  {/* Message content */}
                                  <p className={`text-sm leading-relaxed whitespace-pre-wrap ${
                                    message.role === 'user'
                                      ? 'text-white'
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`}>
                                    {message.content}
                                  </p>
                                </div>

                                {/* Action buttons */}
                                <div className="flex flex-col space-y-1 ml-2">
                                  <Button
                                    key={`edit-${message.id}`}
                                    size="sm"
                                    variant="ghost"
                                    className={`h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity ${
                                      message.role === 'user'
                                        ? 'hover:bg-blue-400 hover:bg-opacity-30 text-white'
                                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`}
                                    onClick={() => openEditDialog(message, 'message')}
                                  >
                                    <Edit className="h-3.5 w-3.5" />
                                  </Button>
                                  <AlertDialog key={`delete-${message.id}`}>
                                    <AlertDialogTrigger asChild>
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className={`h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity ${
                                          message.role === 'user'
                                            ? 'hover:bg-blue-400 hover:bg-opacity-30 text-white'
                                            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                                        }`}
                                      >
                                        <Trash2 className="h-3.5 w-3.5" />
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
                        </div>
                      ))}
                    </div>

                    {/* Separator between sessions (only if not viewing a specific session) */}
                    {!selectedSessionId && groupIndex < groupedMessages.length - 1 && (
                      <hr className="border-gray-200 dark:border-gray-700" />
                    )}
                  </div>
                  );
                })}

                {groupedMessages.length === 0 && (
                  <div className="text-center p-8">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">No messages found</p>
                  </div>
                )}
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
                  <div
                    key={`${concept.name}-${concept.type}-${index}`}
                    className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => loadConceptDetails(concept.name, concept.type)}
                  >
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
          {/* Plain Text / Kuzu Graph Memory (Conversation-based) */}
          {(memoryServiceType === 'plaintext_file' || memoryServiceType === 'kuzu_graph') && (
            <Card>
              <CardHeader>
                <CardTitle>
                  {memoryServiceType === 'plaintext_file' ? '📄 Conversation Memories' : '🗄️ Graph-Based Memories'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {memoryServiceType === 'plaintext_file'
                    ? 'Memories are stored as plain text conversation logs. Use the Messages and Sessions tabs to explore conversation history.'
                    : 'Memories are stored in a graph database. Use the Messages, Sessions, and Concepts tabs to explore relationships.'}
                </p>
                <div className="flex space-x-2">
                  <Button variant="outline" onClick={() => setActiveTab('messages')}>
                    View Messages
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab('sessions')}>
                    View Sessions
                  </Button>
                  {memoryServiceType === 'kuzu_graph' && (
                    <Button variant="outline" onClick={() => setActiveTab('concepts')}>
                      View Concepts
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* LanceDB / Basic Memory (Vector-based standalone memories) */}
          {(memoryServiceType === 'lancedb_langchain' || memoryServiceType === 'lancedb_mcp' || memoryServiceType === 'basic_memory') && (
            <Card>
              <CardHeader>
                <CardTitle>
                  {memoryServiceType === 'lancedb_langchain' && '⚡ Vector Memories (LanceDB LangChain)'}
                  {memoryServiceType === 'lancedb_mcp' && '🔌 Vector Memories (LanceDB MCP)'}
                  {memoryServiceType === 'basic_memory' && '✨ Basic Memories (MCP)'}
                  {' '}({memories.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {memoryServiceType.startsWith('lancedb')
                    ? 'Memories are stored as vector embeddings for semantic search. Each memory has an importance score and vector representation.'
                    : 'Basic memories stored via Model Context Protocol for simple key-value storage.'}
                </p>
                <div className="space-y-4">
                  {memories.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No memories stored yet. Click "Add Memory" to create one.
                    </p>
                  ) : (
                    memories.map((memory) => (
                      <div key={memory.id} className="flex items-start space-x-3 p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
                        <Database className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-1" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{memory.content}</p>
                          <div className="flex items-center flex-wrap gap-3 mt-2">
                            <Badge variant="outline" className="bg-blue-100 dark:bg-blue-900">
                              ⭐ Importance: {memory.importance.toFixed(2)}
                            </Badge>
                            <p className="text-xs text-muted-foreground">
                              🕐 Created: {new Date(memory.created_at).toLocaleString()}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              👁️ Accessed: {new Date(memory.last_accessed).toLocaleString()}
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
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Disabled Memory Service */}
          {memoryServiceType === 'disabled' && (
            <Card>
              <CardHeader>
                <CardTitle>❌ Memory Disabled</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Memory service is currently disabled for this Locrit. Enable it in the settings to start storing memories.
                </p>
              </CardContent>
            </Card>
          )}
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

      {/* Concept Details Dialog */}
      <Dialog open={conceptDialogOpen} onOpenChange={setConceptDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Concept Details</DialogTitle>
          </DialogHeader>
          {conceptDetailsLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-center">
                <Brain className="h-8 w-8 mx-auto mb-4 animate-pulse" />
                <p>Loading concept details...</p>
              </div>
            </div>
          ) : conceptDetails ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Name</Label>
                  <p className="text-sm text-muted-foreground">{conceptDetails.name}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Type</Label>
                  <p className="text-sm text-muted-foreground">{conceptDetails.type}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Mentions</Label>
                  <p className="text-sm text-muted-foreground">{conceptDetails.mentions}</p>
                </div>
                {conceptDetails.first_mentioned && (
                  <div>
                    <Label className="text-sm font-medium">First Mentioned</Label>
                    <p className="text-sm text-muted-foreground">
                      {new Date(conceptDetails.first_mentioned).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>

              {conceptDetails.description && (
                <div>
                  <Label className="text-sm font-medium">Description</Label>
                  <p className="text-sm text-muted-foreground">{conceptDetails.description}</p>
                </div>
              )}

              {conceptDetails.context_examples && conceptDetails.context_examples.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Context Examples</Label>
                  <div className="space-y-2 mt-2">
                    {conceptDetails.context_examples.map((example, index) => (
                      <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={example.role === 'user' ? 'default' : 'secondary'} className="text-xs">
                            {example.role === 'user' ? '👤 User' : '🤖 Assistant'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(example.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm">{example.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {conceptDetails.related_concepts && conceptDetails.related_concepts.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Related Concepts</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {conceptDetails.related_concepts.map((relatedConcept, index) => (
                      <Badge key={index} variant="secondary" className="cursor-pointer hover:bg-gray-300"
                             onClick={() => {
                               setConceptDialogOpen(false);
                               loadConceptDetails(relatedConcept.name, relatedConcept.type);
                             }}>
                        {relatedConcept.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {conceptDetails.last_mentioned && (
                <div>
                  <Label className="text-sm font-medium">Last Mentioned</Label>
                  <p className="text-sm text-muted-foreground">
                    {new Date(conceptDetails.last_mentioned).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center p-8">
              <p className="text-muted-foreground">No concept details available</p>
            </div>
          )}
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