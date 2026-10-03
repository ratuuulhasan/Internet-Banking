import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Table, Badge } from 'react-bootstrap';

export default function Transactions() {
  const [txns, setTxns] = useState([]);
  useEffect(() => {
    api.get('/transactions/').then((r) => setTxns(r.data.results || r.data));
  }, []);

  const statusColor = {
    SUCCESS: 'success', PENDING: 'warning',
    FAILED: 'danger', HELD: 'info', REVERSED: 'secondary',
  };

  return (
    <div className="container mt-4">
      <h3>Transaction History</h3>
      <Table striped bordered hover className="mt-3">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Type</th>
            <th>Amount</th>
            <th>From</th>
            <th>To</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {txns.map((t) => (
            <tr key={t.transaction_id}>
              <td><code>{t.reference_no}</code></td>
              <td>{t.transaction_type}</td>
              <td>৳ {parseFloat(t.amount).toLocaleString()}</td>
              <td>{t.from_account_number}</td>
              <td>{t.to_account_number || '-'}</td>
              <td><Badge bg={statusColor[t.status]}>{t.status}</Badge></td>
              <td>{new Date(t.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}