import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSSEStatus } from '../context/SSEStatusContext';

// ── SSE connection dot indicator ─────────────────────────────────────────────
function SSEIndicator() {
  const { status, lastEventAt, triggerReconnect } = useSSEStatus();
  const [showTooltip, setShowTooltip] = useState(false);

  // Don't render on pages that don't use the SSE stream (e.g. EmployeeDashboard)
  if (!status) return null;

  const dot = {
    connected:    { color: 'bg-emerald-500', ring: 'ring-emerald-200 dark:ring-emerald-900', label: 'Live',         pulse: false },
    connecting:   { color: 'bg-amber-400',   ring: 'ring-amber-200  dark:ring-amber-900',   label: 'Connecting…', pulse: true  },
    disconnected: { color: 'bg-red-500',     ring: 'ring-red-200    dark:ring-red-900',     label: 'Disconnected', pulse: false },
  }[status] ?? { color: 'bg-slate-400', ring: 'ring-slate-200', label: 'Unknown', pulse: false };

  const fmtTime = (d) =>
    d ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'never';

  return (
    <div className="relative flex items-center">
      <button
        onClick={triggerReconnect}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        aria-label={`SSE stream ${dot.label}. Click to reconnect.`}
      >
        <span className={`relative flex h-2.5 w-2.5`}>
          {dot.pulse && (
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${dot.color} opacity-75`} />
          )}
          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${dot.color} ring-2 ${dot.ring}`} />
        </span>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 hidden sm:inline">
          {dot.label}
        </span>
      </button>

      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 pointer-events-none">
          <div className="bg-slate-900 dark:bg-slate-700 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-xl">
            <p className="font-semibold capitalize mb-0.5">{dot.label}</p>
            <p className="text-slate-300">Last event: {fmtTime(lastEventAt)}</p>
            <p className="text-slate-400 mt-1">Click to reconnect</p>
            {/* arrow */}
            <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 dark:bg-slate-700 rotate-45" />
          </div>
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dark, setDark] = useState(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [dark]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const dashboardLink =
    user?.role === 'admin'
      ? '/admin'
      : user?.role === 'team_lead'
        ? '/team-lead'
        : '/dashboard';

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-primary/10 bg-background-light/80 dark:bg-background-dark/80 blur-nav">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to={dashboardLink} className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="material-icons-outlined text-white text-lg">
              restaurant_menu
            </span>
          </div>
          <span className="text-xl font-bold tracking-tight text-primary">
            MHP
          </span>
        </Link>

        <div className="flex items-center gap-6">
          {/* Navigation links */}
          <div className="hidden md:flex items-center gap-4 text-sm font-medium text-slate-600 dark:text-slate-400">
            <Link
              to={dashboardLink}
              className="hover:text-primary transition-colors"
            >
              Dashboard
            </Link>
          </div>

          {/* SSE status indicator */}
          <SSEIndicator />

          {/* Dark mode toggle */}
          <button
            onClick={() => setDark(!dark)}
            className="p-2 rounded-lg text-slate-500 hover:text-primary hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Toggle dark mode"
          >
            <span className="material-icons-outlined text-xl">
              {dark ? 'light_mode' : 'dark_mode'}
            </span>
          </button>

          {/* User info & logout */}
          <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-800">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                {user?.name}
              </p>
              <p className="text-[10px] text-slate-500">
                {user?.team || user?.role}
              </p>
            </div>
            <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold">
              {user?.name
                ?.split(' ')
                .map((n) => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2)}
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
              title="Logout"
            >
              <span className="material-icons-outlined text-xl">logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
