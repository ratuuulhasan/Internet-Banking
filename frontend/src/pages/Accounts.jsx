import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Row, Col, Table } from 'react-bootstrap';

export default function Accounts() {
  const [accounts, setAccounts] = useState([]);
  useEffect(() => {
    api.get('/accounts/').then((r) => setAccounts(r.data.results || r.data));
  }, []);

  return (
    <div className="container mt-4">
      <h3>My Accounts</h3>
      <Row className="mt-3">
        {accounts.map((a) => (
          <Col md={6} key={a.account_id}>
            <Card className="mb-3">
              <Card.Body>
                <Row>
                  <Col>
                    <h6 className="text-muted">{a.account_type}</h6>
                    <h5>{a.account_number}</h5>
                    <span className="badge bg-success">{a.status}</span>
                  </Col>
                  <Col className="text-end">
                    <small>Balance</small>
                    <h4>৳ {parseFloat(a.balance).toLocaleString()}</h4>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}