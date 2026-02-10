import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorMessage from '../components/ErrorMessage';

const TEAMS = [
  'Engineering',
  'Marketing',
  'Human Resources',
  'Sales & Operations',
  'Product & Design',
];

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [team, setTeam] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  // Simple password strength (0-4)
  const getStrength = (pw) => {
    let s = 0;
    if (pw.length >= 6) s++;
    if (pw.length >= 10) s++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
    if (/\d/.test(pw) || /[^A-Za-z0-9]/.test(pw)) s++;
    return s;
  };

  const strength = getStrength(password);
  const strengthLabel = ['Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'][
    strength
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await register(name, email, password, team || null);
      if (user.role === 'admin') {
        navigate('/admin');
      } else if (user.role === 'team_lead') {
        navigate('/team-lead');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Registration failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-primary/20">
            <span className="material-icons text-white text-3xl">
              restaurant
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Create your account
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Join MHP for corporate meal planning
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-xl shadow-xl shadow-gray-200/50 dark:shadow-none p-8">
          <ErrorMessage message={error} onDismiss={() => setError('')} />

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label
                htmlFor="full-name"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Full Name
              </label>
              <input
                id="full-name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 dark:text-white"
              />
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="reg-email"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Work Email
              </label>
              <input
                id="reg-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 dark:text-white"
              />
            </div>

            {/* Team */}
            <div>
              <label
                htmlFor="team"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Team (Optional)
              </label>
              <select
                id="team"
                value={team}
                onChange={(e) => setTeam(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 dark:text-white appearance-none"
              >
                <option value="">Select your team</option>
                {TEAMS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="reg-password"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Password
              </label>
              <input
                id="reg-password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 dark:text-white"
              />
              {password.length > 0 && (
                <div className="mt-2.5">
                  <div className="flex gap-1 h-1.5">
                    {[0, 1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`flex-1 rounded-full ${
                          i < strength
                            ? 'bg-primary'
                            : 'bg-gray-200 dark:bg-zinc-700'
                        }`}
                      ></div>
                    ))}
                  </div>
                  <p className="text-[11px] mt-1.5 text-gray-500 dark:text-gray-400">
                    Password strength:{' '}
                    <span className="text-primary font-medium">
                      {strengthLabel}
                    </span>
                  </p>
                </div>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3 rounded-lg shadow-md shadow-primary/20 transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        </div>

        {/* Login link */}
        <p className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
          Already have an account?{' '}
          <Link
            to="/login"
            className="text-primary font-semibold hover:underline decoration-2 underline-offset-4 ml-1"
          >
            Sign in
          </Link>
        </p>
      </div>

      {/* Background accents */}
      <div className="fixed top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-orange-400 to-primary"></div>
      <div className="fixed -bottom-24 -left-24 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -top-24 -right-24 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
    </div>
  );
}
