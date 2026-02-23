import { useState, useEffect, useRef, useCallback } from 'react';
import { mealsAPI, usersAPI, specialDaysAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import useHeadcountStream from '../hooks/useHeadcountStream';
import Navbar from '../components/Navbar';
import HeadcountTable from '../components/HeadcountTable';
import SpecialDayBanner from '../components/SpecialDayBanner';
import BulkActionForm from '../components/BulkActionForm';
import AnnouncementDraft from '../components/AnnouncementDraft';
import WFHPeriodManager from '../components/WFHPeriodManager';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

const MEAL_TYPES = [
  { value: 'lunch', label: 'Lunch' },
  { value: 'snacks', label: 'Snacks' },
  { value: 'iftar', label: 'Iftar' },
  { value: 'event_dinner', label: 'Event Dinner' },
  { value: 'optional_dinner', label: 'Late Dinner' },
];

export default function TeamManagementView() {
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

  // Special day
  const [specialDay, setSpecialDay] = useState(null);

  // ── SSE live headcount ───────────────────────────────────────
  const { headcount: liveData } = useHeadcountStream(selectedDate);
  const prevLiveTimestampRef = useRef(null);

  useEffect(() => {
    fetchData();
    fetchSpecialDay();
  }, [selectedDate]);

  const fetchSpecialDay = async () => {
    try {
      const res = await specialDaysAPI.getByDate(selectedDate);
      setSpecialDay(res.data);
    } catch {
      setSpecialDay(null);
    }
  };

  // Silent headcount-only refresh triggered by SSE (no loading spinner)
  const refreshHeadcount = useCallback(async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const headcountRes = selectedDate === today
        ? await mealsAPI.getTeamHeadcountToday()
        : await mealsAPI.getTeamHeadcount(selectedDate);
      setHeadcount(headcountRes.data.headcount);
    } catch {
      // non-critical, ignore
    }
  }, [selectedDate]);

  // Re-fetch when SSE signals a headcount change
  useEffect(() => {
    if (!liveData?.timestamp) return;
    if (liveData.timestamp === prevLiveTimestampRef.current) return;
    prevLiveTimestampRef.current = liveData.timestamp;
    refreshHeadcount();
  }, [liveData, refreshHeadcount]);

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
      const res = await mealsAPI.batchAdminUpdateParticipation([
        {
          user_id: participationUser.id,
          meal_type: meal.meal_type,
          is_participating: newValue,
        },
      ]);
      const failedItems = res.data.results.filter((r) => !r.success);
      if (failedItems.length > 0) {
        setError(failedItems.map((f) => f.message).join(', '));
        return;
      }
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
              Team Management
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

        <SpecialDayBanner specialDay={specialDay} />

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
          <HeadcountTable headcount={headcount} totalUsers={activeUsers} date={selectedDate} refreshKey={liveData?.timestamp} />
        </div>

        {/* Announcements */}
        <div className="mb-10">
          <AnnouncementDraft />
        </div>

        {/* WFH Periods */}
        <div className="mb-10">
          <WFHPeriodManager />
        </div>

        {/* Bulk Actions */}
        <div className="mb-10">
          <BulkActionForm scope="team" team={user?.team} onDone={fetchData} />
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
                placeholder="Search member..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full sm:w-64 pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                  <th className="px-6 py-3 font-semibold">Employee</th>
                  <th className="px-6 py-3 font-semibold">Email</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700 text-sm">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-slate-100">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                          {u.name.charAt(0)}
                        </div>
                        {u.name}
                        {!u.is_active && (
                          <span className="text-[10px] px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full font-medium">
                            Inactive
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400">
                      {u.email}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => openParticipationModal(u)}
                        className="text-primary hover:text-primary-dark font-medium text-xs border border-primary/20 hover:border-primary/50 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        Manage Meals
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan="3" className="px-6 py-8 text-center text-slate-400">
                      No members found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Modal */}
        {showParticipationModal && participationUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-900/50">
                <h3 className="font-bold text-lg">Manage Participation</h3>
                <button
                  onClick={() => setShowParticipationModal(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                >
                  <span className="material-icons-outlined">close</span>
                </button>
              </div>

              <div className="p-6">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl font-bold">
                    {participationUser.name.charAt(0)}
                  </div>
                  <div>
                    <h4 className="font-bold text-lg">{participationUser.name}</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{participationUser.email}</p>
                  </div>
                </div>

                {participationLoading ? (
                  <div className="py-8 flex justify-center">
                    <Loading />
                  </div>
                ) : (
                  <div className="space-y-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                       Meals for {new Date().toLocaleDateString()}
                    </p>
                    {participationMeals.length === 0 ? (
                       <p className="text-sm text-slate-500">No meals found for today.</p>
                    ) : (
                      participationMeals.map((meal) => (
                        <div key={meal.meal_type} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                          <span className="font-medium capitalize flex items-center gap-2">
                             {MEAL_TYPES.find(t => t.value === meal.meal_type)?.label || meal.meal_type}
                             {meal.is_participating && <span className="w-2 h-2 rounded-full bg-emerald-500"></span>}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                              meal.is_participating
                                ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400'
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-500'
                            }`}>
                              {meal.is_participating ? 'Opted In' : 'Opted Out'}
                            </span>
                            <button
                               onClick={() => handleToggleMeal(meal, !meal.is_participating)}
                               className="text-xs font-medium text-primary hover:underline ml-2"
                            >
                              {meal.is_participating ? 'Cancel' : 'Add'}
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div className="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-700 text-right">
                <button
                  onClick={() => setShowParticipationModal(false)}
                  className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
