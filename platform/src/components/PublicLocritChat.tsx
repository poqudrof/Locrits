import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';

interface LocritPublicInfo {
  name: string;
  description: string;
  model: string;
  public_address?: string;
  page_config: {
    title: string;
    description: string;
    welcome_message: string;
    theme: string;
    avatar: string;
    custom_css?: string;
    show_model_info?: boolean;
  };
  active: boolean;
}

interface ChatMessage {
  id: string;
  sender: 'visitor' | 'locrit';
  content: string;
  timestamp: Date;
}

const BACKEND_URL = 'http://localhost:5000';

export const PublicLocritChat: React.FC = () => {
  const { locritName } = useParams<{ locritName: string }>();
  const navigate = useNavigate();

  const [locritInfo, setLocritInfo] = useState<LocritPublicInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // État du chat
  const [visitorName, setVisitorName] = useState('');
  const [hasEnteredName, setHasEnteredName] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);

  // Charger les informations du Locrit
  useEffect(() => {
    const loadLocritInfo = async () => {
      if (!locritName) return;

      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${BACKEND_URL}/public/${encodeURIComponent(locritName)}`);
        const data = await response.json();

        if (data.success) {
          setLocritInfo(data.locrit);

          // Ajouter le message de bienvenue
          setMessages([{
            id: '1',
            sender: 'locrit',
            content: data.locrit.page_config.welcome_message,
            timestamp: new Date()
          }]);
        } else {
          setError(data.error || 'Locrit non accessible');
        }
      } catch (err) {
        console.error('Erreur lors du chargement du Locrit:', err);
        setError('Impossible de contacter le Locrit');
      } finally {
        setLoading(false);
      }
    };

    loadLocritInfo();
  }, [locritName]);

  const handleEnterName = () => {
    if (visitorName.trim()) {
      setHasEnteredName(true);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !locritName) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'visitor',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSending(true);

    try {
      const response = await fetch(`${BACKEND_URL}/public/${encodeURIComponent(locritName)}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          visitor_name: visitorName,
          message: inputMessage
        })
      });

      const data = await response.json();

      if (data.success) {
        const locritMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'locrit',
          content: data.response,
          timestamp: new Date(data.timestamp)
        };

        setMessages(prev => [...prev, locritMessage]);
      } else {
        // Afficher l'erreur comme message du système
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'locrit',
          content: `Erreur: ${data.error}`,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      console.error('Erreur lors de l\'envoi du message:', err);

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'locrit',
        content: 'Erreur de connexion. Veuillez réessayer.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="text-red-600">Erreur</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">{error}</p>
            <Button onClick={() => navigate('/')} variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!locritInfo) {
    return null;
  }

  // Page de saisie du nom
  if (!hasEnteredName) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="text-6xl mb-4">{locritInfo.page_config.avatar}</div>
            <CardTitle className="text-2xl">{locritInfo.page_config.title}</CardTitle>
            <CardDescription>{locritInfo.page_config.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quel est votre nom ?
              </label>
              <Input
                type="text"
                placeholder="Entrez votre nom"
                value={visitorName}
                onChange={(e) => setVisitorName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleEnterName()}
                autoFocus
              />
            </div>
            <Button
              className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
              onClick={handleEnterName}
              disabled={!visitorName.trim()}
            >
              Commencer la conversation
            </Button>
            {locritInfo.page_config.show_model_info && (
              <div className="text-xs text-gray-500 text-center">
                Propulsé par {locritInfo.model}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Interface de chat
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <Card className="mb-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-4xl">{locritInfo.page_config.avatar}</div>
                <div>
                  <CardTitle>{locritInfo.name}</CardTitle>
                  <CardDescription>{locritInfo.description}</CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="default">En ligne</Badge>
                <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Quitter
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Chat Messages */}
        <Card className="mb-4">
          <CardContent className="p-6">
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'visitor' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-lg ${
                      message.sender === 'visitor'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs opacity-70">
                        {message.sender === 'visitor' ? visitorName : locritInfo.name}
                      </span>
                      <span className="text-xs opacity-50">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Input */}
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="Écrivez votre message..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="min-h-[60px]"
                disabled={sending}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || sending}
                className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Appuyez sur Entrée pour envoyer, Shift+Entrée pour une nouvelle ligne
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
