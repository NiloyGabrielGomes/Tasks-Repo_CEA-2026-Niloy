import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

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
