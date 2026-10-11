import { useEffect, useState } from 'react';
import {
  Card, Table, Badge, Button, Modal, Form, Spinner, Row, Col, Alert,
} from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';

const API_HOST =
  (process.env.REACT_APP_API_URL || 'http://localhost:8000/api').replace(
    '/api',
    ''
  );

function imageUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${API_HOST}${path}`;
}

export default function KYCApproval() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);
  const [current, setCurrent] = useState(null);
  const [decision, setDecision] = useState('APPROVED');
  const [remarks, setRemarks] = useState('');

  const load = () => {
    setLoading(true);
    adminApi
      .listKYC()
      .then((r) => {
        const items = r.data.results || r.data;
        setList(
          items.filter(
            (k) => !['APPROVED', 'REJECTED'].includes(k.status)
          )
        );
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

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

  const reprocess = async () => {
    try {
      if (adminApi.reprocessOCR) {
        await adminApi.reprocessOCR(current.kyc_id);
      } else {
        await fetch(
          `${process.env.REACT_APP_API_URL}/kyc/${current.kyc_id}/reprocess_ocr/`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access')}`,
            },
          }
        );
      }
      toast.info('OCR reprocessing started');
      setShow(false);
      setTimeout(load, 3000);
    } catch {
      toast.error('Failed to reprocess');
    }
  };

  const riskColor = {
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'success',
  };

  return (
    <div className="container-fluid mt-4">
      <h2>📄 KYC Approval Queue</h2>

      <Card className="mt-3">
        <Card.Body>
          <div className="d-flex justify-content-between mb-3">
            <span>
              Pending: <Badge bg="warning">{list.length}</Badge>
            </span>
            <Button size="sm" onClick={load}>
              🔄 Refresh
            </Button>
          </div>

          {loading ? (
            <Spinner animation="border" />
          ) : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th>#</th>
                  <th>User</th>
                  <th>NID</th>
                  <th>OCR</th>
                  <th>Tamper</th>
                  <th>Face</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {list.map((k) => (
                  <tr key={k.kyc_id}>
                    <td>{k.kyc_id}</td>
                    <td>
                      {k.user_name}
                      <br />
                      <small>{k.user_email}</small>
                    </td>
                    <td>{k.nid_number}</td>
                    <td>
                      {k.ocr_fields_extracted}/9
                      {k.ocr_confidence != null && (
                        <>
                          <br />
                          <small className="text-muted">
                            {(k.ocr_confidence * 100).toFixed(0)}% conf
                          </small>
                        </>
                      )}
                    </td>
                    <td>
                      <Badge
                        bg={riskColor[k.tamper_risk_level] || 'secondary'}
                      >
                        {k.tamper_risk_level || '-'}
                      </Badge>
                    </td>
                    <td>
                      {k.face_matched === true
                        ? '✅'
                        : k.face_matched === false
                        ? '❌'
                        : '—'}
                    </td>
                    <td>
                      <Badge
                        bg={
                          k.status === 'PROCESSING'
                            ? 'info'
                            : k.status === 'OCR_DONE'
                            ? 'primary'
                            : 'warning'
                        }
                      >
                        {k.status}
                      </Badge>
                    </td>
                    <td>
                      <Button size="sm" onClick={() => open(k)}>
                        Review
                      </Button>
                    </td>
                  </tr>
                ))}
                {list.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center text-muted">
                      No pending KYC 🎉
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* ============= REVIEW MODAL ============= */}
      <Modal show={show} onHide={() => setShow(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>
            Review KYC #{current?.kyc_id} — {current?.user_email}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {current && (
            <Row>
              {/* LEFT: Documents */}
              <Col md={6}>
                <h6>📷 Uploaded Documents</h6>

                {/* NID Front */}
                <div className="mb-3">
                  <strong>NID Front:</strong>
                  <br />
                  {current.document_front ? (
                    <img
                      src={imageUrl(current.document_front)}
                      alt="NID Front"
                      style={{
                        maxWidth: '100%',
                        border: '1px solid #ccc',
                        marginTop: 6,
                      }}
                    />
                  ) : (
                    <span className="text-muted">Not uploaded</span>
                  )}
                </div>

                {/* NID Back */}
                <div className="mb-3">
                  <strong>NID Back:</strong>
                  <br />
                  {current.document_back ? (
                    <img
                      src={imageUrl(current.document_back)}
                      alt="NID Back"
                      style={{
                        maxWidth: '100%',
                        border: '1px solid #ccc',
                        marginTop: 6,
                      }}
                    />
                  ) : (
                    <span className="text-muted">Not uploaded</span>
                  )}
                </div>

                {/* Selfie */}
                <div className="mb-3">
                  <strong>Selfie:</strong>
                  <br />
                  {current.selfie ? (
                    <img
                      src={imageUrl(current.selfie)}
                      alt="Selfie"
                      style={{
                        maxWidth: '100%',
                        border: '1px solid #ccc',
                        marginTop: 6,
                      }}
                    />
                  ) : (
                    <span className="text-muted">Not uploaded</span>
                  )}
                </div>
              </Col>

              {/* RIGHT: OCR + Verification Data */}
              <Col md={6}>
                <h6>🔍 OCR Extracted Data</h6>

                {!current.ocr_extracted && (
                  <Alert variant="warning" className="small">
                    OCR not processed yet. Click "Reprocess OCR" to retry.
                  </Alert>
                )}

                {current.ocr_extracted && (
                  <Table size="sm" bordered className="small">
                    <tbody>
                      <tr>
                        <td>
                          <strong>NID Number</strong>
                        </td>
                        <td>{current.nid_number}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Name (Bangla)</strong>
                        </td>
                        <td>{current.ocr_name_bangla || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Name (English)</strong>
                        </td>
                        <td>{current.ocr_name_english || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Father</strong>
                        </td>
                        <td>{current.ocr_father_name || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Mother</strong>
                        </td>
                        <td>{current.ocr_mother_name || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>DOB (user)</strong>
                        </td>
                        <td>{current.dob || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>DOB (OCR)</strong>
                        </td>
                        <td>{current.ocr_dob || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Blood Group</strong>
                        </td>
                        <td>{current.ocr_blood_group || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Issue Date</strong>
                        </td>
                        <td>{current.ocr_issue_date || '-'}</td>
                      </tr>
                      <tr>
                        <td>
                          <strong>Address</strong>
                        </td>
                        <td style={{ fontSize: 12 }}>
                          {current.ocr_address || current.address || '-'}
                        </td>
                      </tr>
                    </tbody>
                  </Table>
                )}

                {/* Verification Summary */}
                <h6 className="mt-3">🛡️ Verification Summary</h6>
                <Row>
                  <Col xs={6}>
                    <small>Confidence</small>
                    <br />
                    <strong>
                      {current.ocr_confidence != null
                        ? (current.ocr_confidence * 100).toFixed(1) + '%'
                        : '-'}
                    </strong>
                  </Col>
                  <Col xs={6}>
                    <small>Fields Extracted</small>
                    <br />
                    <strong>{current.ocr_fields_extracted}/9</strong>
                  </Col>
                  <Col xs={6} className="mt-2">
                    <small>Tamper Score</small>
                    <br />
                    <Badge
                      bg={riskColor[current.tamper_risk_level] || 'secondary'}
                    >
                      {current.tamper_risk_level || '-'}
                      {current.tamper_score != null && (
                        <> ({(current.tamper_score * 100).toFixed(0)}%)</>
                      )}
                    </Badge>
                  </Col>
                  <Col xs={6} className="mt-2">
                    <small>Face Match</small>
                    <br />
                    <Badge
                      bg={
                        current.face_matched === true
                          ? 'success'
                          : current.face_matched === false
                          ? 'danger'
                          : 'secondary'
                      }
                    >
                      {current.face_matched === true
                        ? 'MATCHED'
                        : current.face_matched === false
                        ? 'NO MATCH'
                        : 'N/A'}
                    </Badge>
                    {current.face_match_similarity != null && (
                      <small className="ms-1">
                        ({(current.face_match_similarity * 100).toFixed(0)}%)
                      </small>
                    )}
                  </Col>
                  <Col xs={12} className="mt-2">
                    <Alert
                      variant={current.auto_approve ? 'success' : 'warning'}
                      className="py-1 mb-0 small"
                    >
                      {current.auto_approve
                        ? '✅ AI suggests AUTO-APPROVE'
                        : '⚠️ AI suggests MANUAL REVIEW needed'}
                    </Alert>
                  </Col>
                </Row>

                {/* Reprocess Button */}
                <Button
                  size="sm"
                  variant="outline-secondary"
                  className="mt-3"
                  onClick={reprocess}
                >
                  🔄 Reprocess OCR
                </Button>
              </Col>
            </Row>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Form.Group style={{ flex: 1 }}>
            <Form.Label className="mb-1">
              <small>Remarks</small>
            </Form.Label>
            <Form.Control
              size="sm"
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Optional remarks..."
            />
          </Form.Group>
          <Form.Select
            size="sm"
            style={{ width: 150 }}
            value={decision}
            onChange={(e) => setDecision(e.target.value)}
          >
            <option value="APPROVED">Approve</option>
            <option value="REJECTED">Reject</option>
          </Form.Select>
          <Button variant="secondary" onClick={() => setShow(false)}>
            Cancel
          </Button>
          <Button
            variant={decision === 'APPROVED' ? 'success' : 'danger'}
            onClick={submit}
          >
            {decision === 'APPROVED' ? '✅ Approve' : '❌ Reject'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}