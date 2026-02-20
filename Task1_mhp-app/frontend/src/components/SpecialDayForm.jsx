import { useState, useEffect } from 'react';
import { specialDaysAPI } from '../services/api';

const DAY_TYPES = [
  { value: 'officeclosed', label: 'Office Closed' },
  { value: 'governmentholiday', label: 'Government Holiday' },
  { value: 'specialevent', label: 'Special Event' },
];

export default function SpecialDayForm({ onChanged }) {
  const [date, setDate] = useState('');
  const [dayType, setDayType] = useState('officeclosed');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // List of existing special days (next 30 days)
  const [specialDays, setSpecialDays] = useState([]);
  const [listLoading, setListLoading] = useState(false);

  useEffect(() => {
    fetchSpecialDays();
  }, []);

  const fetchSpecialDays = async () => {
    setListLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const end = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0];
      const res = await specialDaysAPI.getRange(today, end);
      setSpecialDays(res.data.special_days || []);
    } catch {
      // silent
    } finally {
      setListLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!date) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await specialDaysAPI.create(date, dayType, note);
      setSuccess('Special day created.');
      setDate('');
      setNote('');
      fetchSpecialDays();
      onChanged?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create special day.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this special day?')) return;
    try {
      await specialDaysAPI.delete(id);
      setSpecialDays((prev) => prev.filter((d) => d.id !== id));
      setSuccess('Special day deleted.');
      onChanged?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete.');
    }
  };

  const typeLabel = (val) => DAY_TYPES.find((t) => t.value === val)?.label || val;

  return (
    <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700">
        <h2 className="font-bold text-lg flex items-center gap-2">
          <span className="material-icons-outlined text-primary">event_note</span>
          Special Days
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Mark dates as holidays or events. Office-closed and holiday dates block meal participation.
        </p>
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm">
            {success}
          </div>
        )}

        {/* Create Form */}
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 mb-6">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Type</label>
            <select
              value={dayType}
              onChange={(e) => setDayType(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary appearance-none"
            >
              {DAY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Note (optional)</label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Independence Day"
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Add'}
          </button>
        </form>

        {/* Existing Special Days */}
        {listLoading ? (
          <p className="text-xs text-slate-400">Loading...</p>
        ) : specialDays.length === 0 ? (
          <p className="text-xs text-slate-400">No special days in the next 30 days.</p>
        ) : (
          <div className="space-y-2">
            {specialDays.map((sd) => (
              <div key={sd.id} className="flex items-center justify-between py-2 px-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">{sd.date}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">
                    {typeLabel(sd.day_type)}
                  </span>
                  {sd.note && <span className="text-xs text-slate-400">{sd.note}</span>}
                </div>
                <button
                  onClick={() => handleDelete(sd.id)}
                  className="p-1 rounded text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  title="Delete"
                >
                  <span className="material-icons-outlined text-lg">delete_outline</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
