import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { mealsAPI, specialDaysAPI, eventMealsAPI, policyAPI } from '../services/api';
import MealCard from './MealCard';
import EventMealCard from './EventMealCard';
import SpecialDayBanner from './SpecialDayBanner';
import WorkLocationSelector from './WorkLocationSelector';
import WFHPeriodManager from './WFHPeriodManager';
import Loading from './Loading';
import ErrorMessage from './ErrorMessage';
import AnnouncementsBanner from './AnnouncementsBanner';

// Helper: format a Date as YYYY-MM-DD (local)
function fmtDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function EmployeeDashboardContent() {
  const { user } = useAuth();
  const [meals, setMeals] = useState([]);
  const [eventMeals, setEventMeals] = useState([]);
  const [cutoffPassed, setCutoffPassed] = useState(false);
  const [specialDay, setSpecialDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [workLocation, setWorkLocation] = useState('Office');

  // --- Range preference state ---
  const [showRange, setShowRange] = useState(false);
  const todayStr = fmtDate(new Date());
  const defaultEnd = fmtDate(new Date(Date.now() + 6 * 86400000)); // +6 days = 7 total
  const [rangeStart, setRangeStart] = useState(todayStr);
  const [rangeEnd, setRangeEnd] = useState(defaultEnd);
  const [rangeMeals, setRangeMeals] = useState({});
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeResult, setRangeResult] = useState(null);
  const [maxForwardDateStr, setMaxForwardDateStr] = useState('');

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
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      const res = await policyAPI.get();
      if (res.data?.forward_planning_days) {
        const d = new Date();
        d.setDate(d.getDate() + res.data.forward_planning_days);
        setMaxForwardDateStr(fmtDate(d));
      }
    } catch {
      // Ignore if fails
    }
  };

  // Initialise rangeMeals toggles from loaded meals (all opt-in by default)
  useEffect(() => {
    if (meals.length > 0 && Object.keys(rangeMeals).length === 0) {
      const init = {};
      meals.forEach((m) => { init[m.meal_type] = true; });
      setRangeMeals(init);
    }
  }, [meals]);

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
      const [mealsRes, eventMealsRes] = await Promise.all([
        mealsAPI.getTodayMeals(),
        eventMealsAPI.getToday()
      ]);
      setMeals(mealsRes.data.meals);
      setCutoffPassed(mealsRes.data.cutoff_passed ?? false);
      setEventMeals(eventMealsRes.data);
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
      // Instantly update UI: disable and opt out all meals
      setMeals((prev) => prev.map((m) => ({ ...m, is_participating: false })));
      // Then update backend
      const enabledMeals = meals.filter((m) => m.is_participating);
      if (enabledMeals.length > 0) {
        try {
          await Promise.all(
            enabledMeals.map((m) =>
              mealsAPI.updateParticipation(user.id, todayStr, m.meal_type, false)
            )
          );
        } catch {
          setError('Location saved, but failed to update meal preferences.');
        }
      }
    } else {
      // Back to Office — re-fetch so user sees their actual current state
      await fetchMeals();
    }
  };

  // --- Range preference handler ---
  const handleRangeSubmit = async () => {
    // Ensure at least one meal is selected
    const hasSelection = Object.values(rangeMeals).some(Boolean);
    if (!hasSelection) {
      setError('Please select at least one meal for the date range.');
      return;
    }
    setRangeLoading(true);
    setRangeResult(null);
    try {
      const res = await mealsAPI.setRange({
        startDate: rangeStart,
        endDate: rangeEnd,
        meals: rangeMeals,
      });
      setRangeResult(res.data);
      // Refresh today's view in case today was part of the range
      fetchMeals();
      setError('');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to set range preferences.';
      setError(msg);
    } finally {
      setRangeLoading(false);
    }
  };

  const selectedCount = meals.filter((m) => m.is_participating).length;

  // How many days in the selected range
  const rangeDays = useMemo(() => {
    const s = new Date(rangeStart);
    const e = new Date(rangeEnd);
    return Math.max(0, Math.round((e - s) / 86400000) + 1);
  }, [rangeStart, rangeEnd]);

  if (loading) return <Loading />;

  return (
    <>
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

        <AnnouncementsBanner />

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

        {/* Today's Meal Cards Grid */}
        <h2 className="text-xl font-semibold mb-4">Today's Meals</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {eventMeals.length > 0 && eventMeals.map((eventMeal) => (
            <EventMealCard
              key={`event-${eventMeal.id}`}
              eventMeal={eventMeal}
            />
          ))}

          {meals.map((meal) => (
            <MealCard
              key={meal.id}
              meal={meal}
              onToggle={handleToggle}
              disabled={cutoffPassed || isBlocked || workLocation === 'WFH'}
            />
          ))}
        </div>

        {/* ===========================
            Set Upcoming Meals (Range)
            =========================== */}
        <div className="mt-10">
          <button
            onClick={() => setShowRange((prev) => !prev)}
            className="flex items-center gap-2 text-primary font-semibold hover:underline focus:outline-none"
          >
            <span className="material-icons-outlined text-lg">
              {showRange ? 'expand_less' : 'date_range'}
            </span>
            {showRange ? 'Hide upcoming meals' : 'Set meals for upcoming days'}
          </button>

          {showRange && (
            <div className="mt-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-1">Set Meals for a Date Range</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
                Pre-set your meal preferences for upcoming days. Blocked dates
                (holidays, office closed, global WFH) are automatically skipped.
                Admins and WFH changes can still override individual days.
              </p>

              {/* Date pickers */}
              <div className="flex flex-wrap gap-4 mb-5">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={rangeStart}
                    min={todayStr}
                    max={maxForwardDateStr || undefined}
                    onChange={(e) => setRangeStart(e.target.value)}
                    className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={rangeEnd}
                    min={rangeStart}
                    max={maxForwardDateStr || undefined}
                    onChange={(e) => setRangeEnd(e.target.value)}
                    className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div className="flex items-end">
                  <span className="text-xs text-slate-500 dark:text-slate-400 pb-2">
                    {rangeDays} day{rangeDays !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Meal toggles */}
              <div className="mb-5">
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-2">
                  Meals to opt in / out:
                </p>
                <div className="flex flex-wrap gap-3">
                  {meals.map((m) => {
                    const active = rangeMeals[m.meal_type] ?? false;
                    return (
                      <button
                        key={m.meal_type}
                        type="button"
                        onClick={() =>
                          setRangeMeals((prev) => ({
                            ...prev,
                            [m.meal_type]: !prev[m.meal_type],
                          }))
                        }
                        className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${active
                          ? 'bg-primary text-white border-primary'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-600'
                          }`}
                      >
                        {m.meal_type.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                        <span className="ml-1">{active ? '✓' : '✕'}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Submit */}
              <button
                onClick={handleRangeSubmit}
                disabled={rangeLoading}
                className="bg-primary text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {rangeLoading ? 'Saving...' : 'Apply to Date Range'}
              </button>

              {/* Result summary */}
              {rangeResult && (
                <div className="mt-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-lg p-4 text-sm">
                  <p className="font-medium text-emerald-800 dark:text-emerald-200 mb-1">
                    Updated {rangeResult.updated_dates.length} day{rangeResult.updated_dates.length !== 1 ? 's' : ''} successfully.
                  </p>
                  {rangeResult.skipped_dates.length > 0 && (
                    <div className="mt-2">
                      <p className="text-slate-600 dark:text-slate-300 font-medium mb-1">
                        Skipped {rangeResult.skipped_dates.length} day{rangeResult.skipped_dates.length !== 1 ? 's' : ''}:
                      </p>
                      <ul className="list-disc list-inside text-slate-500 dark:text-slate-400">
                        {rangeResult.skipped_dates.map((s) => (
                          <li key={s.date}>
                            {s.date} — {s.reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
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

        {/* WFH Periods */}
        <div className="mt-10">
          <WFHPeriodManager />
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
    </>
  );
}
