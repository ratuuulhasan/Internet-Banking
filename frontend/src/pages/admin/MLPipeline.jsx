import { useEffect, useState } from 'react';
import {
  Card, Row, Col, Button, Table, Badge, Spinner,
  Modal, Alert, ProgressBar,
} from 'react-bootstrap';
import { toast } from 'react-toastify';
import { mlApi } from '../../api/mlPipeline';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function MLPipeline() {
  const [stats, setStats] = useState(null);
  const [versions, setVersions] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  const load = async () => {
    try {
      const [s, v, j] = await Promise.all([
        mlApi.getStats(),
        mlApi.listVersions(),
        mlApi.listJobs(),
      ]);
      setStats(s.data);
      setVersions(v.data.results || v.data);
      setJobs(j.data.results || j.data);
    } catch (e) {
      toast.error('Failed to load ML data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // Auto-refresh every 10s if a job is running
    const interval = setInterval(() => {
      if (stats?.running_job) load();
    }, 10000);
    return () => clearInterval(interval);
  }, [stats?.running_job]);

  const triggerRetrain = async () => {
    if (!window.confirm('Start a new training run? This may take 10-30 minutes.')) return;
    setTriggering(true);
    try {
      const { data } = await mlApi.triggerRetrain();
      toast.success(`Training started (task ${data.task_id})`);
      setTimeout(load, 2000);
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to trigger');
    } finally {
      setTriggering(false);
    }
  };

  const activate = async (id) => {
    if (!window.confirm('Activate this model version?')) return;
    try {
      await mlApi.activateVersion(id);
      toast.success('Model activated');
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed');
    }
  };

  const openLog = (job) => {
    setSelectedJob(job);
    setShowLog(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div className="container-fluid mt-4">
      <div className="d-flex justify-content-between align-items-center">
        <h2>🧠 ML Pipeline Dashboard</h2>
        <Button
          variant="primary"
          onClick={triggerRetrain}
          disabled={triggering || stats?.running_job}
        >
          {stats?.running_job ? '⏳ Training...' : '🚀 Trigger Retraining'}
        </Button>
      </div>

      {/* Active Model Alert */}
      {stats?.active_version && (
        <Alert variant="success" className="mt-3">
          <strong>🎯 Active Model:</strong> {stats.active_version.version_tag}
          {' '}(AUPRC: {(stats.active_version.auprc * 100).toFixed(2)}%,
          Recall: {(stats.active_version.recall * 100).toFixed(2)}%)
        </Alert>
      )}

      {/* Running Job */}
      {stats?.running_job && (
        <Alert variant="info" className="mt-3">
          <strong>⏳ Training in progress</strong> — started{' '}
          {new Date(stats.running_job.started_at).toLocaleString()}
          <ProgressBar animated now={100} className="mt-2" />
        </Alert>
      )}

      {/* Stats Cards */}
      <Row className="mt-3">
        <Col md={3}>
          <Card className="text-white bg-primary">
            <Card.Body>
              <small>Total Versions</small>
              <h3>{stats?.total_versions || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-white bg-success">
            <Card.Body>
              <small>Total Jobs</small>
              <h3>{stats?.total_jobs || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-white bg-warning">
            <Card.Body>
              <small>Last Retrain</small>
              <h6>
                {stats?.last_retrain
                  ? new Date(stats.last_retrain).toLocaleDateString()
                  : 'Never'}
              </h6>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-white bg-info">
            <Card.Body>
              <small>Drift Alerts</small>
              <h3>
                {stats?.recent_drift?.filter(d => d.is_drifted).length || 0}
              </h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Model Versions Table */}
      <Card className="mt-4">
        <Card.Body>
          <Card.Title>📦 Model Versions</Card.Title>
          <Table striped hover responsive>
            <thead>
              <tr>
                <th>Version</th>
                <th>Model</th>
                <th>AUPRC</th>
                <th>ROC-AUC</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1</th>
                <th>Status</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {versions.map(v => (
                <tr key={v.version_id}>
                  <td><code>{v.version_tag}</code></td>
                  <td>{v.model_type}</td>
                  <td>{(v.auprc * 100).toFixed(2)}%</td>
                  <td>{(v.roc_auc * 100).toFixed(2)}%</td>
                  <td>{(v.precision * 100).toFixed(2)}%</td>
                  <td>{(v.recall * 100).toFixed(2)}%</td>
                  <td>{(v.f1_score * 100).toFixed(2)}%</td>
                  <td>
                    <Badge bg={
                      v.status === 'ACTIVE' ? 'success' :
                      v.status === 'VALIDATED' ? 'info' :
                      v.status === 'CANDIDATE' ? 'warning' :
                      v.status === 'FAILED' ? 'danger' :
                      v.status === 'ARCHIVED' ? 'secondary' : 'dark'
                    }>{v.status}</Badge>
                  </td>
                  <td>{new Date(v.created_at).toLocaleString()}</td>
                  <td>
                    {v.status !== 'ACTIVE' && ['VALIDATED', 'ARCHIVED'].includes(v.status) && (
                      <Button size="sm" variant="primary"
                        onClick={() => activate(v.version_id)}>
                        Activate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {versions.length === 0 && (
                <tr><td colSpan={10} className="text-center text-muted">
                  No versions yet. Click "Trigger Retraining".
                </td></tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Retraining Jobs */}
      <Card className="mt-4">
        <Card.Body>
          <Card.Title>🔄 Retraining Jobs</Card.Title>
          <Table striped hover responsive>
            <thead>
              <tr>
                <th>ID</th><th>Trigger</th><th>Status</th>
                <th>Version</th><th>Started</th><th>Duration</th><th>Log</th>
              </tr>
            </thead>
            <tbody>
              {jobs.slice(0, 20).map(j => (
                <tr key={j.job_id}>
                  <td>{j.job_id}</td>
                  <td><Badge bg="secondary">{j.trigger}</Badge></td>
                  <td>
                    <Badge bg={
                      j.status === 'SUCCESS' ? 'success' :
                      j.status === 'RUNNING' ? 'info' :
                      j.status === 'FAILED' ? 'danger' : 'warning'
                    }>{j.status}</Badge>
                  </td>
                  <td>{j.model_version_tag || '-'}</td>
                  <td>{j.started_at ? new Date(j.started_at).toLocaleString() : '-'}</td>
                  <td>{j.duration_sec ? `${j.duration_sec.toFixed(1)}s` : '-'}</td>
                  <td>
                    <Button size="sm" variant="outline-primary"
                      onClick={() => openLog(j)}>View</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Drift Chart */}
      {stats?.recent_drift?.length > 0 && (
        <Card className="mt-4">
          <Card.Body>
            <Card.Title>📉 Recent Drift Metrics (PSI)</Card.Title>
            <Bar
              data={{
                labels: stats.recent_drift.map(
                  d => `${d.feature_name} (${d.date})`
                ),
                datasets: [{
                  label: 'PSI',
                  data: stats.recent_drift.map(d => d.psi_score),
                  backgroundColor: stats.recent_drift.map(d =>
                    d.is_drifted ? '#dc3545' : '#28a745'
                  ),
                }],
              }}
              options={{
                plugins: {
                  tooltip: {
                    callbacks: {
                      afterLabel: (ctx) => {
                        const d = stats.recent_drift[ctx.dataIndex];
                        return `Baseline: ${d.baseline_mean?.toFixed(2) || '-'}\nCurrent: ${d.current_mean?.toFixed(2) || '-'}`;
                      },
                    },
                  },
                },
              }}
            />
          </Card.Body>
        </Card>
      )}

      {/* Job Log Modal */}
      <Modal show={showLog} onHide={() => setShowLog(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Job #{selectedJob?.job_id} Log</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <pre style={{
            maxHeight: 500, overflow: 'auto',
            background: '#1e1e1e', color: '#d4d4d4',
            padding: 15, fontSize: 12, borderRadius: 5,
          }}>
            {selectedJob?.log_output || 'No log'}
            {selectedJob?.error_message && `\n\n❌ ERROR:\n${selectedJob.error_message}`}
          </pre>
        </Modal.Body>
      </Modal>
    </div>
  );
}