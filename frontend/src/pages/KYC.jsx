import { useEffect, useState } from 'react';
import api from '../api/axios';
import { Card, Form, Button, Badge, Spinner, Alert, ProgressBar, Row, Col } from 'react-bootstrap';
import { toast } from 'react-toastify';

export default function KYC() {
  const [kyc, setKyc] = useState(null);
  const [polling, setPolling] = useState(false);
  const [form, setForm] = useState({
    nid_number: '', dob: '', address: '', document_type: 'NID',
  });
  const [files, setFiles] = useState({});
  const [loading, setLoading] = useState(false);

  const loadKYC = async () => {
    try {
      const r = await api.get('/kyc/');
      const list = r.data.results || r.data;
      if (list.length) {
        setKyc(list[0]);
        // If OCR still processing, keep polling
        if (['PENDING', 'PROCESSING'].includes(list[0].status) &&
            !list[0].ocr_extracted) {
          setPolling(true);
        } else {
          setPolling(false);
        }
      } else {
        setKyc(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { loadKYC(); }, []);

  // Auto-poll while OCR processing
  useEffect(() => {
    if (!polling) return;
    const interval = setInterval(loadKYC, 3000);
    return () => clearInterval(interval);
  }, [polling]);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const fd = new FormData();
      Object.keys(form).forEach(k => {
        if (form[k]) fd.append(k, form[k]);
      });
      Object.keys(files).forEach(k => {
        if (files[k]) fd.append(k, files[k]);
      });

      const { data } = await api.post('/kyc/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      toast.success('KYC submitted! OCR processing...');
      setPolling(true);
      loadKYC();
    } catch (err) {
      const errors = err.response?.data;
      toast.error(errors?.error || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  // ---- Existing KYC View ----
  if (kyc) {
    const isProcessing = kyc.status === 'PROCESSING' ||
                        (kyc.status === 'PENDING' && !kyc.ocr_extracted);
    const hasOCR = !!kyc.ocr_extracted;

    return (
      <div className="container mt-4">
        <h3>📄 KYC Verification Status</h3>

        <Card className="mt-3">
          <Card.Body>
            <Row>
              <Col md={8}>
                <p><strong>NID:</strong> {kyc.nid_number}</p>
                <p><strong>DOB:</strong> {kyc.dob || '-'}</p>
                <p><strong>Address:</strong> {kyc.address || '-'}</p>
              </Col>
              <Col md={4} className="text-end">
                <p>Status:</p>
                <Badge bg={
                  kyc.status === 'APPROVED' ? 'success' :
                  kyc.status === 'REJECTED' ? 'danger' :
                  kyc.status === 'PROCESSING' ? 'info' :
                  kyc.status === 'OCR_DONE' ? 'primary' : 'warning'
                } style={{ fontSize: 14 }}>
                  {kyc.status}
                </Badge>
              </Col>
            </Row>

            {isProcessing && (
              <Alert variant="info" className="mt-3 mb-0">
                <Spinner animation="border" size="sm" className="me-2" />
                OCR processing... Please wait (10-30 seconds).
                <ProgressBar animated now={100} className="mt-2" />
              </Alert>
            )}

            {kyc.ocr_error && (
              <Alert variant="warning" className="mt-3 mb-0">
                ⚠️ OCR Error: {kyc.ocr_error}
              </Alert>
            )}
          </Card.Body>
        </Card>

        {/* ---- OCR Result Display ---- */}
        {hasOCR && (
          <Card className="mt-3">
            <Card.Body>
              <h5>🔍 OCR Extracted Data</h5>
              <Row>
                <Col md={6}>
                  <p><strong>Name (Bangla):</strong> {kyc.ocr_name_bangla || '-'}</p>
                  <p><strong>Name (English):</strong> {kyc.ocr_name_english || '-'}</p>
                  <p><strong>Father:</strong> {kyc.ocr_father_name || '-'}</p>
                  <p><strong>Mother:</strong> {kyc.ocr_mother_name || '-'}</p>
                </Col>
                <Col md={6}>
                  <p><strong>DOB (OCR):</strong> {kyc.ocr_dob || '-'}</p>
                  <p><strong>Blood Group:</strong> {kyc.ocr_blood_group || '-'}</p>
                  <p>
                    <strong>Confidence:</strong>{' '}
                    {kyc.ocr_confidence ? (kyc.ocr_confidence * 100).toFixed(1) + '%' : '-'}
                  </p>
                  <p><strong>Fields Extracted:</strong> {kyc.ocr_fields_extracted}/9</p>
                </Col>
              </Row>

              {/* Tamper + Face Match Badges */}
              <hr />
              <Row>
                <Col md={4}>
                  <strong>Tamper Check:</strong>{' '}
                  <Badge bg={
                    kyc.tamper_risk_level === 'HIGH' ? 'danger' :
                    kyc.tamper_risk_level === 'MEDIUM' ? 'warning' : 'success'
                  }>
                    {kyc.tamper_risk_level || 'N/A'}
                  </Badge>
                  {kyc.tamper_score != null && (
                    <small className="text-muted ms-2">
                      ({(kyc.tamper_score * 100).toFixed(1)}%)
                    </small>
                  )}
                </Col>
                <Col md={4}>
                  <strong>Face Match:</strong>{' '}
                  <Badge bg={
                    kyc.face_matched === true ? 'success' :
                    kyc.face_matched === false ? 'danger' : 'secondary'
                  }>
                    {kyc.face_matched === true ? 'MATCHED' :
                     kyc.face_matched === false ? 'NO MATCH' : 'N/A'}
                  </Badge>
                  {kyc.face_match_similarity != null && (
                    <small className="text-muted ms-2">
                      ({(kyc.face_match_similarity * 100).toFixed(0)}%)
                    </small>
                  )}
                </Col>
                <Col md={4}>
                  <strong>Verification:</strong>{' '}
                  <Badge bg={kyc.auto_approve ? 'success' : 'warning'}>
                    {kyc.auto_approve ? 'AUTO-APPROVE' : 'MANUAL REVIEW'}
                  </Badge>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        )}

        {kyc.remarks && (
          <Alert variant="secondary" className="mt-3">
            <strong>Admin Remarks:</strong> {kyc.remarks}
          </Alert>
        )}

        {kyc.status === 'REJECTED' && (
          <Button className="mt-3" onClick={() => { setKyc(null); setPolling(false); }}>
            Re-submit KYC
          </Button>
        )}

        {kyc.status === 'APPROVED' && (
          <Alert variant="success" className="mt-3">
            ✅ Your KYC is approved!
          </Alert>
        )}
      </div>
    );
  }

  // ---- KYC Submission Form ----
  return (
    <div className="container mt-4">
      <h3>📄 KYC Verification</h3>
      <Card className="mt-3">
        <Card.Body>
          <Alert variant="info">
            💡 Upload clear photos for better OCR accuracy.
            <br />
            First request may take 10-30 seconds (AI model loading).
          </Alert>

          <Form onSubmit={submit}>
            <Form.Group className="mb-3">
              <Form.Label>NID Number</Form.Label>
              <Form.Control
                value={form.nid_number}
                onChange={(e) => setForm({ ...form, nid_number: e.target.value })}
                placeholder="10, 13, or 17 digit NID"
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Date of Birth</Form.Label>
              <Form.Control
                type="date"
                value={form.dob}
                onChange={(e) => setForm({ ...form, dob: e.target.value })}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Address</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>NID Front Image *</Form.Label>
              <Form.Control
                type="file"
                accept="image/*"
                onChange={(e) => setFiles({ ...files, document_front: e.target.files[0] })}
                required
              />
              <Form.Text className="text-muted">
                NID card এর সামনের দিকের clear photo
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>NID Back Image</Form.Label>
              <Form.Control
                type="file"
                accept="image/*"
                onChange={(e) => setFiles({ ...files, document_back: e.target.files[0] })}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Selfie (for face match)</Form.Label>
              <Form.Control
                type="file"
                accept="image/*"
                onChange={(e) => setFiles({ ...files, selfie: e.target.files[0] })}
              />
              <Form.Text className="text-muted">
                আপনার স্পষ্ট face photo (face match verification এর জন্য)
              </Form.Text>
            </Form.Group>

            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Submitting...
                </>
              ) : 'Submit KYC'}
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}