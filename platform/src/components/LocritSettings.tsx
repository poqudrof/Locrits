import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Switch } from "./ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Separator } from "./ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { ArrowLeft, Save, Settings, Heart, Sparkles, Database, FileText, X, Zap, Network } from "lucide-react";
import { Locrit, LocritSettings } from "../types";

interface LocritSettingsProps {
  locrit: Locrit;
  onSave: (updatedLocrit: Locrit) => void;
  onBack: () => void;
}

export function LocritSettings({ locrit, onSave, onBack }: LocritSettingsProps) {
  const [formData, setFormData] = useState({
    name: locrit.name,
    description: locrit.description,
    publicAddress: locrit.publicAddress,
    settings: { ...locrit.settings }
  });

  const handleSave = () => {
    onSave({
      ...locrit,
      name: formData.name,
      description: formData.description,
      publicAddress: formData.publicAddress,
      settings: formData.settings
    });
  };

  const updateOpenTo = (key: keyof LocritSettings['openTo'], value: boolean) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        openTo: {
          ...prev.settings.openTo,
          [key]: value
        }
      }
    }));
  };

  const updateAccessTo = (key: keyof LocritSettings['accessTo'], value: boolean) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        accessTo: {
          ...prev.settings.accessTo,
          [key]: value
        }
      }
    }));
  };

  const updateMemoryService = (value: 'kuzu_graph' | 'plaintext_file' | 'basic_memory' | 'lancedb_langchain' | 'lancedb_mcp' | 'disabled') => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        memoryService: value
      }
    }));
  };

  const getMemoryServiceIcon = (type: string) => {
    switch(type) {
      case 'kuzu_graph': return <Database className="h-4 w-4" />;
      case 'plaintext_file': return <FileText className="h-4 w-4" />;
      case 'basic_memory': return <Sparkles className="h-4 w-4" />;
      case 'lancedb_langchain': return <Zap className="h-4 w-4" />;
      case 'lancedb_mcp': return <Network className="h-4 w-4" />;
      case 'disabled': return <X className="h-4 w-4" />;
      default: return <Database className="h-4 w-4" />;
    }
  };

  const getMemoryServiceInfo = (type: string) => {
    switch(type) {
      case 'kuzu_graph':
        return {
          name: "Base de données graphe Kuzu",
          desc: "Mémoire avancée avec relations et recherche sémantique",
          stability: "⚠️ Expérimental"
        };
      case 'plaintext_file':
        return {
          name: "Fichiers texte simples",
          desc: "Stockage stable et facile à lire",
          stability: "✅ Stable"
        };
      case 'basic_memory':
        return {
          name: "Basic Memory (MCP)",
          desc: "Graphe de connaissances Markdown avec recherche sémantique",
          stability: "⚠️ Expérimental"
        };
      case 'lancedb_langchain':
        return {
          name: "LanceDB (LangChain)",
          desc: "Recherche vectorielle rapide avec intégration Python native",
          stability: "✅ Stable"
        };
      case 'lancedb_mcp':
        return {
          name: "LanceDB (MCP)",
          desc: "Recherche vectorielle via protocole MCP standardisé",
          stability: "⚠️ Expérimental"
        };
      case 'disabled':
        return {
          name: "Désactivé",
          desc: "Pas de sauvegarde de mémoire",
          stability: "✅ Stable"
        };
      default:
        return {
          name: "Non configuré",
          desc: "",
          stability: ""
        };
    }
  };

  return (
    <Card className="max-w-2xl mx-auto locrit-card shadow-2xl">
      <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-xl">
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
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Settings className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-white text-xl">⚙️ Paramètres de {locrit.name}</CardTitle>
              <CardDescription className="text-white/80">Configure ton Locrit magique</CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Informations générales */}
        <div className="space-y-4 bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border-2 border-purple-200">
          <h3 className="font-bold text-purple-800 text-lg">📝 Carte d'identité magique</h3>
          <div className="grid gap-4">
            <div>
              <Label htmlFor="name" className="text-purple-700">✨ Nom du Locrit</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="border-2 border-purple-200 focus:border-purple-400 bg-white/80"
              />
            </div>
            <div>
              <Label htmlFor="description" className="text-purple-700">📖 Histoire personnelle</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="border-2 border-purple-200 focus:border-purple-400 bg-white/80"
              />
            </div>
            <div>
              <Label htmlFor="publicAddress" className="text-purple-700">🏠 Adresse de sa maison magique</Label>
              <Input
                id="publicAddress"
                value={formData.publicAddress}
                onChange={(e) => setFormData(prev => ({ ...prev, publicAddress: e.target.value }))}
                className="border-2 border-purple-200 focus:border-purple-400 bg-white/80"
              />
            </div>
          </div>
        </div>

        <Separator className="border-purple-200" />

        {/* Ouvert aux */}
        <div className="space-y-4 bg-gradient-to-br from-blue-50 to-cyan-50 p-6 rounded-xl border-2 border-blue-200">
          <h3 className="font-bold text-blue-800 text-lg">🤝 Avec qui peut-il jouer ?</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="humans" className="text-blue-700 flex items-center gap-2">
                👥 Avec les humains
              </Label>
              <Switch
                id="humans"
                checked={formData.settings.openTo.humans}
                onCheckedChange={(checked) => updateOpenTo('humans', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="locrits" className="text-blue-700 flex items-center gap-2">
                ✨ Avec d'autres Locrits
              </Label>
              <Switch
                id="locrits"
                checked={formData.settings.openTo.locrits}
                onCheckedChange={(checked) => updateOpenTo('locrits', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="invitations" className="text-blue-700 flex items-center gap-2">
                💌 Avec des invités spéciaux
              </Label>
              <Switch
                id="invitations"
                checked={formData.settings.openTo.invitations}
                onCheckedChange={(checked) => updateOpenTo('invitations', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="publicInternet" className="text-blue-700 flex items-center gap-2">
                🌍 Avec le monde entier
              </Label>
              <Switch
                id="publicInternet"
                checked={formData.settings.openTo.publicInternet}
                onCheckedChange={(checked) => updateOpenTo('publicInternet', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="publicPlatform" className="text-blue-700 flex items-center gap-2">
                🏰 Dans le royaume magique
              </Label>
              <Switch
                id="publicPlatform"
                checked={formData.settings.openTo.publicPlatform}
                onCheckedChange={(checked) => updateOpenTo('publicPlatform', checked)}
              />
            </div>
          </div>
        </div>

        <Separator className="border-purple-200" />

        {/* Memory Service Selection */}
        <div className="space-y-4 bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl border-2 border-amber-200">
          <h3 className="font-bold text-amber-800 text-lg">💾 Type de mémoire magique</h3>
          <div className="space-y-3">
            <Label htmlFor="memoryService" className="text-amber-700">
              Choisis comment ton Locrit garde ses souvenirs
            </Label>
            <Select
              value={formData.settings.memoryService || 'plaintext_file'}
              onValueChange={updateMemoryService}
            >
              <SelectTrigger className="border-2 border-amber-200 focus:border-amber-400 bg-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="plaintext_file">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span>Fichiers texte (Recommandé)</span>
                  </div>
                </SelectItem>
                <SelectItem value="lancedb_langchain">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    <span>LanceDB LangChain (Recherche vectorielle)</span>
                  </div>
                </SelectItem>
                <SelectItem value="basic_memory">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    <span>Basic Memory (MCP)</span>
                  </div>
                </SelectItem>
                <SelectItem value="lancedb_mcp">
                  <div className="flex items-center gap-2">
                    <Network className="h-4 w-4" />
                    <span>LanceDB MCP (Recherche vectorielle MCP)</span>
                  </div>
                </SelectItem>
                <SelectItem value="kuzu_graph">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    <span>Base de données Kuzu</span>
                  </div>
                </SelectItem>
                <SelectItem value="disabled">
                  <div className="flex items-center gap-2">
                    <X className="h-4 w-4" />
                    <span>Désactivé</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            {formData.settings.memoryService && (
              <div className="p-3 bg-white/60 rounded-lg text-sm">
                <p className="font-semibold text-amber-800">
                  {getMemoryServiceInfo(formData.settings.memoryService).name}
                </p>
                <p className="text-amber-600">
                  {getMemoryServiceInfo(formData.settings.memoryService).desc}
                </p>
                <p className="text-xs mt-1">
                  {getMemoryServiceInfo(formData.settings.memoryService).stability}
                </p>
              </div>
            )}
          </div>
        </div>

        <Separator className="border-purple-200" />

        {/* Accès aux */}
        <div className="space-y-4 bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border-2 border-green-200">
          <h3 className="font-bold text-green-800 text-lg">🔮 Ses pouvoirs magiques</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="logs" className="text-green-700 flex items-center gap-2">
                📜 Livre de bord des aventures
              </Label>
              <Switch
                id="logs"
                checked={formData.settings.accessTo.logs}
                onCheckedChange={(checked) => updateAccessTo('logs', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="quickMemory" className="text-green-700 flex items-center gap-2">
                ⚡ Mémoire instantanée
              </Label>
              <Switch
                id="quickMemory"
                checked={formData.settings.accessTo.quickMemory}
                onCheckedChange={(checked) => updateAccessTo('quickMemory', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="fullMemory" className="text-green-700 flex items-center gap-2">
                🧠 Mémoire des anciens
              </Label>
              <Switch
                id="fullMemory"
                checked={formData.settings.accessTo.fullMemory}
                onCheckedChange={(checked) => updateAccessTo('fullMemory', checked)}
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg">
              <Label htmlFor="llmInfo" className="text-green-700 flex items-center gap-2">
                🤖 Sagesse des ancêtres numériques
              </Label>
              <Switch
                id="llmInfo"
                checked={formData.settings.accessTo.llmInfo}
                onCheckedChange={(checked) => updateAccessTo('llmInfo', checked)}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-6">
          <Button 
            onClick={handleSave}
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-8 py-3 rounded-xl shadow-lg"
          >
            <Save className="mr-2 h-4 w-4" />
            <Heart className="mr-1 h-3 w-3" />
            Sauvegarder la magie
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}