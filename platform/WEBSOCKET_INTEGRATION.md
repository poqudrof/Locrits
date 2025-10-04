# Intégration WebSocket pour le Chat

## Code à remplacer dans App.tsx

Remplace la fonction `handleSendMessage` (lignes 163-226) par ce code:

```typescript
const handleSendMessage = async (content: string) => {
  if (!selectedLocritId || !selectedLocrit) return;

  const newMessage: ChatMessage = {
    id: Date.now().toString(),
    locritId: selectedLocritId,
    content,
    timestamp: new Date(),
    sender: 'user',
    senderName: user?.displayName || 'Utilisateur actuel',
  };

  // Ajouter le message utilisateur immédiatement (optimistic update)
  setMessages(prev => [...prev, newMessage]);

  // Générer un session_id unique pour cette conversation
  const sessionId = `web_${user?.uid || 'anonymous'}_${selectedLocritId}`;

  // Connecter au WebSocket si pas déjà connecté
  try {
    if (!locritWebSocketService.getIsConnected()) {
      await locritWebSocketService.connect();
      await locritWebSocketService.joinChat(selectedLocrit.name, sessionId);
    }

    // Créer un message temporaire pour le streaming
    const streamingMessageId = (Date.now() + 1).toString();
    let streamingContent = '';

    // Envoyer le message avec streaming via WebSocket
    locritWebSocketService.sendMessage(
      selectedLocrit.name,
      sessionId,
      content,
      // onChunk: recevoir les morceaux de réponse
      (chunk) => {
        streamingContent += chunk.content;

        // Mettre à jour ou créer le message de streaming
        setMessages(prev => {
          const existing = prev.find(m => m.id === streamingMessageId);
          if (existing) {
            return prev.map(m =>
              m.id === streamingMessageId
                ? { ...m, content: streamingContent }
                : m
            );
          } else {
            return [
              ...prev,
              {
                id: streamingMessageId,
                locritId: selectedLocritId,
                content: streamingContent,
                timestamp: new Date(chunk.timestamp),
                sender: 'locrit' as const,
                senderName: selectedLocrit.name,
              },
            ];
          }
        });
      },
      // onComplete: streaming terminé
      (complete) => {
        console.log('✅ Streaming terminé:', complete);
      },
      // onError: erreur
      (error) => {
        console.error('❌ Erreur WebSocket:', error);
        const errorMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          locritId: selectedLocritId,
          content: `Erreur: ${error.message}`,
          timestamp: new Date(),
          sender: 'locrit',
          senderName: 'Système',
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    );
  } catch (error) {
    console.error('Erreur lors de la connexion WebSocket:', error);

    // Fallback: utiliser HTTP si WebSocket échoue
    try {
      const response = await locritBackendService.sendMessage(
        selectedLocrit.name,
        content,
        user?.displayName || 'Utilisateur'
      );

      if (response.success && response.response) {
        const locritResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          locritId: selectedLocritId,
          content: response.response,
          timestamp: new Date(response.timestamp),
          sender: 'locrit',
          senderName: selectedLocrit.name,
        };

        setMessages(prev => [...prev, locritResponse]);
      }
    } catch (httpError) {
      console.error('Erreur HTTP fallback:', httpError);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        locritId: selectedLocritId,
        content: `Erreur de connexion au Locrit.`,
        timestamp: new Date(),
        sender: 'locrit',
        senderName: 'Système',
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }
};
```

## Résumé

✅ **Créé:**
- `platform/src/lib/locritWebSocketService.ts` - Service WebSocket complet
- socket.io-client installé

✅ **À faire:**
- Remplacer la fonction `handleSendMessage` dans App.tsx avec le code ci-dessus

## Fonctionnalités

- **Streaming en temps réel** : Les réponses du Locrit apparaissent token par token
- **Fallback HTTP** : Si WebSocket échoue, bascule automatiquement sur HTTP
- **Reconnexion automatique** : Le WebSocket se reconnecte en cas de déconnexion
- **Gestion d'erreurs** : Messages d'erreur affichés à l'utilisateur

## Test

Une fois intégré, teste en envoyant un message à Bob Technique. Tu devrais voir la réponse s'afficher progressivement!
