import { useState, useEffect } from 'react';
import { mealsAPI, usersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import HeadcountTable from '../components/HeadcountTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

const MEAL_TYPES = [
  { value: 'lunch', label: 'Lunch' },
  { value: 'snacks', label: 'Snacks' },
  { value: 'iftar', label: 'Iftar' },
  { value: 'event_dinner', label: 'Event Dinner' },
  { value: 'optional_dinner', label: 'Late Dinner' },
];

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
  const [success, setSuccess] = useState('');

  // Participation override modal
  const [showParticipationModal, setShowParticipationModal] = useState(false);
  const [participationUser, setParticipationUser] = useState(null);
  const [participationMeals, setParticipationMeals] = useState([]);
  const [participationLoading, setParticipationLoading] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const headcountPromise =
        selectedDate === today
          ? mealsAPI.getTeamHeadcountToday()
          : mealsAPI.getTeamHeadcount(selectedDate);

      const [headcountRes, usersRes] = await Promise.all([
        headcountPromise,
        usersAPI.getTeamUsers(),
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

  // ===========================
  // Participation Override
  // ===========================
  const openParticipationModal = async (targetUser) => {
    setParticipationUser(targetUser);
    setParticipationLoading(true);
    setShowParticipationModal(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await mealsAPI.getUserMeals(targetUser.id, today);
      setParticipationMeals(res.data.meals);
    } catch (err) {
      setError('Failed to load user meals.');
    } finally {
      setParticipationLoading(false);
    }
  };

  const handleToggleMeal = async (meal, newValue) => {
    try {
      await mealsAPI.adminUpdateParticipation(
        participationUser.id,
        meal.meal_type,
        newValue
      );
      setParticipationMeals((prev) =>
        prev.map((m) =>
          m.meal_type === meal.meal_type
            ? { ...m, is_participating: newValue }
            : m
        )
      );
      setSuccess(`Participation updated for ${participationUser.name}.`);
      // Refresh headcount
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate === today) {
        const hcRes = await mealsAPI.getTeamHeadcountToday();
        setHeadcount(hcRes.data.headcount);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update participation.');
    }
  };

  // Stats
  const totalHeadcount = headcount
    ? Object.values(headcount).reduce((a, b) => a + b, 0)
    : 0;
  const activeUsers = users.filter((u) => u.is_active).length;

  // Filtered users
  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
                {user?.team || 'Team'} &mdash; team overview
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
        {success && (
          <div className="mb-6 flex items-center p-3.5 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-900/30 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm">
            <span className="material-icons-outlined mr-2 text-lg">check_circle</span>
            <span className="font-medium flex-1">{success}</span>
            <button onClick={() => setSuccess('')} className="ml-2 text-emerald-400 hover:text-emerald-600 transition-colors">
              <span className="material-icons-outlined text-lg">close</span>
            </button>
          </div>
        )}

        {/* Team badge */}
        <div className="mb-10 flex items-center gap-3">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-semibold">
            <span className="material-icons-outlined text-base">business</span>
            {user?.team}
          </div>
          <span className="text-xs text-slate-400">
            Showing data only for your team
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">group</span>
              </div>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">Team Headcount</h3>
            <p className="text-3xl font-bold mt-1">{totalHeadcount}</p>
          </div>

          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">restaurant_menu</span>
              </div>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">Meal Types Available</h3>
            <p className="text-3xl font-bold mt-1">{headcount ? Object.keys(headcount).length : 0}</p>
          </div>

          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <span className="material-icons-outlined text-primary">person_outline</span>
              </div>
              <span className="text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-full">
                {activeUsers} active
              </span>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">Team Members</h3>
            <p className="text-3xl font-bold mt-1">{totalUsers}</p>
          </div>
        </div>

        {/* Headcount Summary */}
        <div className="mb-10">
          <HeadcountTable headcount={headcount} totalUsers={activeUsers} />
        </div>

        {/* Team Members */}
        <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <h2 className="font-bold text-lg">Team Members</h2>
              <span className="text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-full">
                {user?.team}
              </span>
            </div>
            {/* Search */}
            <div className="relative w-full sm:w-auto">
              <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
                <span className="material-icons-outlined text-lg">search</span>
              </span>
              <input
                type="text"
                placeholder="Search members..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm w-full sm:w-56 focus:ring-primary focus:border-primary dark:text-white"
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4 font-semibold">Name</th>
                  <th className="px-6 py-4 font-semibold">Email</th>
                  <th className="px-6 py-4 font-semibold">Role</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-500 dark:text-slate-300">
                          {u.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)}
                        </div>
                        <span className="text-sm font-medium">{u.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{u.email}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary capitalize">
                        {u.role?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5">Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mr-1.5">Inactive</span>
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => openParticipationModal(u)}
                        title="Update Participation"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-primary/10 transition-colors"
                      >
                        <span className="material-icons-outlined text-lg">restaurant</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700">
            <span className="text-xs text-slate-500">
              Showing {filteredUsers.length} member{filteredUsers.length !== 1 ? 's' : ''} in{' '}
              {user?.team}
            </span>
          </div>
        </section>
      </main>

      {/* ===========================
          Participation Override Modal
          =========================== */}
      {showParticipationModal && participationUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md border border-slate-200 dark:border-slate-700">
            <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg">Update Participation</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">for {participationUser.name}</p>
              </div>
              <button onClick={() => { setShowParticipationModal(false); setParticipationUser(null); }}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white">
                <span className="material-icons-outlined">close</span>
              </button>
            </div>
            <div className="p-6">
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Date: {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
              {participationLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-3">
                  {participationMeals.map((meal) => {
                    const label = MEAL_TYPES.find((m) => m.value === meal.meal_type)?.label || meal.meal_type;
                    return (
                      <div key={meal.meal_type} className="flex items-center justify-between py-2 px-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                        <span className="text-sm font-medium">{label}</span>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs ${meal.is_participating ? 'text-emerald-600' : 'text-slate-400'}`}>
                            {meal.is_participating ? 'Opted In' : 'Opted Out'}
                          </span>
                          <button
                            onClick={() => handleToggleMeal(meal, !meal.is_participating)}
                            className={`relative inline-block w-11 h-6 rounded-full transition-colors cursor-pointer ${meal.is_participating ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-600'}`}>
                            <span className={`block w-4 h-4 mt-1 ml-1 rounded-full bg-white shadow transform transition-transform ${meal.is_participating ? 'translate-x-5' : ''}`}></span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              <div className="flex justify-between mt-6 pt-4 border-t border-slate-100 dark:border-slate-700">
                <button
                  onClick={() => {
                    participationMeals.forEach((meal) => {
                      if (meal.is_participating) handleToggleMeal(meal, false);
                    });
                  }}
                  className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                  Opt Out All
                </button>
                <button
                  onClick={() => { setShowParticipationModal(false); setParticipationUser(null); }}
                  className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm">
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
