import { useEffect, useState } from 'react';
import { Card, Table, Badge, Button, Modal, Form, Spinner } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';

export default function KYCApproval() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);
  const [current, setCurrent] = useState(null);
  const [decision, setDecision] = useState('APPROVED');
  const [remarks, setRemarks] = useState('');

  const load = () => {
    setLoading(true);
    adminApi.listKYC().then(r => {
      const items = r.data.results || r.data;
      setList(items.filter(k => k.status === 'PENDING'));
    }).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const open = (k) => {
    setCurrent(k);
    setDecision('APPROVED');
    setRemarks('');
    setShow(true);
  };

  const submit = async () => {
    try {
      await adminApi.approveKYC(current.kyc_id, decision, remarks);
      toast.success(`KYC ${decision}`);
      setShow(false);
      load();
    } catch {
      toast.error('Failed');
    }
  };

  return (
    <div className="container-fluid mt-4">
      <h2>📄 KYC Approval Queue</h2>

      <Card className="mt-3">
        <Card.Body>
          <div className="d-flex justify-content-between mb-3">
            <span>Pending: <Badge bg="warning">{list.length}</Badge></span>
            <Button size="sm" onClick={load}>🔄 Refresh</Button>
          </div>

          {loading ? <Spinner animation="border" /> : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th>#</th><th>User</th><th>NID</th><th>DOB</th>
                  <th>Submitted</th><th>Docs</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {list.map(k => (
                  <tr key={k.kyc_id}>
                    <td>{k.kyc_id}</td>
                    <td>{k.user_name}<br /><small>{k.user_email}</small></td>
                    <td>{k.nid_number}</td>
                    <td>{k.dob}</td>
                    <td>{new Date(k.created_at).toLocaleDateString()}</td>
                    <td>
                      {k.document_front && <a href={k.document_front} target="_blank" rel="noreferrer">Front </a>}
                      {k.document_back && <a href={k.document_back} target="_blank" rel="noreferrer">Back</a>}
                    </td>
                    <td>
                      <Button size="sm" onClick={() => open(k)}>Review</Button>
                    </td>
                  </tr>
                ))}
                {list.length === 0 && (
                  <tr><td colSpan={7} className="text-center text-muted">No pending KYC 🎉</td></tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      <Modal show={show} onHide={() => setShow(false)} size="lg">
        <Modal.Header closeButton><Modal.Title>Review KYC</Modal.Title></Modal.Header>
        <Modal.Body>
          {current && (
            <>
              <p><strong>User:</strong> {current.user_name} ({current.user_email})</p>
              <p><strong>NID:</strong> {current.nid_number}</p>
              <p><strong>DOB:</strong> {current.dob}</p>
              <p><strong>Address:</strong> {current.address}</p>
              <div className="d-flex gap-3 my-3">
                {current.document_front &&
                  <img src={current.document_front} alt="front"
                       style={{ maxWidth: 250, border: '1px solid #ccc' }} />}
                {current.document_back &&
                  <img src={current.document_back} alt="back"
                       style={{ maxWidth: 250, border: '1px solid #ccc' }} />}
              </div>

              <Form.Group className="mb-3">
                <Form.Label>Decision</Form.Label>
                <Form.Select value={decision}
                  onChange={(e) => setDecision(e.target.value)}>
                  <option value="APPROVED">Approve</option>
                  <option value="REJECTED">Reject</option>
                </Form.Select>
              </Form.Group>
              <Form.Group>
                <Form.Label>Remarks</Form.Label>
                <Form.Control as="textarea" value={remarks}
                  onChange={(e) => setRemarks(e.target.value)} />
              </Form.Group>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>Cancel</Button>
          <Button variant={decision === 'APPROVED' ? 'success' : 'danger'}
            onClick={submit}>Submit {decision}</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}