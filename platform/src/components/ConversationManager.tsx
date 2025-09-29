import { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ArrowLeft, Plus, MessageCircle, Trash2, Clock, Users } from "lucide-react";
import { Conversation, Locrit } from "../types";

interface ConversationManagerProps {
  locrit: Locrit;
  conversations: Conversation[];
  onSelectConversation: (conversationId: string) => void;
  onCreateConversation: (title: string) => void;
  onDeleteConversation: (conversationId: string) => void;
  onBack: () => void;
}

export function ConversationManager({
  locrit,
  conversations,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  onBack
}: ConversationManagerProps) {
  const [newConversationTitle, setNewConversationTitle] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // Filtrer les conversations pour ce Locrit
  const locritConversations = conversations.filter(conv => 
    conv.participants.some(p => p.id === locrit.id && p.type === 'locrit')
  );

  const handleCreateConversation = () => {
    if (newConversationTitle.trim()) {
      onCreateConversation(newConversationTitle.trim());
      setNewConversationTitle("");
      setIsCreateDialogOpen(false);
    }
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

  return (
    <Card className="max-w-4xl mx-auto locrit-card shadow-2xl">
      <CardHeader className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-t-lg">
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
              <CardTitle className="text-white text-xl">💬 Conversations avec {locrit.name}</CardTitle>
              <p className="text-white/80">Gérez vos discussions magiques</p>
            </div>
          </div>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-white/20 hover:bg-white/30 text-white border-white/30">
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle conversation
              </Button>
            </DialogTrigger>
            <DialogContent className="locrit-card">
              <DialogHeader>
                <DialogTitle className="gradient-text">✨ Créer une nouvelle conversation</DialogTitle>
                <DialogDescription>
                  Donnez un titre magique à votre nouvelle discussion avec {locrit.name}
                </DialogDescription>
              </DialogHeader>
              <Input
                placeholder="🌟 Titre de la conversation..."
                value={newConversationTitle}
                onChange={(e) => setNewConversationTitle(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateConversation()}
                className="border-2 border-purple-200 focus:border-purple-400"
              />
              <DialogFooter>
                <Button
                  onClick={handleCreateConversation}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                  disabled={!newConversationTitle.trim()}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Créer
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {locritConversations.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="h-10 w-10 text-purple-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-600 mb-2">Aucune conversation encore</h3>
            <p className="text-gray-500 mb-6">Commencez votre première discussion magique avec {locrit.name} !</p>
            <Button
              onClick={() => setIsCreateDialogOpen(true)}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Première conversation
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold gradient-text">
                {locritConversations.length} conversation{locritConversations.length > 1 ? 's' : ''} active{locritConversations.length > 1 ? 's' : ''}
              </h3>
            </div>

            <div className="grid gap-4">
              {locritConversations.map((conversation) => (
                <Card
                  key={conversation.id}
                  className="hover:shadow-lg transition-all cursor-pointer border-2 border-purple-100 hover:border-purple-300"
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="font-bold text-gray-800">{conversation.title}</h4>
                          {conversation.isActive && (
                            <Badge className="bg-gradient-to-r from-green-400 to-blue-400 text-white border-0">
                              <div className="w-2 h-2 bg-white rounded-full mr-1 animate-pulse" />
                              Active
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {conversation.participants.length} participant{conversation.participants.length > 1 ? 's' : ''}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatLastActivity(conversation.lastActivity)}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectConversation(conversation.id);
                          }}
                          className="text-purple-600 hover:bg-purple-100"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteConversation(conversation.id);
                          }}
                          className="text-red-500 hover:bg-red-100"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}