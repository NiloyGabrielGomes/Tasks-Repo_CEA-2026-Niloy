import { useState, useEffect } from 'react';
import { announcementsAPI } from '../services/api';

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Displays published announcements visible to the current user.
 * Auto-fetches on mount. Individual announcements can be dismissed (client-side only).
 */
export default function AnnouncementsBanner() {
  const [announcements, setAnnouncements] = useState([]);
  const [dismissed, setDismissed] = useState(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await announcementsAPI.getPublished();
        if (!cancelled) setAnnouncements(res.data.announcements ?? []);
      } catch {
        // silently ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const visible = announcements.filter((a) => !dismissed.has(a.id));

  if (loading || visible.length === 0) return null;

  return (
    <div className="space-y-3 mb-6">
      {visible.map((ann) => (
        <div
          key={ann.id}
          className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700 rounded-xl p-4 relative"
        >
          {/* Dismiss button */}
          <button
            onClick={() => setDismissed((prev) => new Set(prev).add(ann.id))}
            className="absolute top-3 right-3 text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-200 transition-colors"
            title="Dismiss"
          >
            <span className="material-icons-outlined text-base">close</span>
          </button>

          <div className="flex items-start gap-3 pr-6">
            <span className="material-icons-outlined text-indigo-500 mt-0.5">campaign</span>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-indigo-900 dark:text-indigo-100 mb-1">
                {ann.title}
              </h3>
              <p className="text-sm text-indigo-800 dark:text-indigo-200 whitespace-pre-wrap">
                {ann.body}
              </p>
              <p className="text-[11px] text-indigo-400 mt-2">
                Published {formatDate(ann.published_at)}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
