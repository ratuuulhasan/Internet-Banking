import { useEffect, useState } from 'react';
import { Card, Table, Badge, Button, Spinner } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';

export default function AdminLoans() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    adminApi.listLoans().then(r => setList(r.data.results || r.data))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const decide = async (id, status) => {
    if (!window.confirm(`Confirm ${status}?`)) return;
    try {
      await adminApi.decideLoan(id, status);
      toast.success(`Loan ${status}`);
      load();
    } catch {
      toast.error('Failed');
    }
  };

  return (
    <div className="container-fluid mt-4">
      <h2>💰 Loan Applications</h2>
      <Card className="mt-3">
        <Card.Body>
          <Button size="sm" className="mb-3" onClick={load}>🔄 Refresh</Button>
          {loading ? <Spinner animation="border" /> : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th>#</th><th>User</th><th>Type</th><th>Amount</th>
                  <th>Tenure</th><th>EMI</th><th>AI Score</th>
                  <th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {list.map(l => (
                  <tr key={l.loan_id}>
                    <td>{l.loan_id}</td>
                    <td>{l.user_email}</td>
                    <td>{l.loan_type}</td>
                    <td>৳{parseFloat(l.principal_amount).toLocaleString()}</td>
                    <td>{l.tenure_months}m</td>
                    <td>৳{parseFloat(l.monthly_emi).toLocaleString()}</td>
                    <td>{l.ai_credit_score?.toFixed(1) || '-'}</td>
                    <td><Badge bg={
                      l.status === 'ACTIVE' || l.status === 'APPROVED' ? 'success' :
                      l.status === 'REJECTED' ? 'danger' : 'warning'
                    }>{l.status}</Badge></td>
                    <td>
                      {l.status === 'PENDING' && (
                        <>
                          <Button size="sm" variant="success"
                            onClick={() => decide(l.loan_id, 'APPROVED')}>Approve</Button>{' '}
                          <Button size="sm" variant="danger"
                            onClick={() => decide(l.loan_id, 'REJECTED')}>Reject</Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}