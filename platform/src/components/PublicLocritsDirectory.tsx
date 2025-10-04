import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, MessageCircle } from 'lucide-react';

interface PublicLocrit {
  name: string;
  description: string;
  public_address?: string;
  avatar: string;
  title: string;
}

const BACKEND_URL = 'http://localhost:5000';

export const PublicLocritsDirectory: React.FC = () => {
  const navigate = useNavigate();
  const [locrits, setLocrits] = useState<PublicLocrit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPublicLocrits = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${BACKEND_URL}/public/list`);
        const data = await response.json();

        if (data.success) {
          setLocrits(data.locrits);
        } else {
          setError(data.error || 'Erreur lors du chargement');
        }
      } catch (err) {
        console.error('Erreur:', err);
        setError('Impossible de charger la liste des Locrits');
      } finally {
        setLoading(false);
      }
    };

    loadPublicLocrits();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement des Locrits publics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Annuaire des Locrits Publics
          </h1>
          <p className="text-gray-600">
            Découvrez et discutez avec les Locrits accessibles publiquement
          </p>
        </div>

        {/* Error State */}
        {error && (
          <Card className="mb-6 border-red-200">
            <CardContent className="pt-6">
              <p className="text-red-600 text-center">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Locrits Grid */}
        {locrits.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {locrits.map((locrit) => (
              <Card
                key={locrit.name}
                className="hover:shadow-xl transition-shadow cursor-pointer"
                onClick={() => navigate(`/public/${locrit.name}`)}
              >
                <CardHeader>
                  <div className="flex items-center space-x-4">
                    <div className="text-5xl">{locrit.avatar}</div>
                    <div className="flex-1">
                      <CardTitle className="text-xl">{locrit.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {locrit.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {locrit.public_address && (
                      <div className="text-xs">
                        <span className="text-gray-500">Adresse: </span>
                        <code className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
                          {locrit.public_address}
                        </code>
                      </div>
                    )}
                    <Button
                      className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/public/${locrit.name}`);
                      }}
                    >
                      <MessageCircle className="h-4 w-4 mr-2" />
                      Discuter
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <div className="text-6xl mb-4">🏠</div>
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  Aucun Locrit public disponible
                </h3>
                <p className="text-gray-600">
                  Il n'y a actuellement aucun Locrit accessible publiquement.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            💡 Pour rendre votre Locrit accessible publiquement, activez l'option "Ouvert à Internet" dans les paramètres
          </p>
        </div>
      </div>
    </div>
  );
};
