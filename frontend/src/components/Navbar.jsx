import { Link, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Navbar as BSNavbar, Nav, Container } from 'react-bootstrap';

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  return (
    <BSNavbar bg="primary" variant="dark" expand="lg">
      <Container>
        <BSNavbar.Brand as={Link} to="/">🏦 IBS</BSNavbar.Brand>
        <BSNavbar.Toggle />
        <BSNavbar.Collapse>
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Dashboard</Nav.Link>
            <Nav.Link as={Link} to="/accounts">Accounts</Nav.Link>
            <Nav.Link as={Link} to="/transfer">Transfer</Nav.Link>
            <Nav.Link as={Link} to="/transactions">Transactions</Nav.Link>
            <Nav.Link as={Link} to="/bills">Bills</Nav.Link>
            <Nav.Link as={Link} to="/cards">Cards</Nav.Link>
            <Nav.Link as={Link} to="/loans">Loans</Nav.Link>
            <Nav.Link as={Link} to="/kyc">KYC</Nav.Link>
            <Nav.Link as={Link} to="/complaints">Support</Nav.Link>
            <Nav.Link as={Link} to="/notifications">🔔</Nav.Link>
          </Nav>
          <Nav>
            <span className="navbar-text text-white me-3">{user?.full_name}</span>
            <button className="btn btn-outline-light btn-sm" onClick={logout}>Logout</button>
          </Nav>
        </BSNavbar.Collapse>
      </Container>
    </BSNavbar>
  );
}