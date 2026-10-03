import { useEffect, useState } from 'react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { Card, Form, Button } from 'react-bootstrap';

export default function Transfer() {
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState({
    from_account_id: '', to_account_number: '', amount: '', description: '', otp_code: ''
  });
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);

  useEffect(() => {
    api.get('/accounts/').then((r) => {
      const list = r.data.results || r.data;
      setAccounts(list);
      if (list.length) setForm((f) => ({ ...f, from_account_id: list[0].account_id }));
    });
  }, []);

  const requestOTP = async () => {
    try {
      await api.post('/otp/request/', { purpose: 'TRANSFER' });
      setOtpSent(true);
      toast.success('OTP sent! Check console/email.');
    } catch (e) {
      toast.error('Failed to send OTP');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post('/transactions/transfer/', form);
      toast.success(`Transfer ${data.status}! Ref: ${data.reference_no}`);
      setForm({ ...form, to_account_number: '', amount: '', description: '', otp_code: '' });
      setOtpSent(false);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Transfer failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-4">
      <h3>💸 Fund Transfer</h3>
      <Card className="mt-3">
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>From Account</Form.Label>
              <Form.Select value={form.from_account_id}
                onChange={(e) => setForm({ ...form, from_account_id: e.target.value })}>
                {accounts.map((a) => (
                  <option key={a.account_id} value={a.account_id}>
                    {a.account_number} — ৳{a.balance}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>To Account Number</Form.Label>
              <Form.Control value={form.to_account_number}
                onChange={(e) => setForm({ ...form, to_account_number: e.target.value })}
                required placeholder="10-digit account number" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Amount (BDT)</Form.Label>
              <Form.Control type="number" value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required min="1" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description (optional)</Form.Label>
              <Form.Control value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>OTP</Form.Label>
              <div className="d-flex gap-2">
                <Form.Control value={form.otp_code} maxLength={6}
                  onChange={(e) => setForm({ ...form, otp_code: e.target.value })}
                  placeholder="6-digit OTP" required />
                <Button variant="outline-secondary" onClick={requestOTP} type="button">
                  {otpSent ? 'Resend' : 'Get OTP'}
                </Button>
              </div>
            </Form.Group>
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Processing...' : 'Transfer Now'}
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}