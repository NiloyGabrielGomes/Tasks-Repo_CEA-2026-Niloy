/**
 * F-7: Navbar SSEIndicator state-transition tests
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';

// ── mock external deps ───────────────────────────────────────────────────────
vi.mock('react-router-dom', () => ({
  Link: ({ children, to }) => <a href={to}>{children}</a>,
  useNavigate: () => vi.fn(),
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin', name: 'Test Admin' }, logout: vi.fn() }),
}));

// SSEStatusContext mock — we'll override per-test via mockReturnValue
const mockSSEStatus = vi.fn();
vi.mock('../context/SSEStatusContext', () => ({
  useSSEStatus: () => mockSSEStatus(),
}));

import Navbar from '../components/Navbar';

// ── helpers ──────────────────────────────────────────────────────────────────
function renderNavbar() {
  return render(<Navbar />);
}

// ── tests ────────────────────────────────────────────────────────────────────
describe('Navbar – SSEIndicator state transitions (F-4)', () => {
  beforeEach(() => {
    // reset localStorage to avoid dark-mode side effects
    localStorage.clear();
  });

  it('renders nothing when status is null (Employee dashboard)', () => {
    mockSSEStatus.mockReturnValue({ status: null, lastEventAt: null, triggerReconnect: vi.fn() });
    renderNavbar();
    // the aria-label button should not be in the document
    expect(screen.queryByRole('button', { name: /SSE stream/i })).toBeNull();
  });

  it('shows green "Live" dot when status is "connected"', () => {
    mockSSEStatus.mockReturnValue({
      status: 'connected',
      lastEventAt: null,
      triggerReconnect: vi.fn(),
    });
    renderNavbar();
    const btn = screen.getByRole('button', { name: /SSE stream Live/i });
    expect(btn).toBeInTheDocument();
    // green dot
    const dot = btn.querySelector('span.bg-emerald-500');
    expect(dot).toBeTruthy();
  });

  it('shows amber "Connecting…" dot with animate-ping when status is "connecting"', () => {
    mockSSEStatus.mockReturnValue({
      status: 'connecting',
      lastEventAt: null,
      triggerReconnect: vi.fn(),
    });
    renderNavbar();
    const btn = screen.getByRole('button', { name: /SSE stream Connecting/i });
    expect(btn).toBeInTheDocument();
    // amber ping element
    const ping = btn.querySelector('span.animate-ping');
    expect(ping).toBeTruthy();
    expect(ping.className).toContain('bg-amber-400');
  });

  it('shows red "Disconnected" dot when status is "disconnected"', () => {
    mockSSEStatus.mockReturnValue({
      status: 'disconnected',
      lastEventAt: null,
      triggerReconnect: vi.fn(),
    });
    renderNavbar();
    const btn = screen.getByRole('button', { name: /SSE stream Disconnected/i });
    expect(btn).toBeInTheDocument();
    const dot = btn.querySelector('span.bg-red-500');
    expect(dot).toBeTruthy();
  });

  it('calls triggerReconnect when the indicator button is clicked', () => {
    const triggerReconnect = vi.fn();
    mockSSEStatus.mockReturnValue({
      status: 'disconnected',
      lastEventAt: null,
      triggerReconnect,
    });
    renderNavbar();
    const btn = screen.getByRole('button', { name: /SSE stream Disconnected/i });
    fireEvent.click(btn);
    expect(triggerReconnect).toHaveBeenCalledTimes(1);
  });

  it('tooltip appears on mouse-enter showing last-event time placeholder', () => {
    mockSSEStatus.mockReturnValue({
      status: 'connected',
      lastEventAt: null,
      triggerReconnect: vi.fn(),
    });
    renderNavbar();
    const btn = screen.getByRole('button', { name: /SSE stream Live/i });
    fireEvent.mouseEnter(btn);
    expect(screen.getByText(/Last event:/i)).toBeInTheDocument();
    expect(screen.getByText(/Click to reconnect/i)).toBeInTheDocument();
  });
});
