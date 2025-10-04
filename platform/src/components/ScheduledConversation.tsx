import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import { Slider } from "./ui/slider";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import {
  Calendar,
  Clock,
  Users,
  Play,
  Pause,
  Square,
  Settings,
  MessageCircle,
  Bot,
  Timer,
  Eye,
  Volume2,
  VolumeX,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Zap
} from "lucide-react";
import { Locrit, Conversation, ChatMessage, ConversationParticipant } from "../types";
import { conversationService, messageService, locritService } from "../firebase/services";

interface ScheduledConversationProps {
  availableLocrits: Locrit[];
  onConversationCreated: (conversation: Conversation) => void;
}

interface ScheduledConversationConfig {
  title: string;
  topic: string;
  duration: number; // in minutes
  participants: string[]; // Locrit IDs
  autoStart: boolean;
  scheduledFor: Date | null;
  messageFrequency: number; // seconds between messages
  maxMessages: number;
  conversationStyle: 'casual' | 'formal' | 'debate' | 'creative';
}

interface LiveConversationState {
  isRunning: boolean;
  conversation: Conversation | null;
  messages: ChatMessage[];
  timeRemaining: number;
  messageCount: number;
  currentSpeaker: string | null;
}

export function ScheduledConversation({ availableLocrits, onConversationCreated }: ScheduledConversationProps) {
  const [config, setConfig] = useState<ScheduledConversationConfig>({
    title: "",
    topic: "",
    duration: 2, // Default 2 minutes
    participants: [],
    autoStart: false,
    scheduledFor: null,
    messageFrequency: 10, // 10 seconds between messages
    maxMessages: 20,
    conversationStyle: 'casual'
  });

  const [liveState, setLiveState] = useState<LiveConversationState>({
    isRunning: false,
    conversation: null,
    messages: [],
    timeRemaining: 0,
    messageCount: 0,
    currentSpeaker: null
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Available conversation topics
  const suggestedTopics = [
    "L'intelligence artificielle et l'avenir de l'humanité",
    "Comment créer le parfait jardin magique",
    "Les secrets de l'organisation parfaite",
    "L'art de la conversation entre IA",
    "Résoudre les mystères de l'univers",
    "Créer de la poésie ensemble",
    "Débat: Chat ou chien?",
    "Inventer une nouvelle recette magique",
    "Planifier la journée idéale",
    "Explorer les émotions artificielles"
  ];

  const conversationStyles = [
    { value: 'casual', label: 'Décontracté', description: 'Conversation amicale et détendue' },
    { value: 'formal', label: 'Formel', description: 'Discussion structurée et professionnelle' },
    { value: 'debate', label: 'Débat', description: 'Échange argumenté avec positions opposées' },
    { value: 'creative', label: 'Créatif', description: 'Brainstorming et exploration d\'idées' }
  ];

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (liveState.isRunning && liveState.timeRemaining > 0) {
      interval = setInterval(() => {
        setLiveState(prev => ({
          ...prev,
          timeRemaining: Math.max(0, prev.timeRemaining - 1)
        }));
      }, 1000);
    } else if (liveState.isRunning && liveState.timeRemaining === 0) {
      // Conversation ended
      endConversation();
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [liveState.isRunning, liveState.timeRemaining]);

  const toggleParticipant = (locritId: string) => {
    setConfig(prev => ({
      ...prev,
      participants: prev.participants.includes(locritId)
        ? prev.participants.filter(id => id !== locritId)
        : [...prev.participants, locritId]
    }));
  };

  const startConversation = async () => {
    if (config.participants.length < 2) {
      alert("Veuillez sélectionner au moins 2 Locrits pour la conversation.");
      return;
    }

    if (!config.title.trim() || !config.topic.trim()) {
      alert("Veuillez remplir le titre et le sujet de la conversation.");
      return;
    }

    setIsLoading(true);

    try {
      // Create conversation participants
      const participants: ConversationParticipant[] = config.participants.map(locritId => {
        const locrit = availableLocrits.find(l => l.id === locritId)!;
        return {
          id: locritId,
          name: locrit.name,
          type: 'locrit',
          joinedAt: new Date(),
          role: 'participant'
        };
      });

      // Create conversation
      const conversation: Omit<Conversation, 'id'> = {
        title: config.title,
        type: 'locrit-locrit',
        participants,
        createdBy: 'system', // System-generated conversation
        topic: config.topic,
        duration: config.duration,
        status: 'active',
        isActive: true,
        isScheduled: true,
        scheduledFor: config.scheduledFor || new Date(),
        lastActivity: new Date(),
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: {
          messageCount: 0,
          averageResponseTime: config.messageFrequency,
          topics: [config.topic],
          sentiment: 'neutral',
          language: 'fr'
        }
      };

      const conversationId = await conversationService.createConversation(conversation);
      const fullConversation = { ...conversation, id: conversationId };

      // Initialize live state
      setLiveState({
        isRunning: true,
        conversation: fullConversation,
        messages: [],
        timeRemaining: config.duration * 60, // Convert minutes to seconds
        messageCount: 0,
        currentSpeaker: config.participants[0]
      });

      // Start generating messages
      generateNextMessage(conversationId, 0);

      onConversationCreated(fullConversation);

      if (soundEnabled) {
        playSound('start');
      }

    } catch (error) {
      console.error("Erreur lors de la création de la conversation:", error);
      alert("Erreur lors de la création de la conversation. Veuillez réessayer.");
    } finally {
      setIsLoading(false);
    }
  };

  const generateNextMessage = async (conversationId: string, messageIndex: number) => {
    if (!liveState.isRunning || messageIndex >= config.maxMessages) {
      return;
    }

    const speakerIndex = messageIndex % config.participants.length;
    const speakerId = config.participants[speakerIndex];
    const speaker = availableLocrits.find(l => l.id === speakerId)!;

    // Generate contextual message based on conversation style and topic
    const messageContent = generateMessage(
      speaker,
      config.topic,
      config.conversationStyle,
      messageIndex,
      liveState.messages
    );

    try {
      const message: Omit<ChatMessage, 'id'> = {
        conversationId,
        content: messageContent,
        timestamp: new Date(),
        sender: 'locrit',
        senderName: speaker.name,
        senderId: speakerId,
        isRead: false,
        messageType: 'text',
        metadata: {
          context: config.topic,
          emotion: getRandomEmotion(config.conversationStyle)
        }
      };

      const messageId = await messageService.sendMessage(message);
      const fullMessage = { ...message, id: messageId };

      // Update live state
      setLiveState(prev => ({
        ...prev,
        messages: [...prev.messages, fullMessage],
        messageCount: prev.messageCount + 1,
        currentSpeaker: speakerId
      }));

      if (soundEnabled) {
        playSound('message');
      }

      // Schedule next message
      setTimeout(() => {
        generateNextMessage(conversationId, messageIndex + 1);
      }, config.messageFrequency * 1000);

    } catch (error) {
      console.error("Erreur lors de la génération du message:", error);
    }
  };

  const generateMessage = (
    speaker: Locrit,
    topic: string,
    style: string,
    messageIndex: number,
    previousMessages: ChatMessage[]
  ): string => {
    // This is a simplified message generation - in a real implementation,
    // this would integrate with an LLM API or the Locrit's own AI system

    const messageTemplates = {
      casual: [
        `Salut ! Je trouve que ${topic.toLowerCase()} est vraiment fascinant. Qu'en pensez-vous ?`,
        `Oh, c'est une excellente question ! Pour moi, ${topic.toLowerCase()} représente...`,
        `Je ne suis pas totalement d'accord. Mon expérience avec ${topic.toLowerCase()} m'a appris que...`,
        `C'est exactement ce que je pensais ! Ajoutons à cela que...`,
        `Hmm, intéressant point de vue. Cependant, il faut aussi considérer...`
      ],
      formal: [
        `Concernant ${topic.toLowerCase()}, il convient d'analyser les aspects suivants...`,
        `Je souhaiterais apporter une perspective différente sur ${topic.toLowerCase()}...`,
        `En effet, les recherches récentes sur ${topic.toLowerCase()} démontrent que...`,
        `Permettez-moi de nuancer cette affirmation en précisant que...`,
        `Pour conclure cette réflexion sur ${topic.toLowerCase()}, il apparaît que...`
      ],
      debate: [
        `Je dois contester cette vision de ${topic.toLowerCase()}. En réalité...`,
        `Vos arguments sur ${topic.toLowerCase()} sont discutables. Voici pourquoi...`,
        `Au contraire ! ${topic.toLowerCase()} prouve exactement l'inverse...`,
        `Cette position sur ${topic.toLowerCase()} ignore un élément crucial...`,
        `Je maintiens ma position : ${topic.toLowerCase()} reste...`
      ],
      creative: [
        `Et si on imaginait ${topic.toLowerCase()} comme une métaphore de...`,
        `${topic.toLowerCase()} m'inspire une idée complètement folle...`,
        `Créons ensemble quelque chose d'unique autour de ${topic.toLowerCase()}...`,
        `Votre vision de ${topic.toLowerCase()} me fait penser à un poème...`,
        `Transformons ${topic.toLowerCase()} en une histoire magique...`
      ]
    };

    const templates = messageTemplates[style as keyof typeof messageTemplates] || messageTemplates.casual;
    const templateIndex = messageIndex % templates.length;

    // Add speaker personality
    let message = templates[templateIndex];

    // Add speaker-specific flourishes based on their description
    if (speaker.description.includes('magique') || speaker.description.includes('magie')) {
      message += ' ✨';
    }
    if (speaker.description.includes('organisateur') || speaker.description.includes('organiser')) {
      message += ' 📋';
    }

    return message;
  };

  const getRandomEmotion = (style: string): string => {
    const emotions = {
      casual: ['joyful', 'curious', 'friendly', 'excited'],
      formal: ['thoughtful', 'analytical', 'composed', 'focused'],
      debate: ['passionate', 'determined', 'confident', 'assertive'],
      creative: ['inspired', 'imaginative', 'playful', 'dreamy']
    };

    const styleEmotions = emotions[style as keyof typeof emotions] || emotions.casual;
    return styleEmotions[Math.floor(Math.random() * styleEmotions.length)];
  };

  const pauseConversation = () => {
    setLiveState(prev => ({ ...prev, isRunning: false }));
    if (soundEnabled) playSound('pause');
  };

  const resumeConversation = () => {
    setLiveState(prev => ({ ...prev, isRunning: true }));
    if (soundEnabled) playSound('resume');
  };

  const endConversation = async () => {
    if (liveState.conversation) {
      try {
        await conversationService.updateConversation(liveState.conversation.id, {
          status: 'ended',
          isActive: false,
          endedAt: new Date()
        });

        if (soundEnabled) playSound('end');
      } catch (error) {
        console.error("Erreur lors de la fin de conversation:", error);
      }
    }

    setLiveState({
      isRunning: false,
      conversation: null,
      messages: [],
      timeRemaining: 0,
      messageCount: 0,
      currentSpeaker: null
    });
  };

  const playSound = (type: 'start' | 'message' | 'pause' | 'resume' | 'end') => {
    // In a real implementation, you would play actual sound files
    // For now, we'll just log the sound type
    console.log(`🔊 Sound: ${type}`);
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const selectedLocrits = availableLocrits.filter(locrit =>
    config.participants.includes(locrit.id)
  );

  return (
    <div className="space-y-6">
      {/* Live Conversation Monitor */}
      {liveState.conversation && (
        <Card className="border-2 border-green-300 bg-gradient-to-r from-green-50 to-blue-50">
          <CardHeader className="bg-gradient-to-r from-green-500 to-blue-500 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
                <CardTitle className="text-lg">🎭 Conversation en direct: {liveState.conversation.title}</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-white/20 text-white">
                  {formatTime(liveState.timeRemaining)}
                </Badge>
                <Badge variant="secondary" className="bg-white/20 text-white">
                  {liveState.messageCount} messages
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                {liveState.isRunning ? (
                  <Button onClick={pauseConversation} variant="outline" size="sm">
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </Button>
                ) : (
                  <Button onClick={resumeConversation} variant="outline" size="sm">
                    <Play className="h-4 w-4 mr-2" />
                    Reprendre
                  </Button>
                )}
                <Button onClick={endConversation} variant="destructive" size="sm">
                  <Square className="h-4 w-4 mr-2" />
                  Terminer
                </Button>
                <Button
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  variant="ghost"
                  size="sm"
                >
                  {soundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                </Button>
              </div>

              {liveState.currentSpeaker && (
                <div className="flex items-center gap-2 text-sm">
                  <Bot className="h-4 w-4 text-blue-500" />
                  <span>
                    Tour de: {availableLocrits.find(l => l.id === liveState.currentSpeaker)?.name}
                  </span>
                </div>
              )}
            </div>

            <ScrollArea className="h-48 w-full border rounded-md p-4 bg-white">
              <div className="space-y-3">
                {liveState.messages.map((message, index) => (
                  <div key={message.id} className="flex items-start gap-3">
                    <Bot className="h-5 w-5 text-purple-500 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{message.senderName}</span>
                        <span className="text-xs text-gray-500">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{message.content}</p>
                    </div>
                  </div>
                ))}
                {liveState.messages.length === 0 && (
                  <p className="text-center text-gray-500 text-sm">
                    La conversation va commencer...
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Configuration Panel */}
      <Card className="locrit-card shadow-lg">
        <CardHeader className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <CardTitle className="flex items-center gap-2">
            <Timer className="h-5 w-5" />
            ⏰ Créer une Conversation Programmée
          </CardTitle>
          <p className="text-white/80">
            Organisez des discussions entre vos Locrits avec une durée et un sujet spécifiques
          </p>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {/* Basic Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="title" className="text-sm font-medium mb-2 block">
                Titre de la conversation
              </Label>
              <Input
                id="title"
                placeholder="Ex: Débat sur l'IA créative"
                value={config.title}
                onChange={(e) => setConfig(prev => ({ ...prev, title: e.target.value }))}
                className="border-2 border-purple-200 focus:border-purple-400"
              />
            </div>

            <div>
              <Label htmlFor="duration" className="text-sm font-medium mb-2 block">
                Durée: {config.duration} minute{config.duration > 1 ? 's' : ''}
              </Label>
              <Slider
                id="duration"
                min={1}
                max={30}
                step={1}
                value={[config.duration]}
                onValueChange={(value) => setConfig(prev => ({ ...prev, duration: value[0] }))}
                className="w-full"
              />
            </div>
          </div>

          {/* Topic Configuration */}
          <div>
            <Label htmlFor="topic" className="text-sm font-medium mb-2 block">
              Sujet de conversation
            </Label>
            <Textarea
              id="topic"
              placeholder="Décrivez le sujet que vous souhaitez que les Locrits abordent..."
              value={config.topic}
              onChange={(e) => setConfig(prev => ({ ...prev, topic: e.target.value }))}
              className="border-2 border-purple-200 focus:border-purple-400"
              rows={3}
            />

            {/* Suggested Topics */}
            <div className="mt-3">
              <p className="text-sm text-gray-600 mb-2">💡 Sujets suggérés:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedTopics.slice(0, 5).map((topic, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => setConfig(prev => ({ ...prev, topic }))}
                    className="text-xs"
                  >
                    {topic}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          {/* Participant Selection */}
          <div>
            <Label className="text-sm font-medium mb-3 block">
              Participants ({config.participants.length} sélectionné{config.participants.length > 1 ? 's' : ''})
            </Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableLocrits.map((locrit) => (
                <Card
                  key={locrit.id}
                  className={`cursor-pointer transition-all border-2 ${
                    config.participants.includes(locrit.id)
                      ? 'border-purple-400 bg-purple-50'
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                  onClick={() => toggleParticipant(locrit.id)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 text-purple-500" />
                        <div>
                          <div className="font-medium text-sm">{locrit.name}</div>
                          <div className="text-xs text-gray-500 truncate max-w-32">
                            {locrit.description}
                          </div>
                        </div>
                      </div>
                      {config.participants.includes(locrit.id) && (
                        <CheckCircle className="h-5 w-5 text-purple-500" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Advanced Settings */}
          <div>
            <Button
              variant="ghost"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="mb-4"
            >
              <Settings className="h-4 w-4 mr-2" />
              {showAdvanced ? 'Masquer' : 'Afficher'} les paramètres avancés
            </Button>

            {showAdvanced && (
              <div className="space-y-4 p-4 border-2 border-dashed border-gray-300 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium mb-2 block">
                      Style de conversation
                    </Label>
                    <select
                      value={config.conversationStyle}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        conversationStyle: e.target.value as any
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {conversationStyles.map(style => (
                        <option key={style.value} value={style.value}>
                          {style.label} - {style.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <Label className="text-sm font-medium mb-2 block">
                      Fréquence des messages: {config.messageFrequency}s
                    </Label>
                    <Slider
                      min={5}
                      max={60}
                      step={5}
                      value={[config.messageFrequency]}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        messageFrequency: value[0]
                      }))}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium mb-2 block">
                      Messages maximum: {config.maxMessages}
                    </Label>
                    <Slider
                      min={10}
                      max={100}
                      step={5}
                      value={[config.maxMessages]}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        maxMessages: value[0]
                      }))}
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="autoStart"
                      checked={config.autoStart}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        autoStart: checked
                      }))}
                    />
                    <Label htmlFor="autoStart" className="text-sm">
                      Démarrage automatique
                    </Label>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <div className="flex items-center gap-2">
              {config.participants.length < 2 && (
                <div className="flex items-center gap-2 text-orange-600 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>Sélectionnez au moins 2 Locrits</span>
                </div>
              )}
              {selectedLocrits.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">Participants:</span>
                  {selectedLocrits.map((locrit, index) => (
                    <Badge key={locrit.id} variant="secondary" className="text-xs">
                      {locrit.name}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <Button
              onClick={startConversation}
              disabled={
                isLoading ||
                config.participants.length < 2 ||
                !config.title.trim() ||
                !config.topic.trim() ||
                liveState.isRunning
              }
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Zap className="h-4 w-4 mr-2" />
              )}
              Lancer la conversation
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}