import { useState } from 'react';
import Navbar from '../components/Navbar';
import EmployeeDashboardContent from '../components/EmployeeDashboardContent';
import TeamManagementContent from '../components/TeamManagementContent';

export default function TeamLeadDashboard() {
  const [activeTab, setActiveTab] = useState('my-meals');

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen text-slate-900 dark:text-slate-100 flex flex-col">
      <Navbar />

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-16 z-40 bg-opacity-90 backdrop-blur-md shadow-sm">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('my-meals')}
              className={`py-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
                activeTab === 'my-meals'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:border-slate-300'
              }`}
            >
              <span className="material-icons-outlined text-xl">restaurant</span>
              My Meals
            </button>
            <button
              onClick={() => setActiveTab('team-management')}
              className={`py-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
                activeTab === 'team-management'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:border-slate-300'
              }`}
            >
              <span className="material-icons-outlined text-xl">diversity_3</span>
              Team Management
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1">
        {activeTab === 'my-meals' ? (
          <EmployeeDashboardContent />
        ) : (
          <TeamManagementContent />
        )}
      </div>
    </div>
  );
}
