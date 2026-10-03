import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Button, Table, Modal, Form, Badge } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function Complaints() {
  const [list, setList] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ subject: '', description: '', priority: 'MEDIUM' });

  const load = () => api.get('/complaints/').then(r => setList(r.data.results || r.data));
  useEffect(() => { load(); }, []);


  const submit = async () => {
    try {
      await api.post('/complaints/', form);
      toast.success('Ticket created');
      setShow(false);
      setForm({ subject: '', description: '', priority: 'MEDIUM' });
      load();
    } catch {
      toast.error('Failed');
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between">
        <h3>My Complaints</h3>
        <Button onClick={() => setShow(true)}>+ New Ticket</Button>
      </div>
      <Table striped bordered hover className="mt-3">
        <thead>
          <tr><th>#</th><th>Subject</th><th>Priority</th><th>Status</th><th>Date</th></tr>
        </thead>
        <tbody>
          {list.map(c => (
            <tr key={c.ticket_id}>
              <td>{c.ticket_id}</td>
              <td>{c.subject}</td>
              <td><Badge bg={
                c.priority === 'HIGH' ? 'danger' :
                c.priority === 'MEDIUM' ? 'warning' : 'secondary'
              }>{c.priority}</Badge></td>
              <td><Badge bg={
                c.status === 'RESOLVED' ? 'success' :
                c.status === 'CLOSED' ? 'secondary' : 'info'
              }>{c.status}</Badge></td>
              <td>{new Date(c.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={show} onHide={() => setShow(false)}>
        <Modal.Header closeButton><Modal.Title>New Ticket</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Subject</Form.Label>
            <Form.Control value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control as="textarea" rows={4} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Form.Group>
          <Form.Group>
            <Form.Label>Priority</Form.Label>
            <Form.Select value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <option>LOW</option><option>MEDIUM</option><option>HIGH</option>
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>Cancel</Button>
          <Button onClick={submit}>Submit</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}