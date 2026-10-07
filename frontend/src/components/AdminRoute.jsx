import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

export default function AdminRoute({ children }) {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="text-center mt-5">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (!['ADMIN', 'SYS_ADMIN'].includes(user.role)) {
    return <div className="container mt-5"><h3>⛔ Access Denied</h3></div>;
  }
  return children;
}