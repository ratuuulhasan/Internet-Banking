import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Table, Button, Modal, Form, Badge } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function Bills() {
  const [bills, setBills] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [showPay, setShowPay] = useState(false);
  const [current, setCurrent] = useState(null);
  const [form, setForm] = useState({ from_account_id: '', otp_code: '' });
  const [showAdd, setShowAdd] = useState(false);
  const [newBill, setNewBill] = useState({
    biller_name: '', bill_number: '', amount: '', due_date: ''
  });

  const load = () => {
    api.get('/bills/').then(r => setBills(r.data.results || r.data));
    api.get('/accounts/').then(r => setAccounts(r.data.results || r.data));
  };

    useEffect(() => { load(); }, []);

  const openPay = (bill) => {
    setCurrent(bill);
    setForm({ from_account_id: accounts[0]?.account_id || '', otp_code: '' });
    setShowPay(true);
  };

  const requestOTP = async () => {
    await api.post('/otp/request/', { purpose: 'BILL_PAYMENT' });
    toast.success('OTP sent');
  };

  const payBill = async () => {
    try {
      const { data } = await api.post('/bills/pay/', {
        bill_id: current.bill_id,
        ...form
      });
      toast.success(`Paid! Ref: ${data.reference_no}`);
      setShowPay(false);
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Payment failed');
    }
  };

  const addBill = async () => {
    try {
      await api.post('/bills/', newBill);
      toast.success('Bill added');
      setShowAdd(false);
      setNewBill({ biller_name: '', bill_number: '', amount: '', due_date: '' });
      load();
    } catch {
      toast.error('Failed to add bill');
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between">
        <h3>Bills</h3>
        <Button onClick={() => setShowAdd(true)}>+ Add Bill</Button>
      </div>
      <Table striped bordered hover className="mt-3">
        <thead>
          <tr>
            <th>Biller</th><th>Bill #</th><th>Amount</th>
            <th>Due</th><th>Status</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {bills.map(b => (
            <tr key={b.bill_id}>
              <td>{b.biller_name}</td>
              <td>{b.bill_number}</td>
              <td>৳{b.amount}</td>
              <td>{b.due_date}</td>
              <td><Badge bg={b.status === 'PAID' ? 'success' : 'warning'}>{b.status}</Badge></td>
              <td>
                {b.status === 'UNPAID' &&
                  <Button size="sm" onClick={() => openPay(b)}>Pay</Button>}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Pay Modal */}
      <Modal show={showPay} onHide={() => setShowPay(false)}>
        <Modal.Header closeButton><Modal.Title>Pay Bill</Modal.Title></Modal.Header>
        <Modal.Body>
          <p>Biller: <strong>{current?.biller_name}</strong></p>
          <p>Amount: <strong>৳{current?.amount}</strong></p>
          <Form.Group className="mb-3">
            <Form.Label>From Account</Form.Label>
            <Form.Select value={form.from_account_id}
              onChange={(e) => setForm({ ...form, from_account_id: e.target.value })}>
              {accounts.map(a => (
                <option key={a.account_id} value={a.account_id}>
                  {a.account_number} - ৳{a.balance}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group>
            <Form.Label>OTP</Form.Label>
            <div className="d-flex gap-2">
              <Form.Control value={form.otp_code}
                onChange={(e) => setForm({ ...form, otp_code: e.target.value })}
                maxLength={6} />
              <Button variant="outline-secondary" onClick={requestOTP}>Get OTP</Button>
            </div>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPay(false)}>Cancel</Button>
          <Button onClick={payBill}>Pay Now</Button>
        </Modal.Footer>
      </Modal>

      {/* Add Bill Modal */}
      <Modal show={showAdd} onHide={() => setShowAdd(false)}>
        <Modal.Header closeButton><Modal.Title>Add Bill</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Biller Name</Form.Label>
            <Form.Control value={newBill.biller_name}
              onChange={(e) => setNewBill({ ...newBill, biller_name: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Bill Number</Form.Label>
            <Form.Control value={newBill.bill_number}
              onChange={(e) => setNewBill({ ...newBill, bill_number: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Amount</Form.Label>
            <Form.Control type="number" value={newBill.amount}
              onChange={(e) => setNewBill({ ...newBill, amount: e.target.value })} />
          </Form.Group>
          <Form.Group>
            <Form.Label>Due Date</Form.Label>
            <Form.Control type="date" value={newBill.due_date}
              onChange={(e) => setNewBill({ ...newBill, due_date: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAdd(false)}>Cancel</Button>
          <Button onClick={addBill}>Save</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}