import { Link, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container">
        <Link className="navbar-brand" to="/">🏦 IBS</Link>
        <div className="navbar-nav me-auto">
          <Link className="nav-link" to="/">Dashboard</Link>
          <Link className="nav-link" to="/accounts">Accounts</Link>
          <Link className="nav-link" to="/transfer">Transfer</Link>
          <Link className="nav-link" to="/transactions">Transactions</Link>
        </div>
        <div className="d-flex align-items-center">
          <span className="text-white me-3">{user?.full_name}</span>
          <button className="btn btn-outline-light btn-sm" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}