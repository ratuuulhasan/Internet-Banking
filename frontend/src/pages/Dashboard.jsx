import { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../api/axios';
import { Card, Row, Col, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    api.get('/accounts/').then((r) => setAccounts(r.data.results || r.data));
  }, []);

  const totalBalance = accounts.reduce((s, a) => s + parseFloat(a.balance), 0);

  return (
    <div className="container mt-4">
      <h3>Welcome, {user?.full_name} 👋</h3>
      <Row className="mt-4">
        <Col md={6}>
          <Card className="text-white bg-success mb-3">
            <Card.Body>
              <Card.Title>Total Balance</Card.Title>
              <h2>৳ {totalBalance.toLocaleString()}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card className="text-white bg-info mb-3">
            <Card.Body>
              <Card.Title>Quick Actions</Card.Title>
              <Link to="/transfer" className="btn btn-light me-2 mt-2">💸 Transfer</Link>
              <Link to="/transactions" className="btn btn-light mt-2">📜 History</Link>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <h5 className="mt-4">Your Accounts</h5>
      <Row>
        {accounts.map((a) => (
          <Col md={4} key={a.account_id}>
            <Card className="mb-3">
              <Card.Body>
                <Card.Title>{a.account_type}</Card.Title>
                <h6 className="text-muted">{a.account_number}</h6>
                <h4>৳ {parseFloat(a.balance).toLocaleString()}</h4>
                <span className="badge bg-success">{a.status}</span>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}