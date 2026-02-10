import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EmployeeDashboard from './pages/EmployeeDashboard';
import AdminDashboard from './pages/AdminDashboard';
import TeamLeadDashboard from './pages/TeamLeadDashboard';
import Loading from './components/Loading';
import './App.css';

function RootRedirect() {
  const { user, loading, isAuthenticated } = useAuth();
  if (loading) return <Loading />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/admin" replace />;
  if (user.role === 'team_lead') return <Navigate to="/team-lead" replace />;
  return <Navigate to="/dashboard" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Employee dashboard */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute requiredRoles={['employee']}>
              <EmployeeDashboard />
            </PrivateRoute>
          }
        />

        {/* Team Lead dashboard */}
        <Route
          path="/team-lead"
          element={
            <PrivateRoute requiredRoles={['team_lead']}>
              <TeamLeadDashboard />
            </PrivateRoute>
          }
        />

        {/* Admin dashboard */}
        <Route
          path="/admin"
          element={
            <PrivateRoute requiredRoles={['admin']}>
              <AdminDashboard />
            </PrivateRoute>
          }
        />

        {/* Root redirect */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
