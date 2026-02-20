const TYPE_CONFIG = {
  officeclosed: {
    icon: 'domain_disabled',
    label: 'Office Closed',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-700 dark:text-red-300',
    iconColor: 'text-red-500',
  },
  governmentholiday: {
    icon: 'flag',
    label: 'Government Holiday',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    iconColor: 'text-amber-500',
  },
  specialevent: {
    icon: 'celebration',
    label: 'Special Event',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-700 dark:text-blue-300',
    iconColor: 'text-blue-500',
  },
};

export default function SpecialDayBanner({ specialDay }) {
  if (!specialDay) return null;

  const config = TYPE_CONFIG[specialDay.day_type] || TYPE_CONFIG.specialevent;
  const blocked = specialDay.day_type === 'officeclosed' || specialDay.day_type === 'governmentholiday';

  return (
    <div className={`mb-6 ${config.bg} border ${config.border} rounded-xl p-4 flex items-start gap-3`}>
      <span className={`material-icons-outlined ${config.iconColor} mt-0.5`}>{config.icon}</span>
      <div>
        <p className={`${config.text} text-sm font-semibold`}>{config.label}</p>
        {specialDay.note && (
          <p className={`${config.text} text-xs mt-0.5 opacity-80`}>{specialDay.note}</p>
        )}
        {blocked && (
          <p className={`${config.text} text-xs mt-1 opacity-70`}>
            Meal participation is disabled for this day.
          </p>
        )}
      </div>
    </div>
  );
}
