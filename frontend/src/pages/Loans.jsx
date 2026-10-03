import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Button, Table, Modal, Form, Badge } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function Loans() {
  const [loans, setLoans] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({
    account: '', loan_type: 'PERSONAL', principal_amount: '',
    interest_rate: 10, tenure_months: 12, purpose: ''
  });

  const load = () => {
    api.get('/loans/').then(r => setLoans(r.data.results || r.data));
    api.get('/accounts/').then(r => setAccounts(r.data.results || r.data));
  };
  useEffect(() => { load(); }, []);


  const apply = async () => {
    try {
      await api.post('/loans/', form);
      toast.success('Loan application submitted');
      setShow(false);
      load();
    } catch {
      toast.error('Failed');
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between">
        <h3>My Loans</h3>
        <Button onClick={() => setShow(true)}>+ Apply for Loan</Button>
      </div>
      <Table striped bordered hover className="mt-3">
        <thead>
          <tr><th>Type</th><th>Amount</th><th>Tenure</th>
              <th>EMI</th><th>Credit Score</th><th>Status</th></tr>
        </thead>
        <tbody>
          {loans.map(l => (
            <tr key={l.loan_id}>
              <td>{l.loan_type}</td>
              <td>৳{l.principal_amount}</td>
              <td>{l.tenure_months}m</td>
              <td>৳{l.monthly_emi}</td>
              <td>{l.ai_credit_score?.toFixed(1) || '-'}</td>
              <td><Badge bg={
                l.status === 'ACTIVE' ? 'success' :
                l.status === 'REJECTED' ? 'danger' : 'warning'
              }>{l.status}</Badge></td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={show} onHide={() => setShow(false)}>
        <Modal.Header closeButton><Modal.Title>Apply Loan</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Account</Form.Label>
            <Form.Select value={form.account}
              onChange={(e) => setForm({ ...form, account: e.target.value })}>
              <option value="">Select</option>
              {accounts.map(a => <option key={a.account_id} value={a.account_id}>{a.account_number}</option>)}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Loan Type</Form.Label>
            <Form.Select value={form.loan_type}
              onChange={(e) => setForm({ ...form, loan_type: e.target.value })}>
              <option>PERSONAL</option><option>HOME</option>
              <option>CAR</option><option>EDUCATION</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Amount</Form.Label>
            <Form.Control type="number" value={form.principal_amount}
              onChange={(e) => setForm({ ...form, principal_amount: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Interest Rate (%)</Form.Label>
            <Form.Control type="number" value={form.interest_rate}
              onChange={(e) => setForm({ ...form, interest_rate: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Tenure (months)</Form.Label>
            <Form.Control type="number" value={form.tenure_months}
              onChange={(e) => setForm({ ...form, tenure_months: e.target.value })} />
          </Form.Group>
          <Form.Group>
            <Form.Label>Purpose</Form.Label>
            <Form.Control as="textarea" value={form.purpose}
              onChange={(e) => setForm({ ...form, purpose: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>Cancel</Button>
          <Button onClick={apply}>Submit</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}