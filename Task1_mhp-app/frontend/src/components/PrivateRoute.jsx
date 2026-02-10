import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Loading from './Loading';

export default function PrivateRoute({ children, requiredRoles }) {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) return <Loading />;

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (requiredRoles && !requiredRoles.includes(user.role)) {
    // Redirect to the correct dashboard for the user's role
    if (user.role === 'employee') return <Navigate to="/dashboard" replace />;
    if (user.role === 'team_lead') return <Navigate to="/team-lead" replace />;
    return <Navigate to="/admin" replace />;
  }

  return children;
}
