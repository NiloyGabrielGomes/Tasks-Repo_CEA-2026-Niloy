import { useState, useEffect } from 'react';
import { auditLogsAPI } from '../services/api';

export default function AuditLogViewer() {
    const [logs, setLogs] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Pagination & Filters
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);
    const [filters, setFilters] = useState({
        action: '',
        entityType: '',
        startDate: '',
        endDate: ''
    });

    const fetchLogs = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await auditLogsAPI.list({
                page,
                pageSize,
                action: filters.action || null,
                entityType: filters.entityType || null,
                startDate: filters.startDate || null,
                endDate: filters.endDate || null,
            });
            setLogs(res.data.audit_logs || []);
            setTotal(res.data.total || 0);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load audit logs.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, pageSize, filters]);

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
        setPage(1); // reset to first page on filter change
    };

    const handleClearFilters = () => {
        setFilters({ action: '', entityType: '', startDate: '', endDate: '' });
        setPage(1);
    };

    const totalPages = Math.ceil(total / pageSize);

    const renderChanges = (log) => {
        if (!log.field_changed) return <span className="text-slate-400 italic">No details</span>;
        return (
            <div className="text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">{log.field_changed}:</span>
                <div className="mt-1 flex items-center gap-1 flex-wrap">
                    {log.old_value && (
                        <span className="bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400 px-1 py-0.5 rounded line-through">
                            {log.old_value}
                        </span>
                    )}
                    {log.old_value && log.new_value && <span className="material-icons-outlined text-[10px] text-slate-400">arrow_forward</span>}
                    {log.new_value && (
                        <span className="bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 px-1 py-0.5 rounded">
                            {log.new_value}
                        </span>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex flex-col h-full">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 shrink-0">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="font-bold text-lg flex items-center gap-2 text-slate-900 dark:text-white">
                            <span className="material-icons-outlined text-primary">history</span>
                            Audit Logs
                        </h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                            View system-wide activity logs and changes.
                        </p>
                    </div>
                    <button
                        onClick={() => fetchLogs()}
                        className="p-2 text-slate-500 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                        title="Refresh Logs"
                    >
                        <span className="material-icons-outlined">refresh</span>
                    </button>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-end gap-3 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-100 dark:border-slate-700">
                    <div>
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Entity Type</label>
                        <select
                            name="entityType"
                            value={filters.entityType}
                            onChange={handleFilterChange}
                            className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary appearance-none min-w-30"
                        >
                            <option value="">All Entities</option>
                            <option value="meal_participation">Meal Participation</option>
                            <option value="work_location">Work Location</option>
                            <option value="policy">System Policy</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Action</label>
                        <select
                            name="action"
                            value={filters.action}
                            onChange={handleFilterChange}
                            className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary appearance-none min-w-30"
                        >
                            <option value="">All Actions</option>
                            <option value="create">Create</option>
                            <option value="update">Update</option>
                            <option value="delete">Delete</option>
                            <option value="batch_update">Batch Update</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Start Date</label>
                        <input
                            type="date"
                            name="startDate"
                            value={filters.startDate}
                            onChange={handleFilterChange}
                            className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">End Date</label>
                        <input
                            type="date"
                            name="endDate"
                            value={filters.endDate}
                            onChange={handleFilterChange}
                            className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white focus:ring-primary focus:border-primary"
                        />
                    </div>
                    <button
                        onClick={handleClearFilters}
                        className="px-3 py-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white text-sm font-medium transition-colors"
                    >
                        Clear Filters
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-0">
                {error ? (
                    <div className="p-6 text-center text-red-500">{error}</div>
                ) : loading ? (
                    <div className="p-12 text-center text-slate-400 flex flex-col items-center">
                        <span className="material-icons-outlined animate-spin text-4xl mb-2">loop</span>
                        <p>Loading audit logs...</p>
                    </div>
                ) : logs.length === 0 ? (
                    <div className="p-12 text-center text-slate-400 flex flex-col items-center">
                        <span className="material-icons-outlined text-4xl mb-2 opacity-50">history_toggle_off</span>
                        <p>No audit logs found matching your filters.</p>
                    </div>
                ) : (
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-50 dark:bg-slate-900/50 sticky top-0 z-10 shadow-sm">
                            <tr>
                                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Timestamp</th>
                                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actor</th>
                                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Target</th>
                                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Changes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {logs.map((log) => (
                                <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400">
                                        {new Date(log.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-slate-900 dark:text-white">
                                            {log.actor?.name || log.actor?.id || 'System'}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                                            {log.action} {log.entity_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-slate-900 dark:text-white">
                                            {log.target_user ? log.target_user.name : log.entity_id}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        {renderChanges(log)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination Footer */}
            {!loading && total > 0 && (
                <div className="px-6 py-3 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between shrink-0">
                    <div className="text-sm text-slate-500">
                        Showing <span className="font-medium">{(page - 1) * pageSize + 1}</span> to <span className="font-medium">{Math.min(page * pageSize, total)}</span> of <span className="font-medium">{total}</span> logs
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage(p => p + 1)}
                            disabled={page >= totalPages}
                            className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
