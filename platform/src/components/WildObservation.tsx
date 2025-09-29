import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { Eye, Sparkles, Clock, Users, MessageCircle, Play, Pause } from "lucide-react";
import { Conversation, ChatMessage, Locrit } from "../types";

interface WildObservationProps {
  conversations: Conversation[];
  messages: ChatMessage[];
  locrits: Locrit[];
}

export function WildObservation({ conversations, messages, locrits }: WildObservationProps) {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [isWatching, setIsWatching] = useState(false);

  // Filtrer les conversations entre Locrits seulement
  const locritConversations = conversations.filter(conv => conv.type === 'locrit-locrit');

  const getLocritById = (id: string) => locrits.find(l => l.id === id);

  const getConversationMessages = (conversationId: string) => 
    messages.filter(msg => msg.conversationId === conversationId)
           .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const formatLastActivity = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "À l'instant";
    if (minutes < 60) return `Il y a ${minutes}min`;
    if (hours < 24) return `Il y a ${hours}h`;
    return `Il y a ${days}j`;
  };

  const getLocritEmoji = (locritName: string) => {
    if (locritName.includes('Pixie')) return '✨';
    if (locritName.includes('Nova')) return '⭐';
    if (locritName.includes('Iris')) return '🦋';
    if (locritName.includes('Buddy')) return '🧸';
    return '🌟';
  };

  const selectedMessages = selectedConversation ? getConversationMessages(selectedConversation) : [];
  const selectedConv = selectedConversation ? conversations.find(c => c.id === selectedConversation) : null;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <Card className="locrit-card shadow-xl">
        <CardHeader className="bg-gradient-to-r from-green-400 to-blue-500 text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                <Eye className="h-6 w-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-white text-2xl">🌿 Observation Sauvage</CardTitle>
                <CardDescription className="text-white/80 text-lg">
                  Découvrez les conversations magiques entre Locrits
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge className="bg-white/20 text-white border-white/30">
                <Sparkles className="w-3 h-3 mr-1" />
                {locritConversations.filter(c => c.isActive).length} conversations actives
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Liste des conversations */}
        <div className="lg:col-span-2">
          <Card className="locrit-card shadow-lg h-[600px]">
            <CardHeader className="pb-3">
              <CardTitle className="gradient-text flex items-center gap-2">
                <Users className="h-5 w-5" />
                Conversations entre Locrits
              </CardTitle>
              <CardDescription>
                Observez les échanges fascinants de vos compagnons
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[480px]">
                <div className="p-4 space-y-3">
                  {locritConversations.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Eye className="h-8 w-8 text-green-400" />
                      </div>
                      <p className="text-gray-500">Aucune conversation entre Locrits pour le moment</p>
                    </div>
                  ) : (
                    locritConversations.map((conversation) => (
                      <Card
                        key={conversation.id}
                        className={`cursor-pointer transition-all border-2 hover:shadow-md ${
                          selectedConversation === conversation.id
                            ? 'border-green-400 bg-green-50'
                            : 'border-gray-200 hover:border-green-300'
                        }`}
                        onClick={() => setSelectedConversation(conversation.id)}
                      >
                        <CardContent className="p-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="font-semibold text-sm">{conversation.title}</h4>
                              {conversation.isActive && (
                                <Badge className="bg-gradient-to-r from-green-400 to-blue-400 text-white border-0 text-xs">
                                  <div className="w-1.5 h-1.5 bg-white rounded-full mr-1 animate-pulse" />
                                  Live
                                </Badge>
                              )}
                            </div>
                            
                            <div className="flex items-center justify-between text-xs text-gray-600">
                              <div className="flex items-center gap-1">
                                {conversation.participants.map((participant, index) => (
                                  <span key={participant.id} className="flex items-center">
                                    <span>{getLocritEmoji(participant.name)}</span>
                                    <span className="ml-1">{participant.name.split(' ')[0]}</span>
                                    {index < conversation.participants.length - 1 && (
                                      <span className="mx-1">•</span>
                                    )}
                                  </span>
                                ))}
                              </div>
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {formatLastActivity(conversation.lastActivity)}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Zone de conversation */}
        <div className="lg:col-span-3">
          <Card className="locrit-card shadow-lg h-[600px]">
            {!selectedConversation ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageCircle className="h-10 w-10 text-green-400" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-600 mb-2">Sélectionnez une conversation</h3>
                  <p className="text-gray-500">Choisissez une discussion entre Locrits pour l'observer</p>
                </div>
              </div>
            ) : (
              <>
                <CardHeader className="bg-gradient-to-r from-green-100 to-blue-100 border-b">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="gradient-text text-lg">{selectedConv?.title}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        {selectedConv?.participants.map((participant, index) => (
                          <div key={participant.id} className="flex items-center">
                            <Avatar className="w-6 h-6">
                              <AvatarFallback className="text-xs bg-gradient-to-br from-purple-400 to-pink-400 text-white">
                                {getLocritEmoji(participant.name)}
                              </AvatarFallback>
                            </Avatar>
                            <span className="ml-1 text-sm text-gray-600">{participant.name}</span>
                            {index < selectedConv.participants.length - 1 && (
                              <span className="mx-2 text-gray-400">•</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsWatching(!isWatching)}
                      className={`${isWatching ? 'bg-green-100 border-green-300 text-green-700' : ''}`}
                    >
                      {isWatching ? (
                        <>
                          <Pause className="w-4 h-4 mr-1" />
                          Pause
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-1" />
                          Observer
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="p-0">
                  <ScrollArea className="h-[480px] p-4">
                    <div className="space-y-4">
                      {selectedMessages.length === 0 ? (
                        <div className="text-center py-12">
                          <p className="text-gray-500">Aucun message dans cette conversation</p>
                        </div>
                      ) : (
                        selectedMessages.map((message, index) => {
                          const isNewDay = index === 0 || 
                            message.timestamp.toDateString() !== selectedMessages[index - 1].timestamp.toDateString();
                          
                          return (
                            <div key={message.id}>
                              {isNewDay && (
                                <div className="text-center my-4">
                                  <Separator className="mb-2" />
                                  <span className="text-xs text-gray-500 bg-white px-3 py-1 rounded-full border">
                                    {message.timestamp.toLocaleDateString('fr-FR', {
                                      weekday: 'long',
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric'
                                    })}
                                  </span>
                                  <Separator className="mt-2" />
                                </div>
                              )}
                              
                              <div className="flex items-start gap-3">
                                <Avatar className="w-8 h-8 flex-shrink-0">
                                  <AvatarFallback className="text-sm bg-gradient-to-br from-purple-400 to-pink-400 text-white">
                                    {getLocritEmoji(message.senderName)}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-baseline gap-2 mb-1">
                                    <span className="font-semibold text-sm text-gray-800">
                                      {message.senderName}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      {formatTime(message.timestamp)}
                                    </span>
                                  </div>
                                  <div className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 border">
                                    {message.content}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}