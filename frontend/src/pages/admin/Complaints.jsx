import { useEffect, useState } from 'react';
import { Card, Table, Badge, Button, Modal, Form, Spinner } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';

export default function AdminComplaints() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);
  const [current, setCurrent] = useState(null);
  const [form, setForm] = useState({
    status: '', priority: '', resolution_note: '', assigned_to: ''
  });

  const load = () => {
    setLoading(true);
    adminApi.listComplaints().then(r => setList(r.data.results || r.data))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const open = (c) => {
    setCurrent(c);
    setForm({
      status: c.status,
      priority: c.priority,
      resolution_note: c.resolution_note || '',
      assigned_to: c.assigned_to || '',
    });
    setShow(true);
  };

  const save = async () => {
    try {
      const payload = { ...form };
      if (!payload.assigned_to) delete payload.assigned_to;
      await adminApi.updateComplaint(current.ticket_id, payload);
      toast.success('Updated');
      setShow(false);
      load();
    } catch {
      toast.error('Failed');
    }
  };

  return (
    <div className="container-fluid mt-4">
      <h2>🎫 Complaint Tickets</h2>
      <Card className="mt-3">
        <Card.Body>
          <Button size="sm" className="mb-3" onClick={load}>🔄 Refresh</Button>
          {loading ? <Spinner animation="border" /> : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th>#</th><th>User</th><th>Subject</th>
                  <th>Priority</th><th>Status</th><th>Created</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {list.map(c => (
                  <tr key={c.ticket_id}>
                    <td>{c.ticket_id}</td>
                    <td>{c.user_email}</td>
                    <td>{c.subject}</td>
                    <td><Badge bg={
                      c.priority === 'HIGH' ? 'danger' :
                      c.priority === 'MEDIUM' ? 'warning' : 'secondary'
                    }>{c.priority}</Badge></td>
                    <td><Badge bg={
                      c.status === 'RESOLVED' ? 'success' :
                      c.status === 'CLOSED' ? 'dark' :
                      c.status === 'IN_PROGRESS' ? 'info' : 'warning'
                    }>{c.status}</Badge></td>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td>
                      <Button size="sm" onClick={() => open(c)}>Manage</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      <Modal show={show} onHide={() => setShow(false)}>
        <Modal.Header closeButton><Modal.Title>Manage Ticket</Modal.Title></Modal.Header>
        <Modal.Body>
          <p><strong>Subject:</strong> {current?.subject}</p>
          <p><strong>Description:</strong> {current?.description}</p>
          <Form.Group className="mb-3">
            <Form.Label>Status</Form.Label>
            <Form.Select value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>OPEN</option>
              <option>IN_PROGRESS</option>
              <option>RESOLVED</option>
              <option>CLOSED</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Priority</Form.Label>
            <Form.Select value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <option>LOW</option><option>MEDIUM</option><option>HIGH</option>
            </Form.Select>
          </Form.Group>
          <Form.Group>
            <Form.Label>Resolution Note</Form.Label>
            <Form.Control as="textarea" value={form.resolution_note}
              onChange={(e) => setForm({ ...form, resolution_note: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>Cancel</Button>
          <Button onClick={save}>Save</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}