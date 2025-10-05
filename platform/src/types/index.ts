export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  isOnline: boolean;
  lastSeen: Date;
}

export interface Locrit {
  id: string;
  name: string;
  description: string;
  publicAddress: string;
  ownerId: string;
  isOnline: boolean;
  lastSeen: Date;
  settings: LocritSettings;
}

export interface LocritSettings {
  openTo: {
    humans: boolean;
    locrits: boolean;
    invitations: boolean;
    publicInternet: boolean;
    publicPlatform: boolean;
  };
  accessTo: {
    logs: boolean;
    quickMemory: boolean;
    fullMemory: boolean;
    llmInfo: boolean;
  };
  memoryService?: 'kuzu_graph' | 'plaintext_file' | 'basic_memory' | 'lancedb_langchain' | 'lancedb_mcp' | 'disabled';
}

export interface MemoryServiceInfo {
  type: 'kuzu_graph' | 'plaintext_file' | 'basic_memory' | 'lancedb_langchain' | 'lancedb_mcp' | 'disabled';
  name: string;
  description: string;
  pros: string;
  cons: string;
  stability: 'stable' | 'experimental';
}

export interface ChatMessage {
  id: string;
  locritId?: string;
  conversationId?: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'locrit';
  senderName: string;
}

export interface Conversation {
  id: string;
  title: string;
  participants: ConversationParticipant[];
  type: 'user-locrit' | 'locrit-locrit';
  isActive: boolean;
  lastActivity: Date;
  createdAt: Date;
}

export interface ConversationParticipant {
  id: string;
  name: string;
  type: 'user' | 'locrit';
}

export interface LocritLog {
  id: string;
  locritId: string;
  timestamp: Date;
  level: 'info' | 'warning' | 'error';
  message: string;
  details?: any;
}