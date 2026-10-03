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