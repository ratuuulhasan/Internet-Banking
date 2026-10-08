import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { useContext } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Transfer from './pages/Transfer';
import Accounts from './pages/Accounts';
import Transactions from './pages/Transactions';
import KYC from './pages/KYC';
import Bills from './pages/Bills';
import Cards from './pages/Cards';
import Loans from './pages/Loans';
import Notifications from './pages/Notifications';
import Complaints from './pages/Complaints';
import Navbar from './components/Navbar';

// Admin
import AdminRoute from './components/AdminRoute';
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminUsers from './pages/admin/Users';
import AdminKYC from './pages/admin/KYCApproval';
import AdminFraud from './pages/admin/FraudAlerts';
import AdminLoans from './pages/admin/Loans';
import AdminComplaints from './pages/admin/Complaints';
import MLPipeline from './pages/admin/MLPipeline';


const Protected = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="text-center mt-5">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
};

function AppRoutes() {
  const { user } = useContext(AuthContext);
  return (
    <>
      {user && <Navbar />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route path="/accounts" element={<Protected><Accounts /></Protected>} />
        <Route path="/transfer" element={<Protected><Transfer /></Protected>} />
        <Route path="/transactions" element={<Protected><Transactions /></Protected>} />
        <Route path="/kyc" element={<Protected><KYC /></Protected>} />
        <Route path="/bills" element={<Protected><Bills /></Protected>} />
        <Route path="/cards" element={<Protected><Cards /></Protected>} />
        <Route path="/loans" element={<Protected><Loans /></Protected>} />
        <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
        <Route path="/complaints" element={<Protected><Complaints /></Protected>} />

        {/* ADMIN ROUTES */}
        <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="kyc" element={<AdminKYC />} />
          <Route path="fraud" element={<AdminFraud />} />
          <Route path="loans" element={<AdminLoans />} />
          <Route path="complaints" element={<AdminComplaints />} />
          <Route path="ml" element={<MLPipeline />} />
        </Route>
      </Routes>
      <ToastContainer position="top-right" />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
