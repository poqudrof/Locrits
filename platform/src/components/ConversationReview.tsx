import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import {
  ArrowLeft,
  MessageCircle,
  Clock,
  Users,
  Download,
  Search,
  Filter,
  BarChart3,
  Calendar,
  Eye,
  MessageSquare,
  TrendingUp,
  User,
  Bot
} from "lucide-react";
import { Conversation, ChatMessage, ConversationParticipant } from "../types";
import { messageService } from "../firebase/services";

interface ConversationReviewProps {
  conversation: Conversation;
  onBack: () => void;
}

interface ConversationStats {
  totalMessages: number;
  averageResponseTime: number;
  participantStats: Array<{
    id: string;
    name: string;
    type: 'user' | 'locrit';
    messageCount: number;
    percentage: number;
  }>;
  timelineData: Array<{
    hour: number;
    count: number;
  }>;
  sentiment: 'positive' | 'neutral' | 'negative';
  topics: string[];
}

export function ConversationReview({ conversation, onBack }: ConversationReviewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [filteredMessages, setFilteredMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedParticipant, setSelectedParticipant] = useState<string>("all");
  const [showStats, setShowStats] = useState(false);
  const [stats, setStats] = useState<ConversationStats | null>(null);

  useEffect(() => {
    loadConversationMessages();
  }, [conversation.id]);

  useEffect(() => {
    filterMessages();
  }, [messages, searchTerm, selectedParticipant]);

  const loadConversationMessages = async () => {
    try {
      setLoading(true);
      const conversationMessages = await messageService.getConversationMessages(conversation.id);
      setMessages(conversationMessages);
      calculateStats(conversationMessages);
    } catch (error) {
      console.error("Erreur lors du chargement des messages:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterMessages = () => {
    let filtered = messages;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(msg =>
        msg.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        msg.senderName.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by participant
    if (selectedParticipant !== "all") {
      filtered = filtered.filter(msg => msg.senderId === selectedParticipant);
    }

    setFilteredMessages(filtered);
  };

  const calculateStats = (msgs: ChatMessage[]) => {
    if (msgs.length === 0) return;

    // Calculate participant stats
    const participantCounts: Record<string, { name: string; type: 'user' | 'locrit'; count: number }> = {};
    msgs.forEach(msg => {
      if (!participantCounts[msg.senderId]) {
        participantCounts[msg.senderId] = {
          name: msg.senderName,
          type: msg.sender,
          count: 0
        };
      }
      participantCounts[msg.senderId].count++;
    });

    const participantStats = Object.entries(participantCounts).map(([id, data]) => ({
      id,
      name: data.name,
      type: data.type,
      messageCount: data.count,
      percentage: Math.round((data.count / msgs.length) * 100)
    }));

    // Calculate timeline data (messages per hour)
    const hourCounts: Record<number, number> = {};
    msgs.forEach(msg => {
      const hour = new Date(msg.timestamp).getHours();
      hourCounts[hour] = (hourCounts[hour] || 0) + 1;
    });

    const timelineData = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      count: hourCounts[hour] || 0
    }));

    // Simple sentiment analysis based on keywords
    const positiveWords = ['bien', 'super', 'génial', 'parfait', 'excellent', 'merci', '😊', '👍', '✨'];
    const negativeWords = ['mal', 'problème', 'erreur', 'difficile', 'impossible', '😞', '👎', '❌'];

    let positiveCount = 0;
    let negativeCount = 0;

    msgs.forEach(msg => {
      const content = msg.content.toLowerCase();
      positiveWords.forEach(word => {
        if (content.includes(word)) positiveCount++;
      });
      negativeWords.forEach(word => {
        if (content.includes(word)) negativeCount++;
      });
    });

    let sentiment: 'positive' | 'neutral' | 'negative' = 'neutral';
    if (positiveCount > negativeCount) sentiment = 'positive';
    else if (negativeCount > positiveCount) sentiment = 'negative';

    // Extract topics (simple keyword extraction)
    const topics = ['conversation', 'aide', 'question', 'réponse', 'information'];

    const calculatedStats: ConversationStats = {
      totalMessages: msgs.length,
      averageResponseTime: 2.5, // Mock data for now
      participantStats,
      timelineData,
      sentiment,
      topics
    };

    setStats(calculatedStats);
  };

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short'
    }).format(date);
  };

  const formatDuration = () => {
    const start = conversation.createdAt;
    const end = conversation.lastActivity;
    const diffMs = end.getTime() - start.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMinutes / 60);
    const minutes = diffMinutes % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}min`;
    }
    return `${minutes}min`;
  };

  const exportConversation = () => {
    const exportData = {
      conversation,
      messages: filteredMessages,
      stats,
      exportedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${conversation.title.replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Card className="max-w-6xl mx-auto locrit-card shadow-2xl">
        <CardContent className="p-8 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p>Chargement de la conversation...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-6xl mx-auto locrit-card shadow-2xl">
      <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="text-white hover:bg-white/20 rounded-xl"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <CardTitle className="text-white text-xl">📖 Révision: {conversation.title}</CardTitle>
              <p className="text-white/80">Analyse détaillée de la conversation</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowStats(!showStats)}
              className="text-white hover:bg-white/20"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              {showStats ? 'Masquer stats' : 'Voir stats'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={exportConversation}
              className="text-white hover:bg-white/20"
            >
              <Download className="h-4 w-4 mr-2" />
              Exporter
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {/* Conversation Info */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4 text-center">
              <MessageSquare className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-700">{messages.length}</div>
              <div className="text-sm text-blue-600">Messages</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-4 text-center">
              <Users className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-700">{conversation.participants.length}</div>
              <div className="text-sm text-green-600">Participants</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardContent className="p-4 text-center">
              <Clock className="h-8 w-8 text-orange-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-orange-700">{formatDuration()}</div>
              <div className="text-sm text-orange-600">Durée</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="p-4 text-center">
              <TrendingUp className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-purple-700">
                {stats?.sentiment === 'positive' ? '😊' : stats?.sentiment === 'negative' ? '😞' : '😐'}
              </div>
              <div className="text-sm text-purple-600">Sentiment</div>
            </CardContent>
          </Card>
        </div>

        {/* Stats Panel */}
        {showStats && stats && (
          <Card className="mb-6 border-2 border-dashed border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistiques détaillées
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Participant Stats */}
              <div>
                <h4 className="font-semibold mb-3">Répartition des messages</h4>
                <div className="space-y-2">
                  {stats.participantStats.map(participant => (
                    <div key={participant.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        {participant.type === 'user' ? (
                          <User className="h-4 w-4 text-blue-500" />
                        ) : (
                          <Bot className="h-4 w-4 text-purple-500" />
                        )}
                        <span className="font-medium">{participant.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-sm text-gray-600">
                          {participant.messageCount} messages ({participant.percentage}%)
                        </div>
                        <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-400 to-purple-400"
                            style={{ width: `${participant.percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Timeline */}
              <div>
                <h4 className="font-semibold mb-3">Activité par heure</h4>
                <div className="flex items-end gap-1 h-20">
                  {stats.timelineData.map(({ hour, count }) => (
                    <div key={hour} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-gradient-to-t from-blue-400 to-purple-400 rounded-t-sm min-h-1"
                        style={{
                          height: count > 0 ? `${Math.max((count / Math.max(...stats.timelineData.map(d => d.count))) * 60, 4)}px` : '2px'
                        }}
                        title={`${hour}h: ${count} messages`}
                      />
                      <div className="text-xs text-gray-500 mt-1">{hour}</div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Rechercher dans les messages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="min-w-48">
            <select
              value={selectedParticipant}
              onChange={(e) => setSelectedParticipant(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">Tous les participants</option>
              {conversation.participants.map(participant => (
                <option key={participant.id} value={participant.id}>
                  {participant.name} ({participant.type === 'user' ? 'Utilisateur' : 'Locrit'})
                </option>
              ))}
            </select>
          </div>
          {(searchTerm || selectedParticipant !== "all") && (
            <Button
              variant="outline"
              onClick={() => {
                setSearchTerm("");
                setSelectedParticipant("all");
              }}
              className="whitespace-nowrap"
            >
              Réinitialiser
            </Button>
          )}
        </div>

        {/* Messages */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Messages de la conversation
              {filteredMessages.length !== messages.length && (
                <Badge variant="secondary">
                  {filteredMessages.length} sur {messages.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-96">
              <div className="p-4 space-y-4">
                {filteredMessages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    {searchTerm || selectedParticipant !== "all" ? (
                      <p>Aucun message ne correspond aux filtres appliqués.</p>
                    ) : (
                      <p>Aucun message dans cette conversation.</p>
                    )}
                  </div>
                ) : (
                  filteredMessages.map((message, index) => (
                    <div key={message.id} className="space-y-2">
                      <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-2xl p-4 rounded-lg ${
                          message.sender === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            {message.sender === 'user' ? (
                              <User className="h-4 w-4" />
                            ) : (
                              <Bot className="h-4 w-4" />
                            )}
                            <span className="text-sm font-medium">{message.senderName}</span>
                            <span className={`text-xs ${
                              message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                            }`}>
                              {formatTimestamp(message.timestamp)}
                            </span>
                          </div>
                          <div className="whitespace-pre-wrap">{message.content}</div>
                        </div>
                      </div>

                      {index < filteredMessages.length - 1 && (
                        <Separator className="my-2 opacity-30" />
                      )}
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Conversation Metadata */}
        <Card className="mt-6">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-gray-500" />
                  <span className="font-medium">Informations</span>
                </div>
                <div className="space-y-1 text-gray-600">
                  <div>Type: {conversation.type === 'user-locrit' ? 'Utilisateur-Locrit' : 'Locrit-Locrit'}</div>
                  <div>Créée le: {formatTimestamp(conversation.createdAt)}</div>
                  <div>Dernière activité: {formatTimestamp(conversation.lastActivity)}</div>
                  <div>Statut: {conversation.isActive ? '🟢 Active' : '🔴 Inactive'}</div>
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-4 w-4 text-gray-500" />
                  <span className="font-medium">Participants</span>
                </div>
                <div className="space-y-1">
                  {conversation.participants.map(participant => (
                    <div key={participant.id} className="flex items-center gap-2 text-gray-600">
                      {participant.type === 'user' ? (
                        <User className="h-3 w-3" />
                      ) : (
                        <Bot className="h-3 w-3" />
                      )}
                      <span>{participant.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {participant.type === 'user' ? 'Utilisateur' : 'Locrit'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}