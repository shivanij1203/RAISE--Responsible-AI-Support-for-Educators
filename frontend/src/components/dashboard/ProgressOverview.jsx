const RISK_LABELS = {
  low: 'On Track',
  medium: 'Needs Attention',
  high: 'Action Required',
};

function ProgressOverview({ completed, total, completion, riskLevel }) {
  return (
    <div className="progress-overview">
      <div className="progress-bar-section">
        <div className="progress-bar-header">
          <span className="progress-bar-label">
            {completed} of {total} steps complete
          </span>
          <span className="progress-bar-pct">{completion}%</span>
        </div>
        <div className="progress-bar-track">
          <div className="progress-bar-fill-linear" style={{ width: `${completion}%` }}></div>
        </div>
      </div>
      <div className={`risk-indicator risk-${riskLevel}`}>
        {RISK_LABELS[riskLevel] || RISK_LABELS.low}
      </div>
    </div>
  );
}

export default ProgressOverview;
