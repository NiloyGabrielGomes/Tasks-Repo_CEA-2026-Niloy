import { useState, useEffect } from 'react';
import { mealsAPI, usersAPI } from '../services/api';

const MEAL_OPTIONS = [
  { value: 'lunch', label: 'Lunch' },
  { value: 'snacks', label: 'Snacks' },
  { value: 'iftar', label: 'Iftar' },
  { value: 'event_dinner', label: 'Event Dinner' },
  { value: 'optional_dinner', label: 'Late Dinner' },
];

export default function BulkActionForm({ scope = 'all', team = null, onDone }) {
  const [users, setUsers] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [meals, setMeals] = useState({});
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = scope === 'team'
        ? await usersAPI.getTeamUsers()
        : await usersAPI.getAllUsers();
      setUsers((res.data.users || []).filter((u) => u.is_active));
    } catch {
      setError('Failed to load users.');
    }
  };

  const toggleUser = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    const visible = filtered.map((u) => u.id);
    const allSelected = visible.every((id) => selectedIds.includes(id));
    setSelectedIds(allSelected
      ? selectedIds.filter((id) => !visible.includes(id))
      : [...new Set([...selectedIds, ...visible])]
    );
  };

  const toggleMeal = (meal) => {
    setMeals((prev) => {
      const copy = { ...prev };
      if (meal in copy) delete copy[meal];
      else copy[meal] = false; // default: opt out
      return copy;
    });
  };

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleSubmit = async () => {
    if (selectedIds.length === 0) { setError('Select at least one user.'); return; }
    if (Object.keys(meals).length === 0) { setError('Select at least one meal.'); return; }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await mealsAPI.bulkUpdate({
        user_ids: selectedIds,
        date,
        meals,
        reason: reason || null,
      });
      const d = res.data;
      const msg = `Updated ${d.updated_count} record(s)${d.failed?.length ? `, ${d.failed.length} failed` : ''}.`;
      setSuccess(msg);
      setSelectedIds([]);
      setMeals({});
      setReason('');
      setConfirming(false);
      onDone?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Bulk update failed.');
      setConfirming(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700">
        <h2 className="font-bold text-lg flex items-center gap-2">
          <span className="material-icons-outlined text-primary">group_work</span>
          Bulk Meal Update
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Update meal participation for multiple {scope === 'team' ? 'team members' : 'users'} at once.
        </p>
      </div>

      <div className="p-6 space-y-5">
        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm">
            {success}
          </div>
        )}

        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Date</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
            className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary" />
        </div>

        {/* Meals */}
        <div>
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">Meals to opt out</label>
          <div className="flex flex-wrap gap-2">
            {MEAL_OPTIONS.map((m) => {
              const selected = m.value in meals;
              return (
                <button key={m.value} type="button" onClick={() => toggleMeal(m.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    selected
                      ? 'bg-primary text-white border-primary'
                      : 'bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-primary/50'
                  }`}>
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* User list */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
              Users ({selectedIds.length} selected)
            </label>
            <button type="button" onClick={selectAll} className="text-xs text-primary hover:underline">
              {filtered.length > 0 && filtered.every((u) => selectedIds.includes(u.id)) ? 'Deselect all' : 'Select all'}
            </button>
          </div>
          <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full mb-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary" />
          <div className="max-h-48 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg divide-y divide-slate-100 dark:divide-slate-700">
            {filtered.map((u) => (
              <label key={u.id} className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-900/50 cursor-pointer text-sm">
                <input type="checkbox" checked={selectedIds.includes(u.id)} onChange={() => toggleUser(u.id)}
                  className="rounded border-slate-300 text-primary focus:ring-primary" />
                <span className="font-medium">{u.name}</span>
                <span className="text-xs text-slate-400 ml-auto">{u.email}</span>
              </label>
            ))}
            {filtered.length === 0 && (
              <p className="px-3 py-4 text-xs text-slate-400 text-center">No users found.</p>
            )}
          </div>
        </div>

        {/* Reason */}
        <div>
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Reason (optional)</label>
          <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Team outing"
            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary" />
        </div>

        {/* Submit */}
        {!confirming ? (
          <button type="button" onClick={() => setConfirming(true)}
            disabled={selectedIds.length === 0 || Object.keys(meals).length === 0}
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed">
            Apply Bulk Update
          </button>
        ) : (
          <div className="flex items-center gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <span className="text-sm text-amber-700 dark:text-amber-300">
              Update {Object.keys(meals).length} meal(s) for {selectedIds.length} user(s)?
            </span>
            <button onClick={handleSubmit} disabled={loading}
              className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary/90 disabled:opacity-50">
              {loading ? 'Updating...' : 'Confirm'}
            </button>
            <button onClick={() => setConfirming(false)}
              className="px-3 py-1.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-xs font-medium">
              Cancel
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
