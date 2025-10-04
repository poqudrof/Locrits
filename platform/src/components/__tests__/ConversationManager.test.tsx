import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConversationManager } from '../ConversationManager';
import { mockLocrits, mockConversations } from '../../test/fixtures/mockData';

// Mock UI components
vi.mock('../ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('../ui/card', () => ({
  Card: ({ children, className, onClick, ...props }: any) => (
    <div className={className} onClick={onClick} {...props}>
      {children}
    </div>
  ),
  CardContent: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
}));

vi.mock('../ui/badge', () => ({
  Badge: ({ children, ...props }: any) => <span {...props}>{children}</span>,
}));

vi.mock('../ui/input', () => ({
  Input: ({ value, onChange, onKeyDown, ...props }: any) => (
    <input
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      {...props}
    />
  ),
}));

vi.mock('../ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: any) => (
    <div data-testid="dialog" data-open={open}>
      {children}
    </div>
  ),
  DialogContent: ({ children }: any) => <div data-testid="dialog-content">{children}</div>,
  DialogDescription: ({ children }: any) => <p data-testid="dialog-description">{children}</p>,
  DialogFooter: ({ children }: any) => <div data-testid="dialog-footer">{children}</div>,
  DialogHeader: ({ children }: any) => <div data-testid="dialog-header">{children}</div>,
  DialogTitle: ({ children }: any) => <h3 data-testid="dialog-title">{children}</h3>,
  DialogTrigger: ({ children }: any) => <div data-testid="dialog-trigger">{children}</div>,
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  ArrowLeft: () => <span data-testid="arrow-left-icon" />,
  Plus: () => <span data-testid="plus-icon" />,
  MessageCircle: () => <span data-testid="message-circle-icon" />,
  Trash2: () => <span data-testid="trash-icon" />,
  Clock: () => <span data-testid="clock-icon" />,
  Users: () => <span data-testid="users-icon" />,
}));

describe('ConversationManager', () => {
  const mockProps = {
    locrit: mockLocrits[0],
    conversations: mockConversations,
    onSelectConversation: vi.fn(),
    onCreateConversation: vi.fn(),
    onDeleteConversation: vi.fn(),
    onBack: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render locrit name in header', () => {
    render(<ConversationManager {...mockProps} />);

    expect(screen.getByText(`💬 Conversations avec ${mockProps.locrit.name}`)).toBeInTheDocument();
  });

  it('should render back button and call onBack when clicked', async () => {
    const user = userEvent.setup();
    render(<ConversationManager {...mockProps} />);

    const backButton = screen.getByTestId('arrow-left-icon').closest('button');
    expect(backButton).toBeInTheDocument();

    if (backButton) {
      await user.click(backButton);
      expect(mockProps.onBack).toHaveBeenCalledTimes(1);
    }
  });

  it('should show empty state when no conversations exist', () => {
    const propsWithNoConversations = {
      ...mockProps,
      conversations: [],
    };

    render(<ConversationManager {...propsWithNoConversations} />);

    expect(screen.getByText('Aucune conversation encore')).toBeInTheDocument();
    expect(screen.getByText(`Commencez votre première discussion magique avec ${mockProps.locrit.name} !`)).toBeInTheDocument();
  });

  it('should filter and display conversations for the current locrit', () => {
    render(<ConversationManager {...mockProps} />);

    // Should show conversations that include this locrit
    const locritConversations = mockConversations.filter(conv =>
      conv.participants.some(p => p.id === mockProps.locrit.id && p.type === 'locrit')
    );

    expect(screen.getByText(`${locritConversations.length} conversation${locritConversations.length > 1 ? 's' : ''} active${locritConversations.length > 1 ? 's' : ''}`)).toBeInTheDocument();
  });

  it('should open create conversation dialog when new conversation button is clicked', async () => {
    const user = userEvent.setup();
    render(<ConversationManager {...mockProps} />);

    const newConversationButton = screen.getByText('Nouvelle conversation');
    await user.click(newConversationButton);

    expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'true');
    expect(screen.getByText('✨ Créer une nouvelle conversation')).toBeInTheDocument();
  });

  it('should handle conversation creation', async () => {
    const user = userEvent.setup();
    render(<ConversationManager {...mockProps} />);

    // Open dialog
    const newConversationButton = screen.getByText('Nouvelle conversation');
    await user.click(newConversationButton);

    // Enter conversation title
    const titleInput = screen.getByPlaceholderText('🌟 Titre de la conversation...');
    await user.type(titleInput, 'Test Conversation');

    // Click create button
    const createButton = screen.getByText('Créer');
    await user.click(createButton);

    expect(mockProps.onCreateConversation).toHaveBeenCalledWith('Test Conversation');
  });

  it('should handle conversation creation with Enter key', async () => {
    const user = userEvent.setup();
    render(<ConversationManager {...mockProps} />);

    // Open dialog
    const newConversationButton = screen.getByText('Nouvelle conversation');
    await user.click(newConversationButton);

    // Enter conversation title and press Enter
    const titleInput = screen.getByPlaceholderText('🌟 Titre de la conversation...');
    await user.type(titleInput, 'Test Conversation{Enter}');

    expect(mockProps.onCreateConversation).toHaveBeenCalledWith('Test Conversation');
  });

  it('should not create conversation with empty title', async () => {
    const user = userEvent.setup();
    render(<ConversationManager {...mockProps} />);

    // Open dialog
    const newConversationButton = screen.getByText('Nouvelle conversation');
    await user.click(newConversationButton);

    // Try to create with empty title
    const createButton = screen.getByText('Créer');
    expect(createButton).toBeDisabled();
  });

  it('should handle conversation selection', async () => {
    const user = userEvent.setup();

    // Use a conversation that includes our locrit
    const conversationWithLocrit = {
      ...mockConversations[0],
      participants: [
        ...mockConversations[0].participants,
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const }
      ]
    };

    const propsWithMatchingConversation = {
      ...mockProps,
      conversations: [conversationWithLocrit],
    };

    render(<ConversationManager {...propsWithMatchingConversation} />);

    // Click on conversation card
    const conversationCard = screen.getByText(conversationWithLocrit.title).closest('div');
    if (conversationCard) {
      await user.click(conversationCard);
      expect(mockProps.onSelectConversation).toHaveBeenCalledWith(conversationWithLocrit.id);
    }
  });

  it('should handle conversation deletion', async () => {
    const user = userEvent.setup();

    // Use a conversation that includes our locrit
    const conversationWithLocrit = {
      ...mockConversations[0],
      participants: [
        ...mockConversations[0].participants,
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const }
      ]
    };

    const propsWithMatchingConversation = {
      ...mockProps,
      conversations: [conversationWithLocrit],
    };

    render(<ConversationManager {...propsWithMatchingConversation} />);

    // Click delete button
    const deleteButton = screen.getByTestId('trash-icon').closest('button');
    if (deleteButton) {
      await user.click(deleteButton);
      expect(mockProps.onDeleteConversation).toHaveBeenCalledWith(conversationWithLocrit.id);
    }
  });

  it('should show active badge for active conversations', () => {
    const activeConversation = {
      ...mockConversations[0],
      isActive: true,
      participants: [
        ...mockConversations[0].participants,
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const }
      ]
    };

    const propsWithActiveConversation = {
      ...mockProps,
      conversations: [activeConversation],
    };

    render(<ConversationManager {...propsWithActiveConversation} />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('should format last activity time correctly', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

    const recentConversation = {
      ...mockConversations[0],
      lastActivity: fiveMinutesAgo,
      participants: [
        ...mockConversations[0].participants,
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const }
      ]
    };

    const propsWithRecentConversation = {
      ...mockProps,
      conversations: [recentConversation],
    };

    render(<ConversationManager {...propsWithRecentConversation} />);

    expect(screen.getByText('Il y a 5min')).toBeInTheDocument();
  });

  it('should show participant count', () => {
    const conversationWithMultipleParticipants = {
      ...mockConversations[0],
      participants: [
        { id: 'user-1', name: 'User 1', type: 'user' as const },
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const },
        { id: 'locrit-2', name: 'Locrit 2', type: 'locrit' as const },
      ]
    };

    const propsWithMultipleParticipants = {
      ...mockProps,
      conversations: [conversationWithMultipleParticipants],
    };

    render(<ConversationManager {...propsWithMultipleParticipants} />);

    expect(screen.getByText('3 participants')).toBeInTheDocument();
  });

  it('should prevent event propagation when clicking action buttons', async () => {
    const user = userEvent.setup();

    const conversationWithLocrit = {
      ...mockConversations[0],
      participants: [
        ...mockConversations[0].participants,
        { id: mockProps.locrit.id, name: mockProps.locrit.name, type: 'locrit' as const }
      ]
    };

    const propsWithMatchingConversation = {
      ...mockProps,
      conversations: [conversationWithLocrit],
    };

    render(<ConversationManager {...propsWithMatchingConversation} />);

    // Click message button (should not trigger conversation selection)
    const messageButton = screen.getByTestId('message-circle-icon').closest('button');
    if (messageButton) {
      await user.click(messageButton);
      expect(mockProps.onSelectConversation).toHaveBeenCalledWith(conversationWithLocrit.id);
    }

    // Reset mock
    mockProps.onSelectConversation.mockClear();

    // Click delete button (should not trigger conversation selection)
    const deleteButton = screen.getByTestId('trash-icon').closest('button');
    if (deleteButton) {
      await user.click(deleteButton);
      expect(mockProps.onSelectConversation).not.toHaveBeenCalled();
      expect(mockProps.onDeleteConversation).toHaveBeenCalledWith(conversationWithLocrit.id);
    }
  });
});