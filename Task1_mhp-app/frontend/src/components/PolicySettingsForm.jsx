import { useState, useEffect } from 'react';
import { policyAPI } from '../services/api';

export default function PolicySettingsForm() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Form fields
    const [cutoffTime, setCutoffTime] = useState('');
    const [forwardPlanningDays, setForwardPlanningDays] = useState('');
    const [wfhMonthlyAllowance, setWfhMonthlyAllowance] = useState('');

    const fetchPolicy = async () => {
        setLoading(true);
        try {
            const res = await policyAPI.get();
            const currentConfig = res.data;
            setConfig(currentConfig);

            // Initialize form fields
            setCutoffTime(currentConfig.cutoff_time);
            setForwardPlanningDays(currentConfig.forward_planning_days);
            setWfhMonthlyAllowance(currentConfig.wfh_monthly_allowance);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load policy configuration.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPolicy();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        setSuccess('');

        try {
            await policyAPI.update({
                cutoffTime,
                forwardPlanningDays: parseInt(forwardPlanningDays, 10),
                wfhMonthlyAllowance: parseInt(wfhMonthlyAllowance, 10)
            });
            setSuccess('Policy configuration updated successfully.');
            fetchPolicy(); // Refresh to ensure we have the latest server state
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update policy configuration.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 text-center text-slate-400">
                <span className="material-icons-outlined animate-spin text-2xl mb-2">settings</span>
                <p>Loading policies...</p>
            </div>
        );
    }

    return (
        <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700">
                <h2 className="font-bold text-lg flex items-center gap-2 text-slate-900 dark:text-white">
                    <span className="material-icons-outlined text-primary">gavel</span>
                    System Policies
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Configure global rules and limits for all users interacting with the system.
                </p>
            </div>

            <div className="p-6">
                {error && (
                    <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm flex items-start gap-2">
                        <span className="material-icons-outlined text-base mt-0.5">error_outline</span>
                        {error}
                    </div>
                )}
                {success && (
                    <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm flex items-start gap-2">
                        <span className="material-icons-outlined text-base mt-0.5">check_circle</span>
                        {success}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">

                    <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-1">
                                    Daily Cutoff Time
                                </label>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    After this time, employees cannot change their meal participation for today or tomorrow. Format: HH:MM (24-hour).
                                </p>
                            </div>
                            <div className="shrink-0 w-32">
                                <input
                                    type="time"
                                    value={cutoffTime}
                                    onChange={(e) => setCutoffTime(e.target.value)}
                                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary shadow-sm"
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-1">
                                    Forward Planning Window (Days)
                                </label>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    How many days in advance employees can see and modify their meal participation. Typical value is 5 to 7.
                                </p>
                            </div>
                            <div className="shrink-0 w-32">
                                <input
                                    type="number"
                                    min="1"
                                    max="30"
                                    value={forwardPlanningDays}
                                    onChange={(e) => setForwardPlanningDays(e.target.value)}
                                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary shadow-sm"
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-1">
                                    Monthly WFH Allowance
                                </label>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    The maximum number of allowed Work From Home (WFH) days per calendar month per employee.
                                </p>
                            </div>
                            <div className="shrink-0 w-32">
                                <input
                                    type="number"
                                    min="0"
                                    max="31"
                                    value={wfhMonthlyAllowance}
                                    onChange={(e) => setWfhMonthlyAllowance(e.target.value)}
                                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary shadow-sm"
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end pt-4">
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50"
                        >
                            {saving ? (
                                <>
                                    <span className="material-icons-outlined animate-spin text-sm">refresh</span>
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <span className="material-icons-outlined text-sm">save</span>
                                    Save Policy
                                </>
                            )}
                        </button>
                    </div>

                </form>
            </div>
        </section>
    );
}
