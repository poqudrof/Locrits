import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Alert, AlertDescription } from "./ui/alert";
import { Sparkles, Heart, User, Mail, Lock, Wand2, AlertCircle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { GoogleSignInButton } from "./GoogleSignInButton";

export function LoginForm() {
  const { signInAnonymously, signInWithCredentials, signInWithGoogleSSO, signUp, error, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);

  const handleAnonymousLogin = async () => {
    await signInAnonymously();
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSignUp) {
      await signUp(email, password, displayName);
    } else {
      await signInWithCredentials(email, password);
    }
  };

  const handleGoogleLogin = async () => {
    await signInWithGoogleSSO();
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md shadow-lg border border-gray-200">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4 border">
            <Sparkles className="h-8 w-8 text-gray-600" />
          </div>
          <CardTitle className="text-2xl mb-2 text-gray-900">
            Monde des Locrits
          </CardTitle>
          <CardDescription className="text-base text-gray-600">
            Bienvenue dans l'univers des Locrits
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <AlertDescription className="text-red-700">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="anonymous" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6 bg-gray-100 p-1 rounded-lg">
              <TabsTrigger 
                value="anonymous" 
                className="rounded-md data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm"
              >
                <Wand2 className="w-4 h-4 mr-2" />
                Visiteur
              </TabsTrigger>
              <TabsTrigger 
                value="account"
                className="rounded-md data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm"
              >
                <User className="w-4 h-4 mr-2" />
                Mon Compte
              </TabsTrigger>
            </TabsList>

            <TabsContent value="anonymous" className="space-y-4">
              <div className="text-center space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-700 mb-3">
                    Découvre le monde des Locrits sans créer de compte
                  </p>
                  <div className="flex items-center justify-center space-x-2 text-xs text-gray-600">
                    <span>Navigation anonyme</span>
                    <span>•</span>
                    <span>Accès instantané</span>
                  </div>
                </div>
                
                <Button
                  onClick={handleAnonymousLogin}
                  disabled={isLoading}
                  className="w-full bg-gray-900 hover:bg-gray-800 text-white py-3 rounded-lg shadow-sm transition-colors duration-200"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Connexion...
                    </div>
                  ) : (
                    <>
                      <Heart className="mr-2 h-4 w-4" />
                      Entrer comme visiteur
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="account" className="space-y-4">
              <div className="text-center mb-4">
                <Tabs defaultValue="signin" className="w-full">
                  <TabsList className="grid w-full grid-cols-2 bg-gray-100 p-1 rounded-lg">
                    <TabsTrigger 
                      value="signin"
                      onClick={() => setIsSignUp(false)}
                      className="rounded-md data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm"
                    >
                      Connexion
                    </TabsTrigger>
                    <TabsTrigger 
                      value="signup"
                      onClick={() => setIsSignUp(true)}
                      className="rounded-md data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm"
                    >
                      Inscription
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Bouton Google SSO */}
              <GoogleSignInButton onClick={handleGoogleLogin} isLoading={isLoading} />

              <form onSubmit={handleEmailLogin} className="space-y-4">
                {isSignUp && (
                  <div className="space-y-2">
                    <Label htmlFor="displayName" className="flex items-center gap-2 text-gray-700">
                      <User className="w-4 h-4 text-gray-500" />
                      Nom d'affichage
                    </Label>
                    <Input
                      id="displayName"
                      type="text"
                      placeholder="Ex: Gardien des Locrits"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      required={isSignUp}
                      className="bg-white border-gray-300 focus:border-gray-500 rounded-lg"
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email" className="flex items-center gap-2 text-gray-700">
                    <Mail className="w-4 h-4 text-gray-500" />
                    Adresse email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="ton-email@exemple.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="bg-white border-gray-300 focus:border-gray-500 rounded-lg"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="flex items-center gap-2 text-gray-700">
                    <Lock className="w-4 h-4 text-gray-500" />
                    Mot de passe
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Au moins 6 caractères"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="bg-white border-gray-300 focus:border-gray-500 rounded-lg"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 rounded-lg shadow-sm bg-gray-900 hover:bg-gray-800 text-white transition-colors duration-200"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {isSignUp ? 'Création du compte...' : 'Connexion...'}
                    </div>
                  ) : (
                    <>
                      <Heart className="mr-2 h-4 w-4" />
                      {isSignUp ? 'Créer mon compte' : 'Se connecter'}
                    </>
                  )}
                </Button>
              </form>

              {!isSignUp && (
                <div className="text-center">
                  <Button
                    variant="ghost"
                    onClick={() => setIsSignUp(true)}
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Pas encore de compte ? Créer un compte
                  </Button>
                </div>
              )}
            </TabsContent>
          </Tabs>

          <div className="text-center pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Figma Make • Plateforme sécurisée par Firebase
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}