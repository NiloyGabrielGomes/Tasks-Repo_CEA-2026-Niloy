import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { mealsAPI, specialDaysAPI } from '../services/api';
import Navbar from '../components/Navbar';
import MealCard from '../components/MealCard';
import SpecialDayBanner from '../components/SpecialDayBanner';
import WorkLocationSelector from '../components/WorkLocationSelector';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

export default function EmployeeDashboard() {
  const { user } = useAuth();
  const [meals, setMeals] = useState([]);
  const [cutoffPassed, setCutoffPassed] = useState(false);
  const [specialDay, setSpecialDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [workLocation, setWorkLocation] = useState('Office');

  const today = new Date();
  const dayName = today.toLocaleDateString('en-US', { weekday: 'long' });
  const dateStr = today.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  // Greeting based on time
  const hour = today.getHours();
  const greeting =
    hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  useEffect(() => {
    fetchMeals();
    fetchSpecialDay();
  }, []);

  const fetchSpecialDay = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await specialDaysAPI.getByDate(today);
      setSpecialDay(res.data);
    } catch {
      setSpecialDay(null);
    }
  };

  const isBlocked = specialDay && (specialDay.day_type === 'officeclosed' || specialDay.day_type === 'governmentholiday');

  const fetchMeals = async () => {
    setLoading(true);
    try {
      const res = await mealsAPI.getTodayMeals();
      setMeals(res.data.meals);
      setCutoffPassed(res.data.cutoff_passed ?? false);
      setError('');
    } catch (err) {
      setError('Failed to load meals. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (meal, newValue) => {
    if (cutoffPassed) {
      setError('Meal preferences are locked after 9:00 PM. You can update again tomorrow morning.');
      return;
    }
    try {
      await mealsAPI.updateParticipation(
        user.id,
        meal.date,
        meal.meal_type,
        newValue
      );
      // Update local state
      setMeals((prev) =>
        prev.map((m) =>
          m.id === meal.id ? { ...m, is_participating: newValue } : m
        )
      );
    } catch (err) {
      setError('Failed to update meal preference.');
    }
  };

  const handleLocationChange = async (newLocation) => {
    setWorkLocation(newLocation);
    const todayStr = new Date().toISOString().split('T')[0];

    if (newLocation === 'WFH') {
      // Opt the employee out of every enabled meal using their own per-meal endpoint
      const enabledMeals = meals.filter((m) => m.is_participating);
      if (enabledMeals.length > 0) {
        try {
          await Promise.all(
            enabledMeals.map((m) =>
              mealsAPI.updateParticipation(user.id, todayStr, m.meal_type, false)
            )
          );
          setMeals((prev) => prev.map((m) => ({ ...m, is_participating: false })));
        } catch {
          setError('Location saved, but failed to update meal preferences.');
        }
      }
    } else {
      // Back to Office — re-fetch so user sees their actual current state
      await fetchMeals();
    }
  };

  const selectedCount = meals.filter((m) => m.is_participating).length;

  if (loading) return <Loading />;

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen text-slate-900 dark:text-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Greeting */}
        <header className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            {greeting}, {user?.name?.split(' ')[0]}
          </h1>
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 font-medium">
            <span className="material-icons-outlined text-sm">
              calendar_today
            </span>
            <span>
              {dayName}, {dateStr}
            </span>
          </div>
        </header>

        <ErrorMessage message={error} onDismiss={() => setError('')} />

        <SpecialDayBanner specialDay={specialDay} />

        {/* Cutoff Banner */}
        {cutoffPassed && !isBlocked && (
          <div className="mb-6 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-xl p-4 flex items-center gap-3">
            <span className="material-icons-outlined text-amber-500">lock_clock</span>
            <p className="text-amber-800 dark:text-amber-200 text-sm font-medium">
              Meal preferences are locked after 9:00 PM. You can update again tomorrow morning.
            </p>
          </div>
        )}

        {/* Work Location Selector */}
        {!isBlocked && (
          <div className="mb-8">
            <WorkLocationSelector
              disabled={cutoffPassed}
              onLoad={(loc) => setWorkLocation(loc)}
              onChange={handleLocationChange}
            />
          </div>
        )}

        {/* WFH Meal Notice */}
        {workLocation === 'WFH' && !isBlocked && (
          <div className="mb-6 bg-sky-50 dark:bg-sky-900/30 border border-sky-200 dark:border-sky-700 rounded-xl p-4 flex items-center gap-3">
            <span className="material-icons-outlined text-sky-500">home</span>
            <p className="text-sky-800 dark:text-sky-200 text-sm font-medium">
              You're working from home — meals have been opted out automatically. Switch to Office to re-enable.
            </p>
          </div>
        )}

        {/* Meal Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {meals.map((meal) => (
            <MealCard
              key={meal.id}
              meal={meal}
              onToggle={handleToggle}
              disabled={cutoffPassed || isBlocked || workLocation === 'WFH'}
            />
          ))}
        </div>

        {/* Info Card */}
        <div className="mt-12">
          <div className="bg-primary rounded-xl p-8 text-white relative overflow-hidden">
            <div className="relative z-10">
              <span className="material-icons-outlined text-4xl mb-4 text-white/80">
                info
              </span>
              <h2 className="text-2xl font-bold mb-4">Office Food Policy</h2>
              <p className="text-white/80 text-sm leading-relaxed mb-6">
                Remember to toggle your preferences before 9:00 PM each day to
                ensure minimal food waste. Special dietary requests can be
                managed in settings.
              </p>
            </div>
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-white/10 rounded-full blur-3xl"></div>
            <div className="absolute -left-12 -top-12 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div>
          </div>
        </div>
      </main>

      {/* Bottom summary bar */}
      <footer className="fixed bottom-8 left-1/2 -translate-x-1/2 w-[90%] max-w-lg z-50">
        <div className="bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 px-6 py-4 rounded-2xl shadow-2xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            <p className="text-sm font-medium">
              {selectedCount} Meal{selectedCount !== 1 ? 's' : ''} selected for
              today
            </p>
          </div>
          <button
            onClick={fetchMeals}
            className="bg-primary/20 dark:bg-primary/10 text-primary px-4 py-2 rounded-lg text-xs font-bold hover:bg-primary/30 transition-colors"
          >
            REFRESH
          </button>
        </div>
      </footer>
    </div>
  );
}
