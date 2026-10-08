import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Table, Badge, Button, Modal } from 'react-bootstrap';
import ShapExplanation from '../components/ShapExplanation';

export default function Transactions() {
  const [txns, setTxns] = useState([]);
  const [showShap, setShowShap] = useState(false);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.get('/transactions/').then((r) => setTxns(r.data.results || r.data));
  }, []);

  const statusColor = {
    SUCCESS: 'success', PENDING: 'warning',
    FAILED: 'danger', HELD: 'info', REVERSED: 'secondary',
  };

  const openShap = (t) => {
    setSelected(t);
    setShowShap(true);
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
            <th>Status</th>
            <th>Risk</th>
            <th>Date</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {txns.map((t) => (
            <tr key={t.transaction_id}>
              <td><code>{t.reference_no}</code></td>
              <td>{t.transaction_type}</td>
              <td>৳ {parseFloat(t.amount).toLocaleString()}</td>
              <td><Badge bg={statusColor[t.status]}>{t.status}</Badge></td>
              <td>
                <Badge bg={
                  t.risk_level === 'HIGH' ? 'danger' :
                  t.risk_level === 'MEDIUM' ? 'warning' :
                  t.risk_level === 'LOW' ? 'info' : 'success'
                }>
                  {t.risk_level || 'N/A'}
                </Badge>
              </td>
              <td>{new Date(t.created_at).toLocaleString()}</td>
              <td>
                {t.fraud_explanation && (
                  <Button size="sm" variant="outline-info"
                    onClick={() => openShap(t)}>
                    🔍 Why?
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={showShap} onHide={() => setShowShap(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Transaction Explanation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selected && (
            <ShapExplanation
              explanation={selected.fraud_explanation}
              fraudScore={selected.fraud_score}
              riskLevel={selected.risk_level}
            />
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
}