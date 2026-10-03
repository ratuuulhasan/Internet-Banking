import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, ListGroup, Badge, Button } from 'react-bootstrap';

export default function Notifications() {
  const [list, setList] = useState([]);

  const load = () => api.get('/notifications/').then(r => setList(r.data.results || r.data));
  useEffect(() => { load(); }, []);


  const markRead = async (id) => {
    await api.post(`/notifications/${id}/mark_read/`);
    load();
  };

  const markAll = async () => {
    await api.post('/notifications/mark_all_read/');
    load();
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between">
        <h3>Notifications</h3>
        <Button size="sm" onClick={markAll}>Mark all read</Button>
      </div>
      <Card className="mt-3">
        <ListGroup variant="flush">
          {list.map(n => (
            <ListGroup.Item key={n.notification_id}
              className={n.is_read ? '' : 'bg-light'}>
              <div className="d-flex justify-content-between">
                <div>
                  <strong>{n.title}</strong>
                  <p className="mb-0 small">{n.message}</p>
                  <small className="text-muted">
                    {new Date(n.created_at).toLocaleString()}
                  </small>
                </div>
                <div>
                  {!n.is_read &&
                    <Button size="sm" variant="outline-primary"
                      onClick={() => markRead(n.notification_id)}>Mark read</Button>}
                </div>
              </div>
            </ListGroup.Item>
          ))}
        </ListGroup>
      </Card>
    </div>
  );
}