import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Row, Col, Button, Badge, Form } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function Cards() {
  const [cards, setCards] = useState([]);

  const load = () => api.get('/cards/').then(r => setCards(r.data.results || r.data));
    useEffect(() => { load(); }, []);

  const toggle = async (c) => {
    const action = c.status === 'ACTIVE' ? 'block' : 'unblock';
    await api.post(`/cards/${c.card_id}/${action}/`);
    toast.success(`Card ${action}ed`);
    load();
  };

  const setLimit = async (c) => {
    const val = prompt('New daily limit (BDT):', c.daily_limit);
    if (!val) return;
    await api.post(`/cards/${c.card_id}/set_limit/`, { daily_limit: val });
    toast.success('Limit updated');
    load();
  };

  return (
    <div className="container mt-4">
      <h3>My Cards</h3>
      <Row className="mt-3">
        {cards.map(c => (
          <Col md={4} key={c.card_id}>
            <Card className="mb-3 text-white bg-dark">
              <Card.Body>
                <h6>{c.card_type} CARD</h6>
                <h5>{c.masked_number}</h5>
                <p>Expires: {c.expiry_date}</p>
                <p>Daily Limit: ৳{c.daily_limit}</p>
                <Badge bg={c.status === 'ACTIVE' ? 'success' : 'danger'}>{c.status}</Badge>
                <div className="mt-3">
                  <Button size="sm" variant="warning"
                    onClick={() => toggle(c)}>
                    {c.status === 'ACTIVE' ? 'Block' : 'Unblock'}
                  </Button>{' '}
                  <Button size="sm" variant="info" onClick={() => setLimit(c)}>
                    Set Limit
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}