import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorMessage from '../components/ErrorMessage';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email, password);
      if (user.role === 'admin') {
        navigate('/admin');
      } else if (user.role === 'team_lead') {
        navigate('/team-lead');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Login failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen flex flex-col items-center justify-center transition-colors duration-300 px-4">
      {/* Brand Logo */}
      <div className="mb-12 flex items-center gap-2">
        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
          <span className="material-icons text-white">restaurant</span>
        </div>
        <span className="text-2xl font-bold text-background-dark dark:text-white tracking-tight">
          MHP
        </span>
      </div>

      {/* Login Card */}
      <main className="w-full max-w-md">
        <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-xl dark:shadow-2xl p-10 md:p-12 glass-card border border-primary/5 dark:border-white/5">
          {/* Header */}
          <div className="mb-10 text-center">
            <h1 className="text-3xl font-bold text-background-dark dark:text-white mb-3 tracking-tight">
              Welcome Back
            </h1>
            <p className="text-background-dark/60 dark:text-white/60 font-medium">
              Enter your details to manage office meals.
            </p>
          </div>

          <ErrorMessage message={error} onDismiss={() => setError('')} />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="block text-sm font-semibold text-background-dark/80 dark:text-white/80 ml-1"
              >
                Email Address
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <span className="material-icons text-background-dark/30 dark:text-white/30 text-xl group-focus-within:text-primary transition-colors">
                    alternate_email
                  </span>
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-background-dark/50 border border-primary/10 dark:border-white/10 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all dark:text-white placeholder:text-background-dark/30 dark:placeholder:text-white/20"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="block text-sm font-semibold text-background-dark/80 dark:text-white/80 ml-1"
              >
                Password
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <span className="material-icons text-background-dark/30 dark:text-white/30 text-xl group-focus-within:text-primary transition-colors">
                    lock_outline
                  </span>
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-background-dark/50 border border-primary/10 dark:border-white/10 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all dark:text-white placeholder:text-background-dark/30 dark:placeholder:text-white/20"
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-4 rounded-lg shadow-lg shadow-primary/20 transition-all transform hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In'}
              {!loading && (
                <span className="material-icons text-xl group-hover:translate-x-1 transition-transform">
                  arrow_forward
                </span>
              )}
            </button>
          </form>

          {/* Register link */}
          <div className="mt-10 pt-8 border-t border-primary/5 dark:border-white/5 text-center">
            <p className="text-background-dark/60 dark:text-white/60 font-medium">
              Don&apos;t have an account?{' '}
              <Link
                to="/register"
                className="text-primary font-bold hover:underline underline-offset-4 ml-1"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 text-center text-background-dark/40 dark:text-white/30 text-sm">
        <p>© 2026 Meal Headcount Planner. All rights reserved.</p>
      </footer>

      {/* Background blurs */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none -z-10 overflow-hidden">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-10 right-10 w-64 h-64 bg-primary/5 rounded-full blur-2xl"></div>
      </div>
    </div>
  );
}
