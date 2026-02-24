import { useState, useEffect } from 'react';
import { eventMealsAPI } from '../services/api';

const MEAL_TYPES = [
    { value: 'event_dinner', label: 'Event Dinner' },
    { value: 'lunch', label: 'Lunch Event' },
    { value: 'optional_dinner', label: 'Late Dinner' },
];

export default function EventMealForm({ onChanged }) {
    const [date, setDate] = useState('');
    const [mealType, setMealType] = useState('event_dinner');
    const [note, setNote] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [eventMeals, setEventMeals] = useState([]);
    const [listLoading, setListLoading] = useState(false);

    useEffect(() => {
        fetchEventMeals();
    }, []);

    const fetchEventMeals = async () => {
        setListLoading(true);
        try {
            const today = new Date().toISOString().split('T')[0];
            const res = await eventMealsAPI.list(today, null);
            setEventMeals(res.data.event_meals || []);
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
            await eventMealsAPI.create(date, mealType, note);
            setSuccess('Event meal created successfully.');
            setDate('');
            setNote('');
            fetchEventMeals();
            onChanged?.();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create event meal.');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this event meal?')) return;
        try {
            await eventMealsAPI.delete(id);
            setEventMeals((prev) => prev.filter((em) => em.id !== id));
            setSuccess('Event meal deleted.');
            onChanged?.();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to delete.');
        }
    };

    const typeLabel = (val) => MEAL_TYPES.find((t) => t.value === val)?.label || val;

    return (
        <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700">
                <h2 className="font-bold text-lg flex items-center gap-2 text-slate-900 dark:text-white">
                    <span className="material-icons-outlined text-primary">celebration</span>
                    Manage Event Meals
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Create special meals (like Team Building Dinners or PI Planning lunches) that employees can opt into.
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
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Meal Type</label>
                        <select
                            value={mealType}
                            onChange={(e) => setMealType(e.target.value)}
                            className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary appearance-none"
                        >
                            {MEAL_TYPES.map((t) => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex-1 min-w-35">
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Note / Description (Optional)</label>
                        <input
                            type="text"
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            placeholder="e.g. Q3 Townhall Dinner"
                            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50"
                    >
                        {saving ? 'Creating...' : 'Create Event'}
                    </button>
                </form>

                {/* Existing Event Meals */}
                {listLoading ? (
                    <p className="text-xs text-slate-400">Loading events...</p>
                ) : eventMeals.length === 0 ? (
                    <p className="text-xs text-slate-400">No upcoming event meals found.</p>
                ) : (
                    <div className="space-y-2">
                        {eventMeals.map((em) => (
                            <div key={em.id} className="flex items-center justify-between py-2 px-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <span className="text-sm font-medium text-slate-800 dark:text-white">{em.date}</span>
                                    <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">
                                        {typeLabel(em.meal_type)}
                                    </span>
                                    {em.note && <span className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">{em.note}</span>}
                                </div>
                                <button
                                    onClick={() => handleDelete(em.id)}
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
