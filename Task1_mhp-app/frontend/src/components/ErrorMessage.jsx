export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="mb-6 flex items-center p-3.5 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
      <span className="material-symbols-outlined mr-2 text-lg">error</span>
      <span className="font-medium flex-1">{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-2 text-red-400 hover:text-red-600 transition-colors"
        >
          <span className="material-icons-outlined text-lg">close</span>
        </button>
      )}
    </div>
  );
}
