import { useState, useEffect, useCallback } from 'react';
import { announcementsAPI } from '../services/api';

const STATUS_TABS = [
  { id: null,        label: 'All' },
  { id: 'draft',     label: 'Drafts' },
  { id: 'scheduled', label: 'Scheduled' },
  { id: 'sent',      label: 'Sent' },
];

const AUDIENCE_OPTIONS = [
  { value: 'all',        label: 'Everyone',    icon: 'groups' },
  { value: 'team_leads', label: 'Team Leads',  icon: 'supervisor_account' },
];

const STATUS_STYLE = {
  draft:     'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  scheduled: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  sent:      'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
};

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

// ── Create Form ───────────────────────────────────────────────────────────────

function CreateForm({ onCreated }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle]           = useState('');
  const [body, setBody]             = useState('');
  const [audience, setAudience]     = useState('all');
  const [scheduleMode, setScheduleMode] = useState(false);
  const [scheduledAt, setScheduledAt]   = useState('');
  const [saving, setSaving]         = useState(false);
  const [error, setError]           = useState('');

  const reset = () => {
    setTitle('');
    setBody('');
    setAudience('all');
    setScheduleMode(false);
    setScheduledAt('');
    setError('');
  };

  const handleSave = async () => {
    if (!title.trim() || !body.trim()) {
      setError('Title and body are required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await announcementsAPI.createDraft(
        title.trim(),
        body.trim(),
        audience,
        null,
      );
      reset();
      setOpen(false);
      onCreated();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save draft.');
    } finally {
      setSaving(false);
    }
  };

  const handleSchedule = async () => {
    if (!title.trim() || !body.trim()) {
      setError('Title and body are required.');
      return;
    }
    if (!scheduledAt) {
      setError('Please pick a date/time to schedule.');
      return;
    }
    if (new Date(scheduledAt) <= new Date()) {
      setError('Scheduled time must be in the future.');
      return;
    }
    setSaving(true);
    setError('');
    try {

      const draft = await announcementsAPI.createDraft(title.trim(), body.trim(), audience, null);
      await announcementsAPI.publish(draft.data.id, new Date(scheduledAt).toISOString());
      reset();
      setOpen(false);
      onCreated();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to schedule announcement.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border-b border-slate-100 dark:border-slate-700">
      {/* Toggle header */}
      <button
        onClick={() => { setOpen((v) => !v); if (open) reset(); }}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors text-left"
      >
        <span className="flex items-center gap-2 font-semibold text-sm text-slate-900 dark:text-white">
          <span className="material-icons-outlined text-primary text-base">add_circle_outline</span>
          New Announcement
        </span>
        <span className="material-icons-outlined text-slate-400 text-base">
          {open ? 'expand_less' : 'expand_more'}
        </span>
      </button>

      {open && (
        <div className="px-6 pb-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
              <span className="material-icons-outlined text-base">error_outline</span>
              {error}
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={255}
              placeholder="Enter announcement title…"
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white placeholder-slate-400"
            />
          </div>

          {/* Body */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
              Message <span className="text-red-400">*</span>
            </label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={4}
              placeholder="Write your announcement…"
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white placeholder-slate-400 resize-none"
            />
          </div>

          {/* Audience */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
              Audience
            </label>
            <div className="flex gap-2">
              {AUDIENCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setAudience(opt.value)}
                  className={[
                    'flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                    audience === opt.value
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-750',
                  ].join(' ')}
                >
                  <span className="material-icons-outlined text-base">{opt.icon}</span>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Schedule toggle */}
          <div>
            <label className="flex items-center gap-2 cursor-pointer w-fit">
              <input
                type="checkbox"
                checked={scheduleMode}
                onChange={(e) => setScheduleMode(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary"
              />
              <span className="text-sm text-slate-600 dark:text-slate-400">Schedule for later</span>
            </label>

            {scheduleMode && (
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                min={new Date(Date.now() + 60000).toISOString().slice(0, 16)}
                className="mt-2 px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary dark:text-white w-full sm:w-auto"
              />
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            {scheduleMode ? (
              <button
                onClick={handleSchedule}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
              >
                <span className="material-icons-outlined text-base">schedule_send</span>
                {saving ? 'Scheduling…' : 'Schedule'}
              </button>
            ) : (
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
              >
                <span className="material-icons-outlined text-base">save</span>
                {saving ? 'Saving…' : 'Save as Draft'}
              </button>
            )}
            <button
              onClick={() => { setOpen(false); reset(); }}
              className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Draft List ────────────────────────────────────────────────────────────────

function DraftList({ refreshTrigger }) {
  const [statusFilter, setStatusFilter] = useState(null);
  const [items, setItems]               = useState([]);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState('');
  const [publishing, setPublishing]     = useState(null); // id of item being published
  const [expandedId, setExpandedId]     = useState(null);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await announcementsAPI.list(statusFilter);
      setItems(res.data.announcements ?? []);
    } catch {
      setError('Failed to load announcements.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { fetchList(); }, [fetchList, refreshTrigger]);

  const handlePublish = async (id) => {
    setPublishing(id);
    try {
      await announcementsAPI.publish(id, null);
      fetchList();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to publish.');
    } finally {
      setPublishing(null);
    }
  };

  return (
    <div>
      {/* Status filter tabs */}
      <div className="flex gap-1 px-6 pt-4 border-b border-slate-100 dark:border-slate-700">
        {STATUS_TABS.map((t) => (
          <button
            key={String(t.id)}
            onClick={() => setStatusFilter(t.id)}
            className={[
              'flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t transition-colors',
              statusFilter === t.id
                ? 'text-primary border-b-2 border-primary -mb-px'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300',
            ].join(' ')}
          >
            {t.label}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={fetchList}
          disabled={loading}
          className="self-center mb-1 p-1.5 text-slate-400 hover:text-primary transition-colors rounded"
          title="Refresh"
        >
          <span className={`material-icons-outlined text-base ${loading ? 'animate-spin' : ''}`}>refresh</span>
        </button>
      </div>

      {/* List body */}
      {error && (
        <div className="m-4 text-sm text-red-500">{error}</div>
      )}

      {!loading && items.length === 0 && (
        <div className="py-12 text-center text-slate-400 text-sm">
          <span className="material-icons-outlined text-3xl block mb-2 opacity-40">campaign</span>
          No announcements found.
        </div>
      )}

      <ul className="divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <li key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors">
              {/* Row header */}
              <div className="flex items-start gap-3 px-6 py-4">
                {/* Expand body toggle */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  className="mt-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors shrink-0"
                >
                  <span className="material-icons-outlined text-base">
                    {isExpanded ? 'expand_less' : 'expand_more'}
                  </span>
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                      {item.title}
                    </span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full capitalize ${STATUS_STYLE[item.status] ?? ''}`}>
                      {item.status}
                    </span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-0.5">
                      <span className="material-icons-outlined text-[13px]">
                        {item.audience === 'all' ? 'groups' : 'supervisor_account'}
                      </span>
                      {item.audience === 'all' ? 'Everyone' : 'Team Leads'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                    <span>Created {formatDate(item.created_at)}</span>
                    {item.scheduled_at && (
                      <span className="text-amber-500">
                        Scheduled {formatDate(item.scheduled_at)}
                      </span>
                    )}
                    {item.published_at && (
                      <span className="text-emerald-500">
                        Sent {formatDate(item.published_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Publish button — only on draft/scheduled */}
                {(item.status === 'draft' || item.status === 'scheduled') && (
                  <button
                    onClick={() => handlePublish(item.id)}
                    disabled={publishing === item.id}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary/90 text-white text-xs font-medium rounded-lg disabled:opacity-50 transition-colors"
                  >
                    <span className="material-icons-outlined text-[14px]">send</span>
                    {publishing === item.id ? 'Sending…' : 'Publish Now'}
                  </button>
                )}
              </div>

              {/* Expanded body */}
              {isExpanded && (
                <div className="px-6 pb-4 ml-8">
                  <div className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    {item.body}
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────

export default function AnnouncementDraft() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  return (
    <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex items-center gap-2">
        <span className="material-icons-outlined text-primary">campaign</span>
        <h2 className="font-bold text-lg text-slate-900 dark:text-white">Announcements</h2>
      </div>

      <CreateForm onCreated={() => setRefreshTrigger((n) => n + 1)} />

      <DraftList refreshTrigger={refreshTrigger} />
    </section>
  );
}
