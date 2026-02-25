import { useState, useEffect, useCallback } from 'react';
import { wfhPeriodsAPI, usersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const TEAMS = [
  'Engineering',
  'Marketing',
  'Human Resources',
  'Sales & Operations',
  'Product & Design',
  'Operations',
];

function periodStatus(start, end) {
  const today = new Date().toISOString().split('T')[0];
  if (end < today) return 'past';
  if (start > today) return 'upcoming';
  return 'current';
}

const STATUS_STYLE = {
  current:  { label: 'Current',  cls: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' },
  upcoming: { label: 'Upcoming', cls: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300' },
  past:     { label: 'Past',     cls: 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400' },
};

function daysBetween(start, end) {
  const ms = new Date(end) - new Date(start);
  return Math.round(ms / 86400000) + 1;
}

function fmt(iso) {
  if (!iso) return '';
  return new Date(iso + 'T00:00:00').toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

// ── Period Form Modal ─────────────────────────────────────────────────────────

function PeriodModal({ mode, initial, currentUser, teamUsers, onClose, onSaved }) {
  const isAdmin     = currentUser.role === 'admin';
  const isTeamLead  = currentUser.role === 'team_lead';
  const canPickUser = isAdmin || isTeamLead;

  const [employeeId, setEmployeeId]   = useState(initial?.employee_id ?? currentUser.id);
  const [startDate,  setStartDate]    = useState(initial?.start_date  ?? '');
  const [endDate,    setEndDate]      = useState(initial?.end_date    ?? '');
  const [reason,     setReason]       = useState(initial?.reason      ?? '');
  const [saving,     setSaving]       = useState(false);
  const [error,      setError]        = useState('');

  const validate = () => {
    if (!startDate || !endDate) return 'Start and end dates are required.';
    if (endDate < startDate)    return 'End date must be on or after start date.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }
    setSaving(true);
    setError('');
    try {
      if (mode === 'create') {
        await wfhPeriodsAPI.create({ employeeId, startDate, endDate, reason: reason || null });
      } else {
        await wfhPeriodsAPI.update(initial.id, { startDate, endDate, reason: reason || null });
      }
      onSaved();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save period.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md border border-slate-200 dark:border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700">
          <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
            <span className="material-icons-outlined text-primary text-xl">
              {mode === 'create' ? 'add_circle_outline' : 'edit'}
            </span>
            {mode === 'create' ? 'Schedule WFH Period' : 'Edit WFH Period'}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span className="material-icons-outlined">close</span>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
              <span className="material-icons-outlined text-base">error_outline</span>
              {error}
            </div>
          )}

          {/* Employee picker — admin / TL only, hidden on edit (employee can't change) */}
          {canPickUser && mode === 'create' && (
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                Employee <span className="text-red-400">*</span>
              </label>
              <select
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white"
              >
                {teamUsers.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}{u.team ? ` — ${u.team}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Date range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                Start Date <span className="text-red-400">*</span>
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                End Date <span className="text-red-400">*</span>
              </label>
              <input
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white"
              />
            </div>
          </div>

          {/* Duration preview */}
          {startDate && endDate && endDate >= startDate && (
            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <span className="material-icons-outlined text-[14px]">calendar_today</span>
              {daysBetween(startDate, endDate)} day{daysBetween(startDate, endDate) !== 1 ? 's' : ''}
              &nbsp;({fmt(startDate)} – {fmt(endDate)})
            </p>
          )}

          {/* Reason */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
              Reason <span className="text-slate-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={500}
              placeholder="e.g. Personal appointment, internet maintenance…"
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white placeholder-slate-400"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 bg-primary hover:bg-primary/90 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
            >
              <span className="material-icons-outlined text-base">save</span>
              {saving ? 'Saving…' : mode === 'create' ? 'Schedule' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function WFHPeriodManager() {
  const { user } = useAuth();
  const role = user?.role ?? 'employee';
  const isAdmin    = role === 'admin';
  const isTeamLead = role === 'team_lead';
  const isElevated = isAdmin || isTeamLead;

  // Filter state
  const [filterTeam,      setFilterTeam]      = useState(isTeamLead ? user?.team : '');
  const [filterEmployeeId, setFilterEmployeeId] = useState('');
  const [filterStart,     setFilterStart]     = useState('');
  const [filterEnd,       setFilterEnd]       = useState('');

  // Data
  const [periods,   setPeriods]   = useState([]);
  const [total,     setTotal]     = useState(0);
  const [page,      setPage]      = useState(1);
  const PAGE_SIZE = 20;

  const [teamUsers, setTeamUsers] = useState([]);   // for employee picker
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState('');

  // Modal
  const [modal,      setModal]      = useState(null); // { mode: 'create'|'edit', initial?: period }
  const [deleteId,   setDeleteId]   = useState(null); // id being confirmed for delete
  const [deleting,   setDeleting]   = useState(false);

  // ── Fetch periods ──────────────────────────────────────────────

  const fetchPeriods = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await wfhPeriodsAPI.list({
        employeeId: filterEmployeeId || null,
        team: filterTeam || null,
        startDate: filterStart || null,
        endDate: filterEnd || null,
        page,
        pageSize: PAGE_SIZE,
      });
      setPeriods(res.data.periods ?? []);
      setTotal(res.data.total ?? 0);
    } catch {
      setError('Failed to load WFH periods.');
    } finally {
      setLoading(false);
    }
  }, [filterEmployeeId, filterTeam, filterStart, filterEnd, page]);

  useEffect(() => { fetchPeriods(); }, [fetchPeriods]);

  // ── Fetch team users for employee picker ───────────────────────

  useEffect(() => {
    if (!isElevated) return;
    const fetch = async () => {
      try {
        const res = isAdmin
          ? await usersAPI.getAllUsers()
          : await usersAPI.getTeamUsers();
        const list = res.data.users ?? res.data ?? [];
        setTeamUsers(list.filter((u) => u.is_active));
      } catch { /* non-critical */ }
    };
    fetch();
  }, [isAdmin, isTeamLead, isElevated]);

  // ── Delete ─────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await wfhPeriodsAPI.delete(deleteId);
      setDeleteId(null);
      fetchPeriods();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete period.');
      setDeleteId(null);
    } finally {
      setDeleting(false);
    }
  };

  // ── Helpers ────────────────────────────────────────────────────

  const applyFilters = () => { setPage(1); fetchPeriods(); };
  const clearFilters = () => {
    setFilterTeam(isTeamLead ? user?.team : '');
    setFilterEmployeeId('');
    setFilterStart('');
    setFilterEnd('');
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // ── Render ─────────────────────────────────────────────────────

  return (
    <>
      {/* Modal */}
      {modal && (
        <PeriodModal
          mode={modal.mode}
          initial={modal.initial}
          currentUser={user}
          teamUsers={teamUsers}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); fetchPeriods(); }}
        />
      )}

      {/* Delete confirmation overlay */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm border border-slate-200 dark:border-slate-700 p-6 text-center">
            <span className="material-icons-outlined text-red-400 text-4xl mb-3 block">delete_forever</span>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-1">Delete WFH Period?</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
              This cannot be undone. The period will be permanently removed.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex items-center gap-2 px-5 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
              >
                <span className="material-icons-outlined text-base">delete</span>
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
              <button
                onClick={() => setDeleteId(null)}
                className="px-5 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white border border-slate-200 dark:border-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        {/* Section header */}
        <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="material-icons-outlined text-primary">home_work</span>
            <h2 className="font-bold text-lg text-slate-900 dark:text-white">WFH Periods</h2>
            {total > 0 && (
              <span className="text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-full">
                {total}
              </span>
            )}
          </div>
          <button
            onClick={() => setModal({ mode: 'create' })}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <span className="material-icons-outlined text-base">add</span>
            Schedule Period
          </button>
        </div>

        {/* Filter bar — admin / TL only */}
        {isElevated && (
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/30">
            <div className="flex flex-wrap gap-3 items-end">
              {/* Employee search */}
              <div className="flex-1 min-w-45">
                <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Employee
                </label>
                <select
                  value={filterEmployeeId}
                  onChange={(e) => setFilterEmployeeId(e.target.value)}
                  className="w-full px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 dark:text-white"
                >
                  <option value="">All employees</option>
                  {teamUsers.map((u) => (
                    <option key={u.id} value={u.id}>{u.name}</option>
                  ))}
                </select>
              </div>

              {/* Team filter — admin only */}
              {isAdmin && (
                <div className="flex-1 min-w-37.5">
                  <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Team
                  </label>
                  <select
                    value={filterTeam}
                    onChange={(e) => setFilterTeam(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 dark:text-white"
                  >
                    <option value="">All teams</option>
                    {TEAMS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              )}

              {/* Date range */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  From
                </label>
                <input
                  type="date"
                  value={filterStart}
                  onChange={(e) => setFilterStart(e.target.value)}
                  className="px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  To
                </label>
                <input
                  type="date"
                  value={filterEnd}
                  min={filterStart || undefined}
                  onChange={(e) => setFilterEnd(e.target.value)}
                  className="px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 dark:text-white"
                />
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={applyFilters}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary/90 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <span className="material-icons-outlined text-base">search</span>
                  Filter
                </button>
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-lg text-sm transition-colors"
                >
                  <span className="material-icons-outlined text-base">clear</span>
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mx-6 mt-4 flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
            <span className="material-icons-outlined text-base">error_outline</span>
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-12 text-slate-400">
            <span className="material-icons-outlined animate-spin mr-2">refresh</span>
            Loading…
          </div>
        )}

        {/* Empty state */}
        {!loading && periods.length === 0 && (
          <div className="py-14 text-center text-slate-400">
            <span className="material-icons-outlined text-4xl block mb-2 opacity-40">home_work</span>
            <p className="text-sm">No WFH periods found.</p>
            <button
              onClick={() => setModal({ mode: 'create' })}
              className="mt-3 text-sm text-primary underline underline-offset-2 hover:opacity-80"
            >
              Schedule a period
            </button>
          </div>
        )}

        {/* Table */}
        {!loading && periods.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider border-b border-slate-100 dark:border-slate-700">
                <tr>
                  {isElevated && <th className="px-6 py-3 font-semibold">Employee</th>}
                  <th className="px-6 py-3 font-semibold">Period</th>
                  <th className="px-6 py-3 font-semibold">Duration</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold">Reason</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {periods.map((p) => {
                  const st = periodStatus(p.start_date, p.end_date);
                  const stStyle = STATUS_STYLE[st];
                  const days = daysBetween(p.start_date, p.end_date);
                  return (
                    <tr key={p.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                      {isElevated && (
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                              {(p.employee_name || '?').split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium text-slate-800 dark:text-slate-200 truncate">
                                {p.employee_name ?? p.employee_id}
                              </p>
                              {p.employee_team && (
                                <p className="text-[11px] text-slate-400 truncate">{p.employee_team}</p>
                              )}
                            </div>
                          </div>
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-slate-800 dark:text-slate-200">
                          {fmt(p.start_date)}
                        </span>
                        <span className="text-slate-400 mx-1.5">→</span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">
                          {fmt(p.end_date)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-slate-600 dark:text-slate-400">
                          {days} day{days !== 1 ? 's' : ''}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${stStyle.cls}`}>
                          {stStyle.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 max-w-50">
                        <span className="text-slate-500 dark:text-slate-400 truncate block" title={p.reason}>
                          {p.reason || <span className="text-slate-300 dark:text-slate-600">—</span>}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {/* Edit — only shown for non-past periods or admin */}
                          {(st !== 'past' || isAdmin) && (
                            <button
                              onClick={() => setModal({ mode: 'edit', initial: p })}
                              className="p-1.5 text-slate-400 hover:text-primary rounded-lg hover:bg-primary/10 transition-colors"
                              title="Edit"
                            >
                              <span className="material-icons-outlined text-base">edit</span>
                            </button>
                          )}
                          <button
                            onClick={() => setDeleteId(p.id)}
                            className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            title="Delete"
                          >
                            <span className="material-icons-outlined text-base">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 dark:border-slate-700">
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages} &bull; {total} total
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-3 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <span className="material-icons-outlined text-base">chevron_left</span>
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Next
                <span className="material-icons-outlined text-base">chevron_right</span>
              </button>
            </div>
          </div>
        )}
      </section>
    </>
  );
}
