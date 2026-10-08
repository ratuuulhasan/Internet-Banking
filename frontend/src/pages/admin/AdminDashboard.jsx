import { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Badge, Spinner } from 'react-bootstrap';
import { adminApi } from '../../api/admin';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend, ArcElement, PointElement, LineElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, ArcElement,
  PointElement, LineElement, Title, Tooltip, Legend
);

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([adminApi.getStats(), adminApi.getActivity()])
      .then(([s, a]) => {
        setStats(s.data);
        setActivity(a.data.recent_transactions || []);
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center mt-5"><Spinner animation="border" /></div>;
  if (!stats) return <p>No data available</p>;

  const cards = [
    { title: 'Total Users', value: stats.total_users, color: 'primary', icon: '👥' },
    { title: 'Active Users', value: stats.active_users, color: 'success', icon: '✅' },
    { title: 'Pending KYC', value: stats.pending_kyc, color: 'warning', icon: '📄' },
    { title: 'Held Txns', value: stats.held_txns, color: 'danger', icon: '🚨' },
    { title: 'Accounts', value: stats.total_accounts, color: 'info', icon: '🏦' },
    { title: 'Total Balance', value: `৳${(stats.total_balance || 0).toLocaleString()}`, color: 'dark', icon: '💰' },
    { title: 'Txns Today', value: stats.txns_today, color: 'primary', icon: '📊' },
    { title: 'Open Complaints', value: stats.open_complaints, color: 'warning', icon: '🎫' },
  ];

  return (
    <div className="container-fluid mt-4">
      <h2>👑 Admin Dashboard</h2>

      <Row className="mt-3">
        {cards.map((c, i) => (
          <Col md={3} key={i}>
            <Card className={`text-white bg-${c.color} mb-3`}>
              <Card.Body>
                <div className="d-flex justify-content-between">
                  <div>
                    <small>{c.title}</small>
                    <h3>{c.value}</h3>
                  </div>
                  <div style={{ fontSize: 32 }}>{c.icon}</div>
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Row className="mt-4">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Transactions Overview</Card.Title>
              <Bar
                data={{
                  labels: ['Today', 'Last 30 Days'],
                  datasets: [{
                    label: 'Transactions',
                    data: [stats.txns_today, stats.txns_30d],
                    backgroundColor: ['#0d6efd', '#198754'],
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { display: false } } }}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Platform Health</Card.Title>
              <Doughnut
                data={{
                  labels: ['Active', 'Pending KYC', 'Held Txns'],
                  datasets: [{
                    data: [stats.active_users, stats.pending_kyc, stats.held_txns],
                    backgroundColor: ['#198754', '#ffc107', '#dc3545'],
                  }],
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Card className="mt-4">
        <Card.Body>
          <Card.Title>Recent Transactions</Card.Title>
          <Table striped hover size="sm">
            <thead>
              <tr>
                <th>Reference</th><th>User</th><th>Amount</th>
                <th>Status</th><th>Time</th>
              </tr>
            </thead>
            <tbody>
              {activity.map((t, i) => (
                <tr key={i}>
                  <td><code>{t.reference}</code></td>
                  <td>{t.user}</td>
                  <td>৳{t.amount.toLocaleString()}</td>
                  <td>
                    <Badge bg={
                      t.status === 'SUCCESS' ? 'success' :
                      t.status === 'HELD' ? 'danger' :
                      t.status === 'PENDING' ? 'warning' : 'secondary'
                    }>{t.status}</Badge>
                  </td>
                  <td>{new Date(t.time).toLocaleString()}</td>
                </tr>
              ))}
              {activity.length === 0 && (
                <tr><td colSpan={5} className="text-center text-muted">No recent transactions</td></tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </div>
  );
}