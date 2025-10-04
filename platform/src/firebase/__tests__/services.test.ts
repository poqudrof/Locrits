import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  collection,
  doc,
  addDoc,
  getDocs,
  getDoc,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  serverTimestamp,
  writeBatch,
} from 'firebase/firestore';
import {
  UserService,
  LocritService,
  MessageService,
  ConversationService,
} from '../services';
import { createMockUser, createMockLocrit, createMockConversation, createMockMessage } from '../../test/fixtures/mockData';

// Mock Firebase functions
vi.mock('firebase/firestore');

const mockCollection = vi.mocked(collection);
const mockDoc = vi.mocked(doc);
const mockAddDoc = vi.mocked(addDoc);
const mockGetDocs = vi.mocked(getDocs);
const mockGetDoc = vi.mocked(getDoc);
const mockUpdateDoc = vi.mocked(updateDoc);
const mockDeleteDoc = vi.mocked(deleteDoc);
const mockQuery = vi.mocked(query);
const mockWhere = vi.mocked(where);
const mockOrderBy = vi.mocked(orderBy);
const mockLimit = vi.mocked(limit);
const mockOnSnapshot = vi.mocked(onSnapshot);
const mockServerTimestamp = vi.mocked(serverTimestamp);
const mockWriteBatch = vi.mocked(writeBatch);

describe('Firebase Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('UserService', () => {
    const userService = new UserService();

    describe('getUsers', () => {
      it('should retrieve all users successfully', async () => {
        const mockUser = createMockUser();
        const mockSnapshot = {
          docs: [
            {
              id: mockUser.id,
              data: () => ({
                ...mockUser,
                lastSeen: { toDate: () => mockUser.lastSeen },
              }),
            },
          ],
        };

        mockGetDocs.mockResolvedValue(mockSnapshot as any);

        const result = await userService.getUsers();

        expect(result).toHaveLength(1);
        expect(result[0]).toEqual(mockUser);
        expect(mockGetDocs).toHaveBeenCalledTimes(1);
      });

      it('should handle errors when retrieving users', async () => {
        const error = new Error('Firestore error');
        mockGetDocs.mockRejectedValue(error);

        await expect(userService.getUsers()).rejects.toThrow('Firestore error');
      });
    });

    describe('getUser', () => {
      it('should retrieve a specific user by ID', async () => {
        const mockUser = createMockUser();
        const mockDocSnap = {
          exists: () => true,
          id: mockUser.id,
          data: () => ({
            ...mockUser,
            lastSeen: { toDate: () => mockUser.lastSeen },
          }),
        };

        mockGetDoc.mockResolvedValue(mockDocSnap as any);

        const result = await userService.getUser(mockUser.id);

        expect(result).toEqual(mockUser);
        expect(mockDoc).toHaveBeenCalledWith(expect.anything(), 'users', mockUser.id);
      });

      it('should return null for non-existent user', async () => {
        const mockDocSnap = {
          exists: () => false,
        };

        mockGetDoc.mockResolvedValue(mockDocSnap as any);

        const result = await userService.getUser('non-existent');

        expect(result).toBeNull();
      });
    });

    describe('subscribeToUsers', () => {
      it('should set up real-time listener for users', () => {
        const callback = vi.fn();
        const unsubscribe = vi.fn();

        mockOnSnapshot.mockReturnValue(unsubscribe);

        const result = userService.subscribeToUsers(callback);

        expect(mockQuery).toHaveBeenCalled();
        expect(mockOrderBy).toHaveBeenCalledWith('name', 'asc');
        expect(mockOnSnapshot).toHaveBeenCalled();
        expect(result).toBe(unsubscribe);
      });
    });
  });

  describe('LocritService', () => {
    const locritService = new LocritService();

    describe('createLocrit', () => {
      it('should create a new Locrit successfully', async () => {
        const mockLocrit = createMockLocrit();
        const { id, ...locritData } = mockLocrit;
        const mockDocRef = { id: 'new-locrit-id' };

        mockAddDoc.mockResolvedValue(mockDocRef as any);

        const result = await locritService.createLocrit(locritData);

        expect(result).toBe('new-locrit-id');
        expect(mockAddDoc).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            ...locritData,
            createdAt: expect.anything(),
            updatedAt: expect.anything(),
          })
        );
      });

      it('should handle errors when creating Locrit', async () => {
        const mockLocrit = createMockLocrit();
        const { id, ...locritData } = mockLocrit;
        const error = new Error('Creation failed');

        mockAddDoc.mockRejectedValue(error);

        await expect(locritService.createLocrit(locritData)).rejects.toThrow('Creation failed');
      });
    });

    describe('getLocrits', () => {
      it('should retrieve all Locrits successfully', async () => {
        const mockLocrit = createMockLocrit();
        const mockSnapshot = {
          docs: [
            {
              id: mockLocrit.id,
              data: () => ({
                ...mockLocrit,
                lastSeen: { toDate: () => mockLocrit.lastSeen },
              }),
            },
          ],
        };

        mockGetDocs.mockResolvedValue(mockSnapshot as any);

        const result = await locritService.getLocrits();

        expect(result).toHaveLength(1);
        expect(result[0]).toEqual(mockLocrit);
      });
    });

    describe('getUserLocrits', () => {
      it('should retrieve Locrits for a specific user', async () => {
        const userId = 'user-123';
        const mockLocrit = createMockLocrit({ ownerId: userId });
        const mockSnapshot = {
          docs: [
            {
              id: mockLocrit.id,
              data: () => ({
                ...mockLocrit,
                lastSeen: { toDate: () => mockLocrit.lastSeen },
              }),
            },
          ],
        };

        mockGetDocs.mockResolvedValue(mockSnapshot as any);

        const result = await locritService.getUserLocrits(userId);

        expect(result).toHaveLength(1);
        expect(result[0].ownerId).toBe(userId);
        expect(mockWhere).toHaveBeenCalledWith('ownerId', '==', userId);
        expect(mockOrderBy).toHaveBeenCalledWith('createdAt', 'desc');
      });
    });

    describe('updateLocrit', () => {
      it('should update a Locrit successfully', async () => {
        const locritId = 'locrit-123';
        const updates = { name: 'Updated Name' };

        await locritService.updateLocrit(locritId, updates);

        expect(mockDoc).toHaveBeenCalledWith(expect.anything(), 'locrits', locritId);
        expect(mockUpdateDoc).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            ...updates,
            updatedAt: expect.anything(),
          })
        );
      });
    });

    describe('deleteLocrit', () => {
      it('should delete a Locrit successfully', async () => {
        const locritId = 'locrit-123';

        await locritService.deleteLocrit(locritId);

        expect(mockDoc).toHaveBeenCalledWith(expect.anything(), 'locrits', locritId);
        expect(mockDeleteDoc).toHaveBeenCalled();
      });
    });
  });

  describe('MessageService', () => {
    const messageService = new MessageService();

    describe('sendMessage', () => {
      it('should send a message successfully', async () => {
        const mockMessage = createMockMessage();
        const { id, ...messageData } = mockMessage;
        const mockDocRef = { id: 'new-message-id' };

        mockAddDoc.mockResolvedValue(mockDocRef as any);

        const result = await messageService.sendMessage(messageData);

        expect(result).toBe('new-message-id');
        expect(mockAddDoc).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            ...messageData,
            timestamp: expect.anything(),
            isRead: false,
          })
        );
      });

      it('should handle errors when sending message', async () => {
        const mockMessage = createMockMessage();
        const { id, ...messageData } = mockMessage;
        const error = new Error('Send failed');

        mockAddDoc.mockRejectedValue(error);

        await expect(messageService.sendMessage(messageData)).rejects.toThrow('Send failed');
      });
    });

    describe('getLocritMessages', () => {
      it('should retrieve messages for a specific Locrit', async () => {
        const locritId = 'locrit-123';
        const mockMessage = createMockMessage({ locritId });
        const mockSnapshot = {
          docs: [
            {
              id: mockMessage.id,
              data: () => ({
                ...mockMessage,
                timestamp: { toDate: () => mockMessage.timestamp },
              }),
            },
          ],
        };

        mockGetDocs.mockResolvedValue(mockSnapshot as any);

        const result = await messageService.getLocritMessages(locritId);

        expect(result).toHaveLength(1);
        expect(result[0].locritId).toBe(locritId);
        expect(mockWhere).toHaveBeenCalledWith('locritId', '==', locritId);
        expect(mockOrderBy).toHaveBeenCalledWith('timestamp', 'asc');
        expect(mockLimit).toHaveBeenCalledWith(100);
      });
    });

    describe('subscribeToLocritMessages', () => {
      it('should set up real-time listener for Locrit messages', () => {
        const locritId = 'locrit-123';
        const callback = vi.fn();
        const unsubscribe = vi.fn();

        mockOnSnapshot.mockReturnValue(unsubscribe);

        const result = messageService.subscribeToLocritMessages(locritId, callback);

        expect(mockQuery).toHaveBeenCalled();
        expect(mockWhere).toHaveBeenCalledWith('locritId', '==', locritId);
        expect(mockOrderBy).toHaveBeenCalledWith('timestamp', 'asc');
        expect(mockLimit).toHaveBeenCalledWith(100);
        expect(mockOnSnapshot).toHaveBeenCalled();
        expect(result).toBe(unsubscribe);
      });
    });
  });

  describe('ConversationService', () => {
    const conversationService = new ConversationService();

    describe('createConversation', () => {
      it('should create a new conversation successfully', async () => {
        const mockConversation = createMockConversation();
        const { id, ...conversationData } = mockConversation;
        const mockDocRef = { id: 'new-conversation-id' };

        mockAddDoc.mockResolvedValue(mockDocRef as any);

        const result = await conversationService.createConversation(conversationData);

        expect(result).toBe('new-conversation-id');
        expect(mockAddDoc).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            ...conversationData,
            createdAt: expect.anything(),
            updatedAt: expect.anything(),
            lastActivity: expect.anything(),
          })
        );
      });
    });

    describe('getActiveConversations', () => {
      it('should retrieve active conversations', async () => {
        const mockConversation = createMockConversation({ isActive: true });
        const mockSnapshot = {
          docs: [
            {
              id: mockConversation.id,
              data: () => ({
                ...mockConversation,
                lastActivity: { toDate: () => mockConversation.lastActivity },
                createdAt: { toDate: () => mockConversation.createdAt },
              }),
            },
          ],
        };

        mockGetDocs.mockResolvedValue(mockSnapshot as any);

        const result = await conversationService.getActiveConversations();

        expect(result).toHaveLength(1);
        expect(result[0].isActive).toBe(true);
        expect(mockWhere).toHaveBeenCalledWith('isActive', '==', true);
        expect(mockOrderBy).toHaveBeenCalledWith('lastActivity', 'desc');
      });
    });

    describe('updateConversation', () => {
      it('should update a conversation successfully', async () => {
        const conversationId = 'conv-123';
        const updates = { title: 'Updated Title' };

        await conversationService.updateConversation(conversationId, updates);

        expect(mockDoc).toHaveBeenCalledWith(expect.anything(), 'conversations', conversationId);
        expect(mockUpdateDoc).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            ...updates,
            updatedAt: expect.anything(),
            lastActivity: expect.anything(),
          })
        );
      });
    });

    describe('subscribeToActiveConversations', () => {
      it('should set up real-time listener for active conversations', () => {
        const callback = vi.fn();
        const unsubscribe = vi.fn();

        mockOnSnapshot.mockReturnValue(unsubscribe);

        const result = conversationService.subscribeToActiveConversations(callback);

        expect(mockQuery).toHaveBeenCalled();
        expect(mockWhere).toHaveBeenCalledWith('isActive', '==', true);
        expect(mockOrderBy).toHaveBeenCalledWith('lastActivity', 'desc');
        expect(mockOnSnapshot).toHaveBeenCalled();
        expect(result).toBe(unsubscribe);
      });
    });
  });
});