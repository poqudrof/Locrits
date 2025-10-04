import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Users, Sparkles, Heart, Zap, Star, MessageCircle } from "lucide-react";
import { User, Locrit } from "../types";

interface DashboardProps {
  users: User[];
  locrits: Locrit[];
}

export function Dashboard({ users, locrits }: DashboardProps) {
  const onlineUsers = users.filter(u => u.isOnline).length;
  const onlineLocrits = locrits.filter(l => l.isOnline).length;
  const totalMessages = 1247; // Mock data
  const activeChats = 23; // Mock data

  const recentActivity = [
    { user: "Alice Martin", action: "a réveillé son Locrit 'Pixie l'Organisateur' ✨", time: "Il y a 5min" },
    { user: "Bob Dupont", action: "a configuré les pouvoirs de 'Buddy le Bienveillant' 🧸", time: "Il y a 12min" },
    { user: "Claire Rousseau", action: "a commencé une aventure avec Nova la Curieuse ⭐", time: "Il y a 18min" },
    { user: "David Chen", action: "a créé un nouveau Locrit 'Iris l'Imaginative' 🦋", time: "Il y a 25min" },
  ];

  return (
    <div className="space-y-6">
      {/* Statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200 shadow-lg hover:shadow-xl transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-blue-800">Amis dans le monde</CardTitle>
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-full flex items-center justify-center">
              <Users className="h-4 w-4 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-800">{users.length}</div>
            <p className="text-xs text-blue-600">
              <span className="text-green-600">🟢 {onlineUsers} en ligne</span>
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200 shadow-lg hover:shadow-xl transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-purple-800">Locrits éveillés</CardTitle>
            <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white animate-pulse" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-800">{onlineLocrits}</div>
            <p className="text-xs text-purple-600">
              sur {locrits.length} compagnons magiques
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 shadow-lg hover:shadow-xl transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-green-800">Messages magiques</CardTitle>
            <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center">
              <MessageCircle className="h-4 w-4 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-800">{totalMessages}</div>
            <p className="text-xs text-green-600">
              ✨ +180 aujourd'hui
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-yellow-50 border-orange-200 shadow-lg hover:shadow-xl transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-orange-800">Aventures en cours</CardTitle>
            <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center">
              <Star className="h-4 w-4 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-800">{activeChats}</div>
            <p className="text-xs text-orange-600">
              🎮 histoires fantastiques
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Utilisation de la plateforme */}
      <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200 shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Heart className="h-6 w-6 text-purple-600" />
            <div>
              <CardTitle className="text-purple-800">Énergie du monde magique</CardTitle>
              <CardDescription className="text-purple-600">Activité de tes Locrits enchantés</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-purple-700">✨ Locrits éveillés</span>
              <span className="text-sm text-purple-600 font-medium">
                {onlineLocrits}/{locrits.length}
              </span>
            </div>
            <Progress 
              value={(onlineLocrits / locrits.length) * 100} 
              className="h-3 bg-purple-100"
            />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-purple-700">🌟 Amis connectés</span>
              <span className="text-sm text-purple-600 font-medium">
                {onlineUsers}/{users.length}
              </span>
            </div>
            <Progress 
              value={(onlineUsers / users.length) * 100} 
              className="h-3 bg-purple-100"
            />
          </div>
        </CardContent>
      </Card>

      {/* Activité récente */}
      <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200 shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-emerald-600" />
            <div>
              <CardTitle className="text-emerald-800">Dernières aventures</CardTitle>
              <CardDescription className="text-emerald-600">Ce qui se passe dans le monde magique</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-3 px-4 bg-white/60 rounded-lg border border-emerald-100">
                <div className="flex-1">
                  <span className="font-medium text-emerald-800">{activity.user}</span>
                  <span className="text-emerald-700"> {activity.action}</span>
                </div>
                <Badge className="bg-gradient-to-r from-emerald-400 to-teal-400 text-white border-0 text-xs">
                  {activity.time}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}