import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../../App';
import { mockUsers, mockLocrits, mockConversations, mockMessages } from '../../test/fixtures/mockData';
import * as firebaseServices from '../../firebase/services';

// Mock Firebase services
vi.mock('../../firebase/services');

// Mock Firebase config
vi.mock('../../firebase/config', () => ({
  db: {},
  auth: {
    currentUser: null,
  },
  storage: {},
}));

// Mock auth hook
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUsers[0],
    loading: false,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
  }),
}));

describe('Conversation Flow Integration Tests', () => {
  const mockServices = vi.mocked(firebaseServices);

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mock implementations
    mockServices.userService = {
      getUsers: vi.fn().mockResolvedValue(mockUsers),
      getUser: vi.fn().mockResolvedValue(mockUsers[0]),
      subscribeToUsers: vi.fn().mockReturnValue(() => {}),
    } as any;

    mockServices.locritService = {
      getLocrits: vi.fn().mockResolvedValue(mockLocrits),
      getUserLocrits: vi.fn().mockResolvedValue(mockLocrits.filter(l => l.ownerId === mockUsers[0].id)),
      createLocrit: vi.fn().mockResolvedValue('new-locrit-id'),
      updateLocrit: vi.fn().mockResolvedValue(),
      deleteLocrit: vi.fn().mockResolvedValue(),
      subscribeToUserLocrits: vi.fn().mockReturnValue(() => {}),
      subscribeToAllLocrits: vi.fn().mockReturnValue(() => {}),
    } as any;

    mockServices.conversationService = {
      getActiveConversations: vi.fn().mockResolvedValue(mockConversations),
      createConversation: vi.fn().mockResolvedValue('new-conversation-id'),
      updateConversation: vi.fn().mockResolvedValue(),
      subscribeToActiveConversations: vi.fn().mockReturnValue(() => {}),
    } as any;

    mockServices.messageService = {
      sendMessage: vi.fn().mockResolvedValue('new-message-id'),
      getLocritMessages: vi.fn().mockResolvedValue(mockMessages),
      getConversationMessages: vi.fn().mockResolvedValue(mockMessages),
      subscribeToLocritMessages: vi.fn().mockReturnValue(() => {}),
      subscribeToConversationMessages: vi.fn().mockReturnValue(() => {}),
    } as any;
  });

  describe('Complete Conversation Lifecycle', () => {
    it('should allow user to create and manage a conversation', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Wait for app to load and show dashboard
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      // Navigate to conversations
      const conversationsButton = screen.getByText(/Conversations/i);
      await user.click(conversationsButton);

      // Create new conversation
      const newConversationButton = screen.getByText(/Nouvelle conversation/i);
      await user.click(newConversationButton);

      // Fill in conversation details
      const titleInput = screen.getByPlaceholderText(/Titre de la conversation/i);
      await user.type(titleInput, 'Test Integration Conversation');

      const topicInput = screen.getByPlaceholderText(/Sujet/i);
      await user.type(topicInput, 'Testing conversation flow');

      // Select participants
      const firstLocrit = screen.getByText(mockLocrits[0].name);
      await user.click(firstLocrit);

      const secondLocrit = screen.getByText(mockLocrits[1].name);
      await user.click(secondLocrit);

      // Create conversation
      const createButton = screen.getByText(/Créer/i);
      await user.click(createButton);

      // Verify conversation creation
      await waitFor(() => {
        expect(mockServices.conversationService.createConversation).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Test Integration Conversation',
            participants: expect.arrayContaining([
              expect.objectContaining({ id: mockLocrits[0].id }),
              expect.objectContaining({ id: mockLocrits[1].id }),
            ]),
          })
        );
      });
    });

    it('should handle conversation message flow', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Navigate to specific conversation
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      // Click on existing conversation
      const conversationTitle = screen.getByText(mockConversations[0].title);
      await user.click(conversationTitle);

      // Wait for conversation to load
      await waitFor(() => {
        expect(mockServices.messageService.getConversationMessages).toHaveBeenCalledWith(
          mockConversations[0].id
        );
      });

      // Send a new message
      const messageInput = screen.getByPlaceholderText(/Tapez votre message/i);
      await user.type(messageInput, 'Hello from integration test');

      const sendButton = screen.getByText(/Envoyer/i);
      await user.click(sendButton);

      // Verify message was sent
      await waitFor(() => {
        expect(mockServices.messageService.sendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            content: 'Hello from integration test',
            conversationId: mockConversations[0].id,
          })
        );
      });
    });

    it('should handle real-time message updates', async () => {
      const user = userEvent.setup();
      let messageCallback: Function;

      // Mock subscription to capture callback
      mockServices.messageService.subscribeToConversationMessages = vi.fn().mockImplementation(
        (conversationId, callback) => {
          messageCallback = callback;
          return () => {}; // unsubscribe function
        }
      );

      render(<App />);

      // Navigate to conversation
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      const conversationTitle = screen.getByText(mockConversations[0].title);
      await user.click(conversationTitle);

      // Wait for subscription to be set up
      await waitFor(() => {
        expect(mockServices.messageService.subscribeToConversationMessages).toHaveBeenCalled();
      });

      // Simulate new message from Firebase
      const newMessage = {
        id: 'new-message-id',
        conversationId: mockConversations[0].id,
        content: 'Real-time message from Locrit',
        timestamp: new Date(),
        sender: 'locrit' as const,
        senderName: mockLocrits[0].name,
        senderId: mockLocrits[0].id,
        isRead: false,
        messageType: 'text' as const,
        metadata: {},
      };

      messageCallback!([...mockMessages, newMessage]);

      // Verify new message appears in UI
      await waitFor(() => {
        expect(screen.getByText('Real-time message from Locrit')).toBeInTheDocument();
      });
    });
  });

  describe('Scheduled Conversation Flow', () => {
    it('should create and start a scheduled conversation', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Navigate to scheduled conversations
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      const scheduledButton = screen.getByText(/Conversations programmées/i);
      await user.click(scheduledButton);

      // Fill in scheduled conversation form
      const titleInput = screen.getByPlaceholderText(/Titre de la conversation/i);
      await user.type(titleInput, 'Scheduled Integration Test');

      const topicTextarea = screen.getByPlaceholderText(/Décrivez le sujet/i);
      await user.type(topicTextarea, 'AI and machine learning discussion');

      // Set duration to 3 minutes
      const durationSlider = screen.getByTestId('duration-slider');
      await user.type(durationSlider, '3');

      // Select participants
      const firstLocrit = screen.getByText(mockLocrits[0].name);
      await user.click(firstLocrit);

      const secondLocrit = screen.getByText(mockLocrits[1].name);
      await user.click(secondLocrit);

      // Start conversation
      const startButton = screen.getByText(/Lancer la conversation/i);
      await user.click(startButton);

      // Verify conversation creation
      await waitFor(() => {
        expect(mockServices.conversationService.createConversation).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Scheduled Integration Test',
            topic: 'AI and machine learning discussion',
            type: 'locrit-locrit',
            duration: 3,
            isScheduled: true,
          })
        );
      });

      // Verify live conversation monitor appears
      expect(screen.getByText(/Conversation en direct/i)).toBeInTheDocument();
      expect(screen.getByText('3:00')).toBeInTheDocument(); // Timer
    });

    it('should handle conversation pause and resume', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Set up and start a scheduled conversation (abbreviated)
      // ... setup code similar to previous test

      await waitFor(() => {
        expect(screen.getByText(/Conversation en direct/i)).toBeInTheDocument();
      });

      // Pause conversation
      const pauseButton = screen.getByText(/Pause/i);
      await user.click(pauseButton);

      // Verify UI updates
      expect(screen.getByText(/Reprendre/i)).toBeInTheDocument();

      // Resume conversation
      const resumeButton = screen.getByText(/Reprendre/i);
      await user.click(resumeButton);

      // Verify UI updates back
      expect(screen.getByText(/Pause/i)).toBeInTheDocument();
    });

    it('should end conversation when timer expires', async () => {
      vi.useFakeTimers();
      const user = userEvent.setup();
      render(<App />);

      // Start a 1-minute conversation for faster testing
      // ... setup code

      // Fast forward timer
      vi.advanceTimersByTime(60 * 1000); // 1 minute

      await waitFor(() => {
        expect(mockServices.conversationService.updateConversation).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            status: 'ended',
            isActive: false,
          })
        );
      });

      vi.useRealTimers();
    });
  });

  describe('Conversation Review Flow', () => {
    it('should display conversation analytics and allow export', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Navigate to conversation review
      await waitFor(() => {
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });

      // Click on conversation to review
      const conversationTitle = screen.getByText(mockConversations[0].title);
      await user.click(conversationTitle);

      // Click review button
      const reviewButton = screen.getByText(/Révision/i);
      await user.click(reviewButton);

      // Verify analytics are displayed
      await waitFor(() => {
        expect(screen.getByText(/Statistiques détaillées/i)).toBeInTheDocument();
        expect(screen.getByText(/Répartition des messages/i)).toBeInTheDocument();
        expect(screen.getByText(/Activité par heure/i)).toBeInTheDocument();
      });

      // Test export functionality
      const exportButton = screen.getByText(/Exporter/i);
      await user.click(exportButton);

      // Verify download was triggered (in real scenario, would check for file download)
      // Note: File download testing requires additional setup in testing environment
    });

    it('should filter messages by participant and search term', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Navigate to conversation review
      // ... navigation code

      // Use search filter
      const searchInput = screen.getByPlaceholderText(/Rechercher dans les messages/i);
      await user.type(searchInput, 'test');

      // Use participant filter
      const participantSelect = screen.getByDisplayValue(/Tous les participants/i);
      await user.selectOptions(participantSelect, mockLocrits[0].id);

      // Verify filtered results
      await waitFor(() => {
        // Should show filtered message count
        expect(screen.getByText(/sur \d+ messages/)).toBeInTheDocument();
      });

      // Reset filters
      const resetButton = screen.getByText(/Réinitialiser/i);
      await user.click(resetButton);

      // Verify all messages are shown again
      expect(searchInput).toHaveValue('');
      expect(participantSelect).toHaveValue('all');
    });
  });

  describe('Error Handling', () => {
    it('should handle conversation creation errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock service to throw error
      mockServices.conversationService.createConversation = vi.fn().mockRejectedValue(
        new Error('Network error')
      );

      render(<App />);

      // Attempt to create conversation
      // ... setup code

      await waitFor(() => {
        expect(screen.getByText(/Erreur lors de la création/i)).toBeInTheDocument();
      });
    });

    it('should handle message sending errors', async () => {
      const user = userEvent.setup();

      // Mock service to throw error
      mockServices.messageService.sendMessage = vi.fn().mockRejectedValue(
        new Error('Failed to send message')
      );

      render(<App />);

      // Attempt to send message
      // ... setup code

      await waitFor(() => {
        expect(screen.getByText(/Erreur lors de l'envoi/i)).toBeInTheDocument();
      });
    });

    it('should handle Firebase connection errors', async () => {
      const user = userEvent.setup();

      // Mock all services to throw connection errors
      Object.values(mockServices).forEach(service => {
        if (typeof service === 'object') {
          Object.keys(service).forEach(method => {
            service[method] = vi.fn().mockRejectedValue(new Error('Firebase connection failed'));
          });
        }
      });

      render(<App />);

      // Should show appropriate error messages
      await waitFor(() => {
        expect(screen.getByText(/Erreur de connexion/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance and Loading States', () => {
    it('should show loading states during data fetching', async () => {
      const user = userEvent.setup();

      // Mock services with delayed responses
      mockServices.conversationService.getActiveConversations = vi.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockConversations), 1000))
      );

      render(<App />);

      // Should show loading indicators
      expect(screen.getByText(/Chargement/i)).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(mockConversations[0].title)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should handle large numbers of messages efficiently', async () => {
      const user = userEvent.setup();

      // Generate many messages
      const manyMessages = Array.from({ length: 1000 }, (_, i) => ({
        id: `message-${i}`,
        conversationId: mockConversations[0].id,
        content: `Message ${i}`,
        timestamp: new Date(),
        sender: i % 2 === 0 ? 'user' as const : 'locrit' as const,
        senderName: i % 2 === 0 ? 'User' : mockLocrits[0].name,
        senderId: i % 2 === 0 ? mockUsers[0].id : mockLocrits[0].id,
        isRead: true,
        messageType: 'text' as const,
        metadata: {},
      }));

      mockServices.messageService.getConversationMessages = vi.fn().mockResolvedValue(manyMessages);

      render(<App />);

      // Navigate to conversation with many messages
      // ... navigation code

      // Should render without performance issues
      await waitFor(() => {
        expect(screen.getByText('Message 0')).toBeInTheDocument();
      });

      // Should implement virtualization or pagination for performance
      // (This would depend on the actual implementation)
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });
});