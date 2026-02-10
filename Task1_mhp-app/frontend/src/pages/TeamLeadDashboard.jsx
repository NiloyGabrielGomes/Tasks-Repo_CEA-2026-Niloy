import { useState, useEffect } from 'react';
import { mealsAPI, usersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import HeadcountTable from '../components/HeadcountTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

export default function TeamLeadDashboard() {
  const { user } = useAuth();
  const [headcount, setHeadcount] = useState(null);
  const [users, setUsers] = useState([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const headcountPromise =
        selectedDate === today
          ? mealsAPI.getDeptHeadcountToday()
          : mealsAPI.getDeptHeadcount(selectedDate);

      const [headcountRes, usersRes] = await Promise.all([
        headcountPromise,
        usersAPI.getDepartmentUsers(),
      ]);

      setHeadcount(headcountRes.data.headcount);
      setUsers(usersRes.data.users);
      setTotalUsers(usersRes.data.total);
      setError('');
    } catch (err) {
      setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  // Stats
  const totalHeadcount = headcount
    ? Object.values(headcount).reduce((a, b) => a + b, 0)
    : 0;
  const activeUsers = users.filter((u) => u.is_active).length;

  if (loading) return <Loading />;

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen text-slate-900 dark:text-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-1">
              Team Lead Dashboard
            </h1>
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-sm">
              <span className="material-icons-outlined text-primary text-base">
                apartment
              </span>
              <span>
                {user?.department || 'Department'} &mdash; department overview
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="pl-4 pr-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium focus:ring-primary focus:border-primary cursor-pointer dark:text-white"
            />
          </div>
        </header>

        <ErrorMessage message={error} onDismiss={() => setError('')} />

        {/* Department badge */}
        <div className="mb-10 flex items-center gap-3">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-semibold">
            <span className="material-icons-outlined text-base">business</span>
            {user?.department}
          </div>
          <span className="text-xs text-slate-400">
            Showing data only for your department
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">
                  group
                </span>
              </div>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">
              Dept Headcount
            </h3>
            <p className="text-3xl font-bold mt-1">{totalHeadcount}</p>
          </div>

          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">
                  restaurant_menu
                </span>
              </div>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">
              Meal Types Available
            </h3>
            <p className="text-3xl font-bold mt-1">
              {headcount ? Object.keys(headcount).length : 0}
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">
                  person_outline
                </span>
              </div>
              <span className="text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-full">
                {activeUsers} active
              </span>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">
              Dept Members
            </h3>
            <p className="text-3xl font-bold mt-1">{totalUsers}</p>
          </div>
        </div>

        {/* Headcount Summary */}
        <div className="mb-10">
          <HeadcountTable headcount={headcount} totalUsers={totalUsers} />
        </div>

        {/* Department Members */}
        <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
            <h2 className="font-bold text-lg">
              Department Members
            </h2>
            <span className="text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-full">
              {user?.department}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4 font-semibold">Name</th>
                  <th className="px-6 py-4 font-semibold">Email</th>
                  <th className="px-6 py-4 font-semibold">Role</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {users.map((u) => (
                  <tr
                    key={u.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-500 dark:text-slate-300">
                          {u.name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')
                            .toUpperCase()
                            .slice(0, 2)}
                        </div>
                        <span className="text-sm font-medium">{u.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {u.email}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary capitalize">
                        {u.role?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mr-1.5"></span>
                          Inactive
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700">
            <span className="text-xs text-slate-500">
              Showing {users.length} member{users.length !== 1 ? 's' : ''} in{' '}
              {user?.department}
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}
