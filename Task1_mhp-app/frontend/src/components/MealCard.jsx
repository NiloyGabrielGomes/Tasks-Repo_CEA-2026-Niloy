import { useState } from 'react';

const MEAL_ICONS = {
  lunch: 'lunch_dining',
  snacks: 'cookie',
  iftar: 'brightness_3',
  event_dinner: 'celebration',
  optional_dinner: 'nightlight_round',
};

const MEAL_LABELS = {
  lunch: 'Lunch',
  snacks: 'Snacks',
  iftar: 'Iftar',
  event_dinner: 'Event Dinner',
  optional_dinner: 'Late Dinner',
};

const MEAL_TIMES = {
  lunch: '12:00 PM — 1:30 PM',
  snacks: '4:00 PM',
  iftar: '6:45 PM (Sunset)',
  event_dinner: '7:30 PM — Team Social',
  optional_dinner: '8:30 PM — Late Stay',
};

export default function MealCard({ meal, onToggle, disabled }) {
  const [toggling, setToggling] = useState(false);
  const mealType = meal.meal_type;
  const isOn = meal.is_participating;

  const handleToggle = async () => {
    if (disabled || toggling) return;
    setToggling(true);
    try {
      await onToggle(meal, !isOn);
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900/50 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-all hover:shadow-md hover:border-primary/30">
      <div>
        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary mb-4">
          <span className="material-icons-outlined">
            {MEAL_ICONS[mealType] || 'restaurant'}
          </span>
        </div>
        <h3 className="text-lg font-bold mb-1 text-slate-900 dark:text-white">
          {MEAL_LABELS[mealType] || mealType}
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
          {MEAL_TIMES[mealType] || ''}
        </p>
      </div>
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
        <span className="text-xs font-medium text-slate-400">
          {isOn ? 'Opting In' : 'Opted Out'}
        </span>
        <div
          className="relative inline-block w-11 h-6 cursor-pointer"
          onClick={handleToggle}
        >
          <input
            type="checkbox"
            checked={isOn}
            readOnly
            className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-transparent appearance-none cursor-pointer hidden"
          />
          <label
            className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer transition-colors duration-200 ${
              isOn ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'
            } ${toggling ? 'opacity-50' : ''}`}
          >
            <span
              className={`toggle-dot block w-4 h-4 mt-1 ml-1 rounded-full bg-white shadow transform transition-transform duration-200 ${
                isOn ? 'translate-x-5' : ''
              }`}
            ></span>
          </label>
        </div>
      </div>
    </div>
  );
}
