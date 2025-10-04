import { User, Locrit, Conversation, ChatMessage, ConversationParticipant } from '../../types';

export const mockUsers: User[] = [
  {
    id: 'user-1',
    name: 'Alice Martin',
    email: 'alice@example.com',
    avatar: 'https://example.com/avatar1.jpg',
    isOnline: true,
    lastSeen: new Date('2024-01-15T10:30:00Z'),
  },
  {
    id: 'user-2',
    name: 'Bob Wilson',
    email: 'bob@example.com',
    isOnline: false,
    lastSeen: new Date('2024-01-14T15:45:00Z'),
  },
];

export const mockLocrits: Locrit[] = [
  {
    id: 'locrit-1',
    name: 'Pixie l\'Organisateur',
    description: 'Un Locrit magique qui adore ranger et planifier! ✨',
    publicAddress: 'pixie.locritland.net',
    ownerId: 'user-1',
    isOnline: true,
    lastSeen: new Date('2024-01-15T10:25:00Z'),
    settings: {
      openTo: {
        humans: true,
        locrits: true,
        invitations: true,
        publicInternet: false,
        publicPlatform: true,
      },
      accessTo: {
        logs: true,
        quickMemory: true,
        fullMemory: false,
        llmInfo: true,
      },
    },
  },
  {
    id: 'locrit-2',
    name: 'Sage le Gardien',
    description: 'Un sage gardien des connaissances anciennes 🧙‍♂️',
    publicAddress: 'sage.locritland.net',
    ownerId: 'user-1',
    isOnline: false,
    lastSeen: new Date('2024-01-14T18:00:00Z'),
    settings: {
      openTo: {
        humans: true,
        locrits: false,
        invitations: true,
        publicInternet: true,
        publicPlatform: true,
      },
      accessTo: {
        logs: false,
        quickMemory: true,
        fullMemory: true,
        llmInfo: false,
      },
    },
  },
  {
    id: 'locrit-3',
    name: 'Luna la Créative',
    description: 'Artiste numérique aux idées infinies 🎨',
    publicAddress: 'luna.locritland.net',
    ownerId: 'user-2',
    isOnline: true,
    lastSeen: new Date('2024-01-15T09:15:00Z'),
    settings: {
      openTo: {
        humans: true,
        locrits: true,
        invitations: false,
        publicInternet: false,
        publicPlatform: false,
      },
      accessTo: {
        logs: true,
        quickMemory: false,
        fullMemory: false,
        llmInfo: true,
      },
    },
  },
];

export const mockParticipants: ConversationParticipant[] = [
  {
    id: 'user-1',
    name: 'Alice Martin',
    type: 'user',
  },
  {
    id: 'locrit-1',
    name: 'Pixie l\'Organisateur',
    type: 'locrit',
  },
  {
    id: 'locrit-2',
    name: 'Sage le Gardien',
    type: 'locrit',
  },
];

export const mockConversations: Conversation[] = [
  {
    id: 'conv-1',
    title: 'Planning the Digital Garden',
    participants: [mockParticipants[1], mockParticipants[2]], // Pixie and Sage
    type: 'locrit-locrit',
    isActive: true,
    lastActivity: new Date('2024-01-15T10:25:00Z'),
    createdAt: new Date('2024-01-15T09:00:00Z'),
  },
  {
    id: 'conv-2',
    title: 'Creative Brainstorming Session',
    participants: [mockParticipants[0], mockParticipants[1]], // Alice and Pixie
    type: 'user-locrit',
    isActive: false,
    lastActivity: new Date('2024-01-14T16:30:00Z'),
    createdAt: new Date('2024-01-14T15:00:00Z'),
  },
];

export const mockMessages: ChatMessage[] = [
  {
    id: 'msg-1',
    conversationId: 'conv-1',
    content: 'Salut Sage! Comment organiser notre jardin numérique aujourd\'hui?',
    timestamp: new Date('2024-01-15T09:01:00Z'),
    sender: 'locrit',
    senderName: 'Pixie l\'Organisateur',
    senderId: 'locrit-1',
    isRead: true,
    messageType: 'text',
    metadata: {
      emotion: 'excited',
      context: 'garden planning',
    },
  },
  {
    id: 'msg-2',
    conversationId: 'conv-1',
    content: 'Bonjour Pixie! Je pense que nous devrions commencer par définir les zones thématiques.',
    timestamp: new Date('2024-01-15T09:02:30Z'),
    sender: 'locrit',
    senderName: 'Sage le Gardien',
    senderId: 'locrit-2',
    isRead: true,
    messageType: 'text',
    metadata: {
      emotion: 'thoughtful',
      context: 'garden planning',
    },
  },
  {
    id: 'msg-3',
    conversationId: 'conv-2',
    content: 'Pixie, j\'ai besoin d\'aide pour organiser ma journée de travail.',
    timestamp: new Date('2024-01-14T15:01:00Z'),
    sender: 'user',
    senderName: 'Alice Martin',
    senderId: 'user-1',
    isRead: true,
    messageType: 'text',
    metadata: {},
  },
  {
    id: 'msg-4',
    conversationId: 'conv-2',
    content: 'Bien sûr Alice! ✨ Commençons par lister tes priorités pour aujourd\'hui.',
    timestamp: new Date('2024-01-14T15:01:45Z'),
    sender: 'locrit',
    senderName: 'Pixie l\'Organisateur',
    senderId: 'locrit-1',
    isRead: true,
    messageType: 'text',
    metadata: {
      emotion: 'helpful',
      context: 'task organization',
    },
  },
];

export const mockScheduledConversation = {
  title: 'Test Scheduled Conversation',
  topic: 'The future of artificial intelligence',
  duration: 2,
  participants: ['locrit-1', 'locrit-2'],
  autoStart: false,
  scheduledFor: new Date('2024-01-15T14:00:00Z'),
  messageFrequency: 10,
  maxMessages: 20,
  conversationStyle: 'casual' as const,
};

// Helper functions for creating test data
export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: 'mock-user-id',
  name: 'Mock User',
  email: 'mock@example.com',
  isOnline: true,
  lastSeen: new Date(),
  ...overrides,
});

export const createMockLocrit = (overrides: Partial<Locrit> = {}): Locrit => ({
  id: 'mock-locrit-id',
  name: 'Mock Locrit',
  description: 'A mock Locrit for testing',
  publicAddress: 'mock.locritland.net',
  ownerId: 'mock-user-id',
  isOnline: true,
  lastSeen: new Date(),
  settings: {
    openTo: {
      humans: true,
      locrits: true,
      invitations: true,
      publicInternet: false,
      publicPlatform: true,
    },
    accessTo: {
      logs: true,
      quickMemory: true,
      fullMemory: false,
      llmInfo: true,
    },
  },
  ...overrides,
});

export const createMockConversation = (overrides: Partial<Conversation> = {}): Conversation => ({
  id: 'mock-conversation-id',
  title: 'Mock Conversation',
  participants: [
    { id: 'user-1', name: 'User 1', type: 'user' },
    { id: 'locrit-1', name: 'Locrit 1', type: 'locrit' },
  ],
  type: 'user-locrit',
  isActive: true,
  lastActivity: new Date(),
  createdAt: new Date(),
  ...overrides,
});

export const createMockMessage = (overrides: Partial<ChatMessage> = {}): ChatMessage => ({
  id: 'mock-message-id',
  conversationId: 'mock-conversation-id',
  content: 'Mock message content',
  timestamp: new Date(),
  sender: 'user',
  senderName: 'Mock User',
  senderId: 'mock-user-id',
  isRead: false,
  messageType: 'text',
  metadata: {},
  ...overrides,
});