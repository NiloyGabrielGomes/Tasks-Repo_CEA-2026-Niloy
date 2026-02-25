import Navbar from '../components/Navbar';
import EmployeeDashboardContent from '../components/EmployeeDashboardContent';

export default function EmployeeDashboard() {
  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen text-slate-900 dark:text-slate-100">
      <Navbar />
      <EmployeeDashboardContent />
    </div>
  );
}
