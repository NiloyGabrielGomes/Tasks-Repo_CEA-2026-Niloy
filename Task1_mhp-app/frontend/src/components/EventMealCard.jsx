import { useState } from 'react';

const MEAL_ICONS = {
    lunch: 'lunch_dining',
    event_dinner: 'celebration',
    optional_dinner: 'nightlight_round',
};

const MEAL_LABELS = {
    lunch: 'Event Lunch',
    event_dinner: 'Event Dinner',
    optional_dinner: 'Late Dinner Event',
};

export default function EventMealCard({ eventMeal, isParticipating, onToggle, disabled }) {
    const [toggling, setToggling] = useState(false);

    const mealType = eventMeal.meal_type;

    const handleToggle = async () => {
        if (disabled || toggling) return;
        setToggling(true);
        try {
            await onToggle(eventMeal, !isParticipating);
        } finally {
            setToggling(false);
        }
    };

    return (
        <div className={`bg-white dark:bg-slate-900/50 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-all ${disabled ? 'opacity-60' : 'hover:shadow-md hover:border-primary/30'} relative overflow-hidden`}>
            {/* Visual flair for event meal */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-bl-full -mr-4 -mt-4 z-0 pointer-events-none"></div>

            <div className="relative z-10">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary mb-4 ring-2 ring-primary/20">
                    <span className="material-icons-outlined">
                        {MEAL_ICONS[mealType] || 'celebration'}
                    </span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                        {MEAL_LABELS[mealType] || mealType}
                    </h3>
                    <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider dark:bg-amber-900 border border-amber-200 dark:border-amber-700 dark:text-amber-200">
                        Special Event
                    </span>
                </div>

                {eventMeal.note && (
                    <p className="text-sm text-slate-600 dark:text-slate-300 font-medium mb-1 line-clamp-2">
                        "{eventMeal.note}"
                    </p>
                )}

                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 flex items-center gap-1">
                    <span className="material-icons-outlined text-[14px]">event</span>
                    {eventMeal.date}
                </p>
            </div>

            <div className="relative z-10 flex items-center justify-between mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <span className="text-xs font-medium text-slate-400">
                    {disabled ? (
                        <span className="flex items-center gap-1">
                            <span className="material-icons-outlined text-xs">lock</span>
                            Locked
                        </span>
                    ) : isParticipating ? 'Opting In' : 'Opted Out'}
                </span>
                <div
                    className={`relative inline-block w-11 h-6 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                    onClick={handleToggle}
                >
                    <input
                        type="checkbox"
                        checked={isParticipating}
                        readOnly
                        disabled={disabled}
                        className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-transparent appearance-none cursor-pointer"
                    />
                    <label
                        className={`toggle-label block overflow-hidden h-6 rounded-full transition-colors duration-200 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'
                            } ${isParticipating ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'
                            } ${toggling ? 'opacity-50' : ''}`}
                    >
                        <span
                            className={`toggle-dot block w-4 h-4 mt-1 ml-1 rounded-full bg-white shadow transform transition-transform duration-200 ${isParticipating ? 'translate-x-5' : ''
                                }`}
                        ></span>
                    </label>
                </div>
            </div>
        </div>
    );
}
