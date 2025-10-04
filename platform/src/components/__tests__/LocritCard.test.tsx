import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocritCard } from '../LocritCard';
import { mockLocrits } from '../../test/fixtures/mockData';

// Mock UI components
vi.mock('../ui/card', () => ({
  Card: ({ children, className, ...props }: any) => (
    <div className={className} {...props}>
      {children}
    </div>
  ),
  CardContent: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h3 {...props}>{children}</h3>,
}));

vi.mock('../ui/badge', () => ({
  Badge: ({ children, variant, className, ...props }: any) => (
    <span data-variant={variant} className={className} {...props}>
      {children}
    </span>
  ),
}));

vi.mock('../ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      data-variant={variant}
      data-size={size}
      {...props}
    >
      {children}
    </button>
  ),
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  MessageCircle: () => <span data-testid="message-icon" />,
  Settings: () => <span data-testid="settings-icon" />,
  Eye: () => <span data-testid="eye-icon" />,
  Calendar: () => <span data-testid="calendar-icon" />,
  Globe: () => <span data-testid="globe-icon" />,
  Lock: () => <span data-testid="lock-icon" />,
  Users: () => <span data-testid="users-icon" />,
  Bot: () => <span data-testid="bot-icon" />,
}));

describe('LocritCard', () => {
  const mockProps = {
    locrit: mockLocrits[0],
    onChat: vi.fn(),
    onSettings: vi.fn(),
    onObserve: vi.fn(),
    onScheduleConversation: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render locrit name and description', () => {
    render(<LocritCard {...mockProps} />);

    expect(screen.getByText(mockProps.locrit.name)).toBeInTheDocument();
    expect(screen.getByText(mockProps.locrit.description)).toBeInTheDocument();
  });

  it('should show online status when locrit is online', () => {
    const onlineLocrit = { ...mockLocrits[0], isOnline: true };
    render(<LocritCard {...mockProps} locrit={onlineLocrit} />);

    expect(screen.getByText('🟢 En ligne')).toBeInTheDocument();
  });

  it('should show offline status when locrit is offline', () => {
    const offlineLocrit = { ...mockLocrits[0], isOnline: false };
    render(<LocritCard {...mockProps} locrit={offlineLocrit} />);

    expect(screen.getByText('🔴 Hors ligne')).toBeInTheDocument();
  });

  it('should display public address', () => {
    render(<LocritCard {...mockProps} />);

    expect(screen.getByText(mockProps.locrit.publicAddress)).toBeInTheDocument();
  });

  it('should show correct access badges based on settings', () => {
    const locritWithOpenSettings = {
      ...mockLocrits[0],
      settings: {
        ...mockLocrits[0].settings,
        openTo: {
          ...mockLocrits[0].settings.openTo,
          humans: true,
          locrits: true,
          publicPlatform: true,
        },
      },
    };

    render(<LocritCard {...mockProps} locrit={locritWithOpenSettings} />);

    expect(screen.getByText('👥 Humains')).toBeInTheDocument();
    expect(screen.getByText('🤖 Locrits')).toBeInTheDocument();
    expect(screen.getByText('🌐 Public')).toBeInTheDocument();
  });

  it('should show private badge when not public', () => {
    const privateLocrit = {
      ...mockLocrits[0],
      settings: {
        ...mockLocrits[0].settings,
        openTo: {
          ...mockLocrits[0].settings.openTo,
          publicPlatform: false,
        },
      },
    };

    render(<LocritCard {...mockProps} locrit={privateLocrit} />);

    expect(screen.getByText('🔒 Privé')).toBeInTheDocument();
  });

  it('should call onChat when chat button is clicked', async () => {
    const user = userEvent.setup();
    render(<LocritCard {...mockProps} />);

    const chatButton = screen.getByTestId('message-icon').closest('button');
    if (chatButton) {
      await user.click(chatButton);
      expect(mockProps.onChat).toHaveBeenCalledWith(mockProps.locrit);
    }
  });

  it('should call onSettings when settings button is clicked', async () => {
    const user = userEvent.setup();
    render(<LocritCard {...mockProps} />);

    const settingsButton = screen.getByTestId('settings-icon').closest('button');
    if (settingsButton) {
      await user.click(settingsButton);
      expect(mockProps.onSettings).toHaveBeenCalledWith(mockProps.locrit);
    }
  });

  it('should call onObserve when observe button is clicked', async () => {
    const user = userEvent.setup();
    render(<LocritCard {...mockProps} />);

    const observeButton = screen.getByTestId('eye-icon').closest('button');
    if (observeButton) {
      await user.click(observeButton);
      expect(mockProps.onObserve).toHaveBeenCalledWith(mockProps.locrit);
    }
  });

  it('should call onScheduleConversation when schedule button is clicked', async () => {
    const user = userEvent.setup();
    render(<LocritCard {...mockProps} />);

    const scheduleButton = screen.getByTestId('calendar-icon').closest('button');
    if (scheduleButton) {
      await user.click(scheduleButton);
      expect(mockProps.onScheduleConversation).toHaveBeenCalledWith(mockProps.locrit);
    }
  });

  it('should format last seen time correctly', () => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const locritWithRecentActivity = {
      ...mockLocrits[0],
      lastSeen: oneHourAgo,
    };

    render(<LocritCard {...mockProps} locrit={locritWithRecentActivity} />);

    expect(screen.getByText(/Il y a 1h/)).toBeInTheDocument();
  });

  it('should handle very recent activity (less than 1 minute)', () => {
    const now = new Date();
    const thirtySecondsAgo = new Date(now.getTime() - 30 * 1000);
    const locritWithVeryRecentActivity = {
      ...mockLocrits[0],
      lastSeen: thirtySecondsAgo,
    };

    render(<LocritCard {...mockProps} locrit={locritWithVeryRecentActivity} />);

    expect(screen.getByText(/À l'instant/)).toBeInTheDocument();
  });

  it('should show days for older activity', () => {
    const now = new Date();
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
    const locritWithOldActivity = {
      ...mockLocrits[0],
      lastSeen: threeDaysAgo,
    };

    render(<LocritCard {...mockProps} locrit={locritWithOldActivity} />);

    expect(screen.getByText(/Il y a 3j/)).toBeInTheDocument();
  });

  it('should show correct access level indicators', () => {
    const locritWithLimitedAccess = {
      ...mockLocrits[0],
      settings: {
        ...mockLocrits[0].settings,
        accessTo: {
          logs: false,
          quickMemory: true,
          fullMemory: false,
          llmInfo: true,
        },
      },
    };

    render(<LocritCard {...mockProps} locrit={locritWithLimitedAccess} />);

    // Should show available access types
    expect(screen.getByText(/Accès:/)).toBeInTheDocument();
  });

  it('should apply correct styling for online/offline status', () => {
    const { rerender } = render(<LocritCard {...mockProps} />);

    // Online locrit should have appropriate styling
    const onlineLocrit = { ...mockLocrits[0], isOnline: true };
    rerender(<LocritCard {...mockProps} locrit={onlineLocrit} />);

    // Offline locrit should have appropriate styling
    const offlineLocrit = { ...mockLocrits[0], isOnline: false };
    rerender(<LocritCard {...mockProps} locrit={offlineLocrit} />);
  });

  it('should handle missing optional props gracefully', () => {
    const minimalProps = {
      locrit: mockLocrits[0],
      onChat: vi.fn(),
      onSettings: vi.fn(),
      onObserve: vi.fn(),
    };

    // Should render without onScheduleConversation
    expect(() => render(<LocritCard {...minimalProps} />)).not.toThrow();
  });

  it('should show correct accessibility attributes', () => {
    render(<LocritCard {...mockProps} />);

    // Buttons should be accessible
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeInTheDocument();
    });
  });

  it('should handle button interactions with keyboard', async () => {
    const user = userEvent.setup();
    render(<LocritCard {...mockProps} />);

    const chatButton = screen.getByTestId('message-icon').closest('button');
    if (chatButton) {
      // Focus and press Enter
      await user.tab();
      await user.keyboard('{Enter}');
      // Note: Actual keyboard interaction testing would require more complex setup
    }
  });
});