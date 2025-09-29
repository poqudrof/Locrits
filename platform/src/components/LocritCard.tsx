import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { MessageCircle, Settings, Sparkles, Moon, Heart, Users, Globe, Mail, Shield } from "lucide-react";
import { Locrit } from "../types";

interface LocritCardProps {
  locrit: Locrit;
  onChat: (locritId: string) => void;
  onSettings: (locritId: string) => void;
}

export function LocritCard({ locrit, onChat, onSettings }: LocritCardProps) {
  const formatLastSeen = (date: Date) => {
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
    <Card className="w-full locrit-card hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-2xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shadow-md ${locrit.isOnline ? 'bg-gradient-to-br from-green-400 to-emerald-500' : 'bg-gradient-to-br from-gray-400 to-gray-500'}`}>
              {locrit.isOnline ? (
                <Sparkles className="h-4 w-4 text-white animate-pulse" />
              ) : (
                <Moon className="h-4 w-4 text-white" />
              )}
            </div>
            <Badge className={`${locrit.isOnline ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-gray-400 to-gray-500'} text-white border-0 shadow-md`}>
              {locrit.isOnline ? "🌟 Éveillé" : "💤 Endormi"}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground bg-white/80 px-2 py-1 rounded-full">
            {formatLastSeen(locrit.lastSeen)}
          </span>
        </div>
        <CardTitle className="text-xl font-bold text-purple-800">{locrit.name}</CardTitle>
        <CardDescription className="text-base text-gray-600">{locrit.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-3 rounded-lg">
          <div className="text-sm">
            <span className="font-medium text-purple-700">🏠 Maison magique:</span> 
            <span className="text-purple-600 ml-1">{locrit.publicAddress}</span>
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">🤝 Peut jouer avec:</p>
          <div className="flex flex-wrap gap-2">
            {locrit.settings.openTo.humans && (
              <Badge variant="outline" className="bg-blue-50 border-blue-200 text-blue-700">
                <Users className="w-3 h-3 mr-1" />
                Humains
              </Badge>
            )}
            {locrit.settings.openTo.locrits && (
              <Badge variant="outline" className="bg-purple-50 border-purple-200 text-purple-700">
                <Sparkles className="w-3 h-3 mr-1" />
                Locrits
              </Badge>
            )}
            {locrit.settings.openTo.invitations && (
              <Badge variant="outline" className="bg-pink-50 border-pink-200 text-pink-700">
                <Mail className="w-3 h-3 mr-1" />
                Invités
              </Badge>
            )}
            {locrit.settings.openTo.publicInternet && (
              <Badge variant="outline" className="bg-green-50 border-green-200 text-green-700">
                <Globe className="w-3 h-3 mr-1" />
                Monde entier
              </Badge>
            )}
            {locrit.settings.openTo.publicPlatform && (
              <Badge variant="outline" className="bg-orange-50 border-orange-200 text-orange-700">
                <Shield className="w-3 h-3 mr-1" />
                Plateforme
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-3 pt-4">
        <Button 
          onClick={() => onChat(locrit.id)} 
          disabled={!locrit.isOnline}
          className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl shadow-lg disabled:from-gray-400 disabled:to-gray-500"
        >
          <MessageCircle className="mr-2 h-4 w-4" />
          {locrit.isOnline ? "💬 Discuter" : "😴 Endormi"}
        </Button>
        <Button 
          variant="outline" 
          onClick={() => onSettings(locrit.id)}
          className="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200 hover:from-blue-100 hover:to-cyan-100 text-blue-700 rounded-xl"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}