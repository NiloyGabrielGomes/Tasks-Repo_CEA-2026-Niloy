import { useState, useEffect } from 'react';
import { headcountAPI } from '../services/api';

const MEAL_LABELS = {
  lunch: 'Lunch',
  snacks: 'Snacks',
  iftar: 'Iftar',
  event_dinner: 'Event Dinner',
  optional_dinner: 'Late Dinner',
};

const TABS = [
  { id: 'meals', label: 'Meals', icon: 'restaurant' },
  { id: 'team', label: 'By Team', icon: 'groups' },
  { id: 'location', label: 'By Location', icon: 'location_on' },
];

// ── helpers ──────────────────────────────────────────────────────────────────

function TabBar({ active, onChange }) {
  return (
    <div className="flex gap-1 border-b border-slate-100 dark:border-slate-700 px-6 pt-2">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={[
            'flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t transition-colors',
            active === t.id
              ? 'text-primary border-b-2 border-primary -mb-px'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300',
          ].join(' ')}
        >
          <span className="material-icons-outlined text-base">{t.icon}</span>
          {t.label}
        </button>
      ))}
    </div>
  );
}

function LoadingRow() {
  return (
    <div className="flex items-center justify-center py-10 text-slate-400">
      <span className="material-icons-outlined animate-spin mr-2">refresh</span>
      Loading…
    </div>
  );
}

function ErrorRow({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-red-500 gap-2">
      <span className="material-icons-outlined text-2xl">error_outline</span>
      <p className="text-sm">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-xs underline text-primary hover:opacity-80">
          Retry
        </button>
      )}
    </div>
  );
}

// ── tab panels ────────────────────────────────────────────────────────────────

function MealsPanel({ headcount, totalUsers }) {
  if (!headcount) {
    return (
      <div className="py-10 text-center text-slate-400 text-sm">No meal data available.</div>
    );
  }
  const entries = Object.entries(headcount);
  const max = totalUsers || 1;

  return (
    <div className="p-6 space-y-5">
      {entries.map(([mealType, count]) => {
        const pct = Math.round((count / max) * 100);
        return (
          <div key={mealType}>
            <div className="flex justify-between items-end mb-1.5">
              <span className="font-semibold text-sm text-slate-900 dark:text-white">
                {MEAL_LABELS[mealType] || mealType}
              </span>
              <div className="text-right">
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {count} / {max}
                </span>
                <span className="text-xs text-slate-400 ml-1">({pct}%)</span>
              </div>
            </div>
            <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TeamPanel({ date, refreshKey }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(new Set());

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await headcountAPI.byTeam(date);
      setData(res.data);
    } catch {
      setError('Failed to load team breakdown.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when date changes OR when a live SSE update arrives (refreshKey)
  useEffect(() => { fetchData(); }, [date, refreshKey]);

  const toggleTeam = (team) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(team) ? next.delete(team) : next.add(team);
      return next;
    });

  if (loading) return <LoadingRow />;
  if (error) return <ErrorRow message={error} onRetry={fetchData} />;
  if (!data || !data.teams?.length)
    return <div className="py-10 text-center text-slate-400 text-sm">No team data available.</div>;

  const total = data.total_employees;

  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-700">
      {/* summary strip */}
      <div className="px-6 py-3 flex items-center gap-4 bg-slate-50 dark:bg-slate-750 text-xs text-slate-500">
        <span>
          <strong className="text-slate-700 dark:text-slate-300">{total}</strong> active employees
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" /> Office
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-sky-400" /> WFH
        </span>
      </div>

      {data.teams.map((t) => {
        const isOpen = expanded.has(t.team);
        const officePct = t.total_members > 0
          ? Math.round((t.office_count / t.total_members) * 100)
          : 0;
        return (
          <div key={t.team}>
            <button
              onClick={() => toggleTeam(t.team)}
              className="w-full flex items-center px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors text-left gap-3"
            >
              <span className="material-icons-outlined text-slate-400 text-base">
                {isOpen ? 'expand_less' : 'expand_more'}
              </span>
              <span className="flex-1 font-semibold text-sm text-slate-900 dark:text-white truncate">
                {t.team}
              </span>
              <div className="hidden sm:flex items-center gap-2 w-32">
                <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${officePct}%` }}
                  />
                </div>
              </div>
              <div className="flex gap-3 text-xs font-medium shrink-0">
                <span className="text-emerald-600 dark:text-emerald-400">{t.office_count} Office</span>
                <span className="text-sky-500 dark:text-sky-400">{t.wfh_count} WFH</span>
                <span className="text-slate-400">/ {t.total_members}</span>
              </div>
            </button>

            {isOpen && (
              <div className="bg-slate-50 dark:bg-slate-750 border-t border-slate-100 dark:border-slate-700">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="text-slate-400 uppercase text-[11px]">
                      <th className="px-8 py-2">Name</th>
                      <th className="px-4 py-2">Email</th>
                      <th className="px-4 py-2 text-right">Location</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {t.members.map((m) => {
                      const isWFH = m.location === 'WFH';
                      return (
                        <tr
                          key={m.user_id}
                          className="hover:bg-white dark:hover:bg-slate-800 transition-colors"
                        >
                          <td className="px-8 py-2 font-medium text-slate-700 dark:text-slate-200">
                            {m.name}
                          </td>
                          <td className="px-4 py-2 text-slate-500">{m.email}</td>
                          <td className="px-4 py-2 text-right">
                            <span
                              className={[
                                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium',
                                isWFH
                                  ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300'
                                  : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
                              ].join(' ')}
                            >
                              <span className="material-icons-outlined text-[11px]">
                                {isWFH ? 'home' : 'apartment'}
                              </span>
                              {m.location}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function LocationPanel({ date, refreshKey }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(new Set(['Office', 'WFH']));

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await headcountAPI.byLocation(date);
      setData(res.data);
    } catch {
      setError('Failed to load location breakdown.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when date changes OR when a live SSE update arrives (refreshKey)
  useEffect(() => { fetchData(); }, [date, refreshKey]);

  const toggleLocation = (loc) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(loc) ? next.delete(loc) : next.add(loc);
      return next;
    });

  if (loading) return <LoadingRow />;
  if (error) return <ErrorRow message={error} onRetry={fetchData} />;
  if (!data) return null;

  const total = data.total_employees || 1;
  const LOCATION_STYLE = {
    Office: {
      dot: 'bg-emerald-500',
      badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
      bar: 'bg-emerald-500',
    },
    WFH: {
      dot: 'bg-sky-400',
      badge: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
      bar: 'bg-sky-400',
    },
  };

  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-700">
      {/* summary bars */}
      <div className="px-6 py-4 flex flex-col sm:flex-row gap-4 bg-slate-50 dark:bg-slate-750">
        {(data.locations || []).map((loc) => {
          const pct = Math.round((loc.count / total) * 100);
          const style = LOCATION_STYLE[loc.location] || {};
          return (
            <div key={loc.location} className="flex items-center gap-2 flex-1 min-w-0">
              <span className={`inline-block w-3 h-3 rounded-full shrink-0 ${style.dot}`} />
              <div className="flex-1 min-w-0">
                <div className="flex justify-between text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">
                  <span>{loc.location}</span>
                  <span className="text-slate-500">{loc.count} ({pct}%)</span>
                </div>
                <div className="w-full h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${style.bar}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* expandable per-location lists */}
      {(data.locations || []).map((loc) => {
        const isOpen = expanded.has(loc.location);
        const style = LOCATION_STYLE[loc.location] || {};
        return (
          <div key={loc.location}>
            <button
              onClick={() => toggleLocation(loc.location)}
              className="w-full flex items-center px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors text-left gap-3"
            >
              <span className="material-icons-outlined text-slate-400 text-base">
                {isOpen ? 'expand_less' : 'expand_more'}
              </span>
              <span className={`inline-block w-2.5 h-2.5 rounded-full ${style.dot}`} />
              <span className="flex-1 font-semibold text-sm text-slate-900 dark:text-white">
                {loc.location}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${style.badge}`}>
                {loc.count} employee{loc.count !== 1 ? 's' : ''}
              </span>
            </button>

            {isOpen && loc.employees?.length > 0 && (
              <div className="bg-slate-50 dark:bg-slate-750 border-t border-slate-100 dark:border-slate-700">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="text-slate-400 uppercase text-[11px]">
                      <th className="px-8 py-2">Name</th>
                      <th className="px-4 py-2">Email</th>
                      <th className="px-4 py-2">Team</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {loc.employees.map((e) => (
                      <tr
                        key={e.user_id}
                        className="hover:bg-white dark:hover:bg-slate-800 transition-colors"
                      >
                        <td className="px-8 py-2 font-medium text-slate-700 dark:text-slate-200">{e.name}</td>
                        <td className="px-4 py-2 text-slate-500">{e.email}</td>
                        <td className="px-4 py-2 text-slate-500">{e.team || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {isOpen && !loc.employees?.length && (
              <div className="px-8 py-4 text-xs text-slate-400 bg-slate-50 dark:bg-slate-750 border-t border-slate-100 dark:border-slate-700">
                No employees at this location.
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── main export ───────────────────────────────────────────────────────────────

export default function HeadcountTable({ headcount, totalUsers, date, refreshKey }) {
  const [activeTab, setActiveTab] = useState('meals');
  const resolvedDate = date || new Date().toISOString().split('T')[0];

  return (
    <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
        <h2 className="font-bold text-lg text-slate-900 dark:text-white">Headcount Summary</h2>
        <span className="text-xs text-slate-400 font-medium">{resolvedDate}</span>
      </div>

      <TabBar active={activeTab} onChange={setActiveTab} />

      {activeTab === 'meals' && (
        <MealsPanel headcount={headcount} totalUsers={totalUsers} />
      )}
      {activeTab === 'team' && <TeamPanel date={resolvedDate} refreshKey={refreshKey} />}
      {activeTab === 'location' && <LocationPanel date={resolvedDate} refreshKey={refreshKey} />}
    </section>
  );
}
