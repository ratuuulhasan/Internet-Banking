import { useEffect, useState } from 'react';
import {
  Card, Table, Badge, Button, Spinner, Alert, Modal,
} from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';
import ShapExplanation from '../../components/ShapExplanation';

export default function FraudAlerts() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showShap, setShowShap] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = () => {
    setLoading(true);
    adminApi.listFraudAlerts()
      .then(r => setList(r.data.results || r.data))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const decide = async (txnId, decision) => {
    if (!window.confirm(`Confirm ${decision}?`)) return;
    try {
      await adminApi.decideFraud(txnId, decision);
      toast.success(`Transaction ${decision}D`);
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Action failed');
    }
  };

  const openShap = (txn) => {
    setSelected(txn);
    setShowShap(true);
  };

  return (
    <div className="container-fluid mt-4">
      <h2>🚨 Fraud Alert Monitor</h2>

      {list.length > 0 && (
        <Alert variant="danger">
          ⚠️ <strong>{list.length}</strong> transaction(s) held for review.
        </Alert>
      )}

      <Card className="mt-3">
        <Card.Body>
          <div className="d-flex justify-content-between mb-3">
            <span>Held: <Badge bg="danger">{list.length}</Badge></span>
            <Button size="sm" onClick={load}>🔄 Refresh</Button>
          </div>

          {loading ? <Spinner animation="border" /> : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th>Ref</th><th>From → To</th><th>Amount</th>
                  <th>Fraud Score</th><th>Risk</th><th>Time</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {list.map(t => (
                  <tr key={t.transaction_id}>
                    <td><code>{t.reference_no}</code></td>
                    <td>
                      <small>{t.from_account_number}</small>
                      <br />→ <small>{t.to_account_number || '-'}</small>
                    </td>
                    <td>৳{parseFloat(t.amount).toLocaleString()}</td>
                    <td>
                      <Badge bg={
                        (t.fraud_score || 0) > 0.9 ? 'danger' :
                        (t.fraud_score || 0) > 0.8 ? 'warning' : 'secondary'
                      }>
                        {t.fraud_score ? (t.fraud_score * 100).toFixed(1) + '%' : 'N/A'}
                      </Badge>
                    </td>
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
                      <Button size="sm" variant="outline-info"
                        onClick={() => openShap(t)}>
                        🔍 Explain
                      </Button>{' '}
                      <Button size="sm" variant="success"
                        onClick={() => decide(t.transaction_id, 'APPROVE')}>
                        ✅
                      </Button>{' '}
                      <Button size="sm" variant="danger"
                        onClick={() => decide(t.transaction_id, 'REJECT')}>
                        ❌
                      </Button>
                    </td>
                  </tr>
                ))}
                {list.length === 0 && (
                  <tr>
                    <td colSpan={7} className="text-center text-muted">
                      No fraud alerts 🎉
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* SHAP Explanation Modal */}
      <Modal show={showShap} onHide={() => setShowShap(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            🔍 Transaction Explanation — <code>{selected?.reference_no}</code>
          </Modal.Title>
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
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowShap(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}