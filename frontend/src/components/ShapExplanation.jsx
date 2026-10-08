import { Card, Badge, ProgressBar, Table, Alert } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function ShapExplanation({ explanation, fraudScore, riskLevel }) {
  if (!explanation || !explanation.top_features) {
    return <Alert variant="secondary">No explanation available</Alert>;
  }

  const { base_value, prediction, top_features, top_positive, top_negative } = explanation;

  // Waterfall-style chart data
  const chartData = {
    labels: top_features.map(f => f.feature),
    datasets: [
      {
        label: 'SHAP Contribution',
        data: top_features.map(f => f.shap_value),
        backgroundColor: top_features.map(f =>
          f.shap_value > 0 ? 'rgba(220, 53, 69, 0.8)' : 'rgba(25, 135, 84, 0.8)'
        ),
        borderColor: top_features.map(f =>
          f.shap_value > 0 ? '#dc3545' : '#198754'
        ),
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    indexAxis: 'y',
    responsive: true,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Feature Contributions (Red = Increases Risk, Green = Decreases)',
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const f = top_features[ctx.dataIndex];
            return [
              `SHAP: ${f.shap_value}`,
              `Value: ${f.feature_value}`,
              `Direction: ${f.direction}`,
            ];
          },
        },
      },
    },
    scales: {
      x: { title: { display: true, text: 'SHAP Value' } },
    },
  };

  const riskColor = {
    SAFE: 'success', LOW: 'info',
    MEDIUM: 'warning', HIGH: 'danger',
  };

  return (
    <div>
      {/* Prediction Summary */}
      <Card className="mb-3">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">Prediction</h5>
              <h3 className="mb-0">
                {prediction ? (prediction * 100).toFixed(2) : (fraudScore * 100).toFixed(2)}%
              </h3>
              <small className="text-muted">
                Base value: {base_value}
              </small>
            </div>
            <div className="text-end">
              <Badge bg={riskColor[riskLevel] || 'secondary'} style={{ fontSize: 16 }}>
                {riskLevel}
              </Badge>
            </div>
          </div>
          <ProgressBar
            className="mt-3"
            variant={riskColor[riskLevel] || 'secondary'}
            now={(prediction || fraudScore) * 100}
            label={`${((prediction || fraudScore) * 100).toFixed(1)}%`}
          />
        </Card.Body>
      </Card>

      {/* SHAP Bar Chart */}
      <Card className="mb-3">
        <Card.Body>
          <h6>🔍 Why this decision?</h6>
          <Bar data={chartData} options={chartOptions} height={120} />
        </Card.Body>
      </Card>

      {/* Top Risk Factors */}
      <Card className="mb-3">
        <Card.Body>
          <h6 className="text-danger">🚨 Top Risk Contributors</h6>
          {top_positive.length === 0 ? (
            <p className="text-muted">No risk factors detected</p>
          ) : (
            <Table size="sm" striped>
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Value</th>
                  <th>Impact</th>
                </tr>
              </thead>
              <tbody>
                {top_positive.map((f, i) => (
                  <tr key={i}>
                    <td><code>{f.feature}</code></td>
                    <td>{f.feature_value}</td>
                    <td className="text-danger">
                      +{f.shap_value.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Top Safety Factors */}
      <Card className="mb-3">
        <Card.Body>
          <h6 className="text-success">✅ Top Safety Indicators</h6>
          {top_negative.length === 0 ? (
            <p className="text-muted">No safety indicators</p>
          ) : (
            <Table size="sm" striped>
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Value</th>
                  <th>Impact</th>
                </tr>
              </thead>
              <tbody>
                {top_negative.map((f, i) => (
                  <tr key={i}>
                    <td><code>{f.feature}</code></td>
                    <td>{f.feature_value}</td>
                    <td className="text-success">
                      {f.shap_value.toFixed(4)}
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