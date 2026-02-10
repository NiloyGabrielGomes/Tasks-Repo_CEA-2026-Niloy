const MEAL_LABELS = {
  lunch: 'Lunch',
  snacks: 'Snacks',
  iftar: 'Iftar',
  event_dinner: 'Event Dinner',
  optional_dinner: 'Late Dinner',
};

export default function HeadcountTable({ headcount, totalUsers }) {
  if (!headcount) return null;

  const entries = Object.entries(headcount);

  return (
    <section className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
        <h2 className="font-bold text-lg text-slate-900 dark:text-white">
          Meal Headcount Summary
        </h2>
      </div>
      <div className="p-6 space-y-6">
        {entries.map(([mealType, count]) => {
          const max = totalUsers || 1;
          const pct = Math.round((count / max) * 100);
          return (
            <div key={mealType}>
              <div className="flex justify-between items-end mb-2">
                <div>
                  <h4 className="font-semibold text-sm text-slate-900 dark:text-white">
                    {MEAL_LABELS[mealType] || mealType}
                  </h4>
                </div>
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
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
