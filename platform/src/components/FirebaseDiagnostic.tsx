import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { CheckCircle, XCircle, Loader2, Database, Users, MessageSquare } from 'lucide-react';
import { testFirebaseConnection, initializeFirebaseData } from '../firebase/setup';
import { userService, locritService, messageService, conversationService } from '../firebase/services';

interface DiagnosticResult {
  name: string;
  status: 'success' | 'error' | 'loading' | 'pending';
  message: string;
  details?: any;
}

export function FirebaseDiagnostic() {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const updateResult = (name: string, status: DiagnosticResult['status'], message: string, details?: any) => {
    setResults(prev => {
      const existing = prev.find(r => r.name === name);
      const newResult = { name, status, message, details };
      
      if (existing) {
        return prev.map(r => r.name === name ? newResult : r);
      } else {
        return [...prev, newResult];
      }
    });
  };

  const runDiagnostic = async () => {
    setIsRunning(true);
    setResults([]);

    const tests = [
      {
        name: 'Connexion Firebase',
        test: async () => {
          updateResult('Connexion Firebase', 'loading', 'Test de connexion...');
          const connected = await testFirebaseConnection();
          if (connected) {
            updateResult('Connexion Firebase', 'success', 'Connexion réussie');
          } else {
            updateResult('Connexion Firebase', 'error', 'Échec de la connexion');
          }
        }
      },
      {
        name: 'Service Utilisateurs',
        test: async () => {
          updateResult('Service Utilisateurs', 'loading', 'Test du service utilisateurs...');
          try {
            const users = await userService.getUsers();
            updateResult('Service Utilisateurs', 'success', `${users.length} utilisateurs trouvés`, users);
          } catch (error) {
            updateResult('Service Utilisateurs', 'error', `Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}`, error);
          }
        }
      },
      {
        name: 'Service Locrits',
        test: async () => {
          updateResult('Service Locrits', 'loading', 'Test du service Locrits...');
          try {
            const locrits = await locritService.getLocrits();
            updateResult('Service Locrits', 'success', `${locrits.length} Locrits trouvés`, locrits);
          } catch (error) {
            updateResult('Service Locrits', 'error', `Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}`, error);
          }
        }
      },
      {
        name: 'Service Conversations',
        test: async () => {
          updateResult('Service Conversations', 'loading', 'Test du service conversations...');
          try {
            const conversations = await conversationService.getActiveConversations();
            updateResult('Service Conversations', 'success', `${conversations.length} conversations trouvées`, conversations);
          } catch (error) {
            updateResult('Service Conversations', 'error', `Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}`, error);
          }
        }
      }
    ];

    // Exécuter tous les tests
    for (const { test } of tests) {
      try {
        await test();
      } catch (error) {
        console.error('Erreur lors du test:', error);
      }
    }

    setIsRunning(false);
  };

  const initializeData = async () => {
    setIsRunning(true);
    try {
      updateResult('Migration des données', 'loading', 'Migration en cours...');
      await initializeFirebaseData();
      updateResult('Migration des données', 'success', 'Données migrées avec succès');
    } catch (error) {
      updateResult('Migration des données', 'error', `Erreur lors de la migration: ${error instanceof Error ? error.message : 'Erreur inconnue'}`, error);
    }
    setIsRunning(false);
  };

  const getStatusIcon = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'loading':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <div className="h-4 w-4 rounded-full bg-gray-300" />;
    }
  };

  const getStatusColor = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'loading':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Diagnostic Firebase
        </CardTitle>
        <CardDescription>
          Vérifiez l'état de la configuration Firebase et des services
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button onClick={runDiagnostic} disabled={isRunning}>
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Test en cours...
              </>
            ) : (
              'Lancer le diagnostic'
            )}
          </Button>
          <Button onClick={initializeData} disabled={isRunning} variant="outline">
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Migration...
              </>
            ) : (
              'Migrer les données mockup'
            )}
          </Button>
        </div>

        {results.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-medium">Résultats du diagnostic :</h3>
            {results.map((result) => (
              <div key={result.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(result.status)}
                  <div>
                    <div className="font-medium">{result.name}</div>
                    <div className="text-sm text-gray-600">{result.message}</div>
                  </div>
                </div>
                <Badge className={getStatusColor(result.status)}>
                  {result.status}
                </Badge>
              </div>
            ))}
          </div>
        )}

        <Alert>
          <AlertDescription>
            <strong>Instructions :</strong>
            <br />
            1. Assurez-vous que les règles de sécurité Firestore sont déployées
            <br />
            2. Vérifiez que l'authentification est activée dans la console Firebase
            <br />
            3. Utilisez "Migrer les données mockup" pour initialiser Firebase avec des données de test
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}