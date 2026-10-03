import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Form, Button, Badge } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function KYC() {
  const [kyc, setKyc] = useState(null);
  const [form, setForm] = useState({
    nid_number: '', dob: '', address: '',
    document_type: 'NID'
  });
  const [files, setFiles] = useState({});

  useEffect(() => {
    api.get('/kyc/').then((r) => {
      const list = r.data.results || r.data;
      if (list.length) setKyc(list[0]);
    });
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    Object.keys(form).forEach(k => fd.append(k, form[k]));
    Object.keys(files).forEach(k => fd.append(k, files[k]));
    try {
      const { data } = await api.post('/kyc/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setKyc(data);
      toast.success('KYC submitted. Await approval.');
    } catch (err) {
      toast.error('Submission failed');
    }
  };

  if (kyc) {
    return (
      <div className="container mt-4">
        <h3>KYC Status</h3>
        <Card className="mt-3">
          <Card.Body>
            <p><strong>NID:</strong> {kyc.nid_number}</p>
            <p><strong>DOB:</strong> {kyc.dob}</p>
            <p><strong>Address:</strong> {kyc.address}</p>
            <p>Status: <Badge bg={
              kyc.status === 'APPROVED' ? 'success' :
              kyc.status === 'REJECTED' ? 'danger' : 'warning'
            }>{kyc.status}</Badge></p>
            {kyc.remarks && <p><strong>Remarks:</strong> {kyc.remarks}</p>}
          </Card.Body>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <h3>KYC Verification</h3>
      <Card className="mt-3">
        <Card.Body>
          <Form onSubmit={submit}>
            <Form.Group className="mb-3">
              <Form.Label>NID Number</Form.Label>
              <Form.Control value={form.nid_number}
                onChange={(e) => setForm({ ...form, nid_number: e.target.value })}
                required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Date of Birth</Form.Label>
              <Form.Control type="date" value={form.dob}
                onChange={(e) => setForm({ ...form, dob: e.target.value })} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Address</Form.Label>
              <Form.Control as="textarea" value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Document (Front)</Form.Label>
              <Form.Control type="file" accept="image/*"
                onChange={(e) => setFiles({ ...files, document_front: e.target.files[0] })} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Document (Back)</Form.Label>
              <Form.Control type="file" accept="image/*"
                onChange={(e) => setFiles({ ...files, document_back: e.target.files[0] })} />
            </Form.Group>
            <Button type="submit">Submit KYC</Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}