import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Send, ArrowLeft, Sparkles, Heart } from "lucide-react";
import { ChatMessage, Locrit } from "../types";

interface ChatInterfaceProps {
  locrit: Locrit;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onBack: () => void;
}

export function ChatInterface({ locrit, messages, onSendMessage, onBack }: ChatInterfaceProps) {
  console.log('ChatInterface render - messages count:', messages.length);
  const [newMessage, setNewMessage] = useState("");

  const handleSend = () => {
    if (newMessage.trim()) {
      onSendMessage(newMessage.trim());
      setNewMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className="h-[600px] flex flex-col locrit-card shadow-2xl overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-t-xl flex-shrink-0">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="text-white hover:bg-white/20"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-white">💬 Aventure avec {locrit.name}</CardTitle>
              <p className="text-white/80 text-sm">Prêt à vivre une histoire magique ?</p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0 bg-gradient-to-b from-purple-50 to-pink-50 min-h-0">
        <ScrollArea className="h-full p-4 overflow-auto">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-4 rounded-2xl shadow-lg ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                      : 'bg-white border-2 border-purple-200 text-gray-800'
                  }`}
                >
                  <div className={`text-sm font-medium mb-1 ${message.sender === 'user' ? 'text-blue-100' : 'text-purple-700'}`}>
                    {message.sender === 'user' ? '🧑‍💼 ' : '✨ '}
                    {message.senderName}
                  </div>
                  <div className="text-base">{message.content}</div>
                  <div className={`text-xs mt-2 ${message.sender === 'user' ? 'text-blue-200' : 'text-gray-500'}`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
      <CardFooter className="bg-white border-t-2 border-purple-200 rounded-b-xl flex-shrink-0 relative z-10">
        <div className="flex w-full gap-3">
          <Input
            id="chat-message-input"
            name="message"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Écris ton message magique... ✨"
            className="flex-1 border-2 border-purple-200 rounded-xl bg-purple-50 focus:border-purple-400 focus:bg-white pointer-events-auto"
            autoComplete="off"
          />
          <Button
            onClick={handleSend}
            disabled={!newMessage.trim()}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl px-6 shadow-lg disabled:from-gray-400 disabled:to-gray-500"
          >
            <Send className="h-4 w-4 mr-1" />
            <Heart className="h-3 w-3" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}