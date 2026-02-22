import { useState, useEffect } from "react";
import { workLocationsAPI } from "../services/api";

export default function WorkLocationSelector({
  date = null,
  onChange = null,
  disabled = false,
}) {
  const [location, setLocation] = useState("Office");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const targetDate = date || new Date().toISOString().slice(0, 10);

  useEffect(() => {
    const fetchLocation = async () => {
      try {
        const res = await workLocationsAPI.getMine(targetDate);
        if (res.data?.location) setLocation(res.data.location);
      } catch {
        setLocation("Office");
      } finally {
        setLoaded(true);
      }
    };
    fetchLocation();
  }, [targetDate]);

  const handleChange = async (newLocation) => {
    if (newLocation === location || saving || disabled) return;
    setSaving(true);
    setError(null);
    try {
      await workLocationsAPI.set(targetDate, newLocation);
      setLocation(newLocation);
      if (onChange) onChange(newLocation);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update work location");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm px-6 py-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Label side */}
        <div>
          <h3 className="font-semibold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <span className="material-icons-outlined text-base text-primary">location_on</span>
            Today's Work Location
          </h3>
          {!loaded ? (
            <p className="text-xs text-slate-400 mt-0.5">Loading…</p>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {location === "Office" ? "You're working from the office today" : "You're working from home today"}
            </p>
          )}
        </div>

        {/* Toggle buttons */}
        {loaded && (
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => handleChange("Office")}
              disabled={disabled || saving}
              className={[
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all",
                location === "Office"
                  ? "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-400"
                  : "bg-slate-50 dark:bg-slate-700 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-600 hover:border-emerald-300 hover:text-emerald-600",
                (disabled || saving) ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
              ].join(" ")}
            >
              <span className="material-icons-outlined text-base">apartment</span>
              Office
            </button>

            <button
              onClick={() => handleChange("WFH")}
              disabled={disabled || saving}
              className={[
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all",
                location === "WFH"
                  ? "bg-sky-50 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 border-sky-400"
                  : "bg-slate-50 dark:bg-slate-700 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-600 hover:border-sky-300 hover:text-sky-600",
                (disabled || saving) ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
              ].join(" ")}
            >
              <span className="material-icons-outlined text-base">home</span>
              WFH
            </button>

            {saving && (
              <span className="flex items-center text-xs text-slate-400 ml-1">
                <span className="material-icons-outlined text-base animate-spin mr-1">refresh</span>
                Saving…
              </span>
            )}
          </div>
        )}
      </div>

      {error && (
        <p className="mt-3 text-xs text-red-500 flex items-center gap-1">
          <span className="material-icons-outlined text-sm">error_outline</span>
          {error}
        </p>
      )}
    </div>
  );
}
