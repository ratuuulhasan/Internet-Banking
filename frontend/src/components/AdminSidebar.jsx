import { NavLink } from 'react-router-dom';
import { Nav } from 'react-bootstrap';

export default function AdminSidebar() {
  return (
    <div className="bg-dark text-white p-3" style={{ minHeight: '90vh', width: 230 }}>
      <h5 className="text-center mb-4">👑 Admin Panel</h5>
      <Nav className="flex-column">
        <Nav.Link as={NavLink} to="/admin" end className="text-white">
          📊 Dashboard
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/users" className="text-white">
          👥 Users
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/kyc" className="text-white">
          📄 KYC Approval
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/fraud" className="text-white">
          🚨 Fraud Alerts
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/loans" className="text-white">
          💰 Loans
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/complaints" className="text-white">
          🎫 Complaints
        </Nav.Link>
        <Nav.Link as={NavLink} to="/admin/ml" className="text-white">
          🧠 ML Pipeline
        </Nav.Link>
      </Nav>
    </div>
  );
}