import { useState, useEffect } from 'react';
import { fetchDashboardStats } from '../services/api';
import UserMenu from './UserMenu';
import NotificationBell from './NotificationBell';

const USE_CASE_LABELS = {
  'data_analysis': 'Data Analysis',
  'qualitative': 'Qualitative Analysis',
  'ml_model': 'ML / AI Model',
  'literature': 'Literature Review',
  'writing': 'Writing Assistance',
  'grading': 'Grading & Assessment',
  'teaching': 'Teaching Materials',
  'admin': 'Admin Decisions',
  'other': 'Other',
};

function InstitutionalDashboard({ user, role, onLogout, onBack, onViewToolRegistry }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scope, setScope] = useState('mine');

  useEffect(() => {
    loadStats(scope);
  }, [scope]);

  async function loadStats(s) {
    setLoading(true);
    setError('');
    try {
      const data = await fetchDashboardStats(s);
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard', err);
      setError('Could not load dashboard data.');
    } finally {
      setLoading(false);
    }
  }

  function getComplianceColor(pct) {
    if (pct === 100) return '#16a34a';
    if (pct >= 50) return '#d97706';
    return '#94a3b8';
  }

  const isFaculty = stats?.userRole === 'faculty';
  const userName = stats?.userName || '';

  const dashboardTitle = scope === 'all' ? 'Department Overview' : 'My Dashboard';
  const dashboardSubtitle = scope === 'all'
    ? 'Compliance overview across all activities in the department'
    : `Your personal compliance overview, ${userName}`;

  function renderTopBar() {
    return (
      <>
        <div className="pl-topbar">
          <div className="pl-topbar-inner">
            <div className="pl-topbar-brand">
              <img src="/usf-logo.svg" alt="USF" className="pl-topbar-logo" />
              <div className="pl-topbar-text">
                <span className="pl-topbar-uni">University of South Florida</span>
                <span className="pl-topbar-app">RAISE Ethics Toolkit</span>
              </div>
            </div>
            <div className="pl-topbar-right">
              <NotificationBell />
              <UserMenu user={user} role={role} onLogout={onLogout} />
            </div>
          </div>
        </div>
        <div className="pl-nav">
          <div className="pl-nav-inner">
            <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
            <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Library</button>
            <button className="pl-nav-tab active">Compliance Overview</button>
          </div>
        </div>
      </>
    );
  }

  if (loading && !stats) {
    return (
      <div className="inst-dashboard">
        {renderTopBar()}
        <div className="inst-dashboard-content">
          <div className="summary-cards">
            {[1, 2, 3].map(i => (
              <div key={i} className="summary-card skeleton-card">
                <div className="skeleton-line skeleton-title"></div>
                <div className="skeleton-line skeleton-bar"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="inst-dashboard">
        {renderTopBar()}
        <div className="inst-dashboard-content">
          <div className="error-banner">
            {error}
            <button className="error-retry" onClick={() => loadStats(scope)}>Retry</button>
          </div>
        </div>
      </div>
    );
  }

  const { totalActivities, avgCompliance, riskBreakdown, recentFeed, activities } = stats;

  return (
    <div className="inst-dashboard">
      {renderTopBar()}
      <div className="inst-dashboard-content">
        <div className="inst-dashboard-title-row">
          <div>
            <h1 className="inst-dashboard-heading">{dashboardTitle}</h1>
            <p className="inst-subtitle">{dashboardSubtitle}</p>
          </div>
          {isFaculty && (
            <div className="scope-toggle">
              <button
                className={`scope-btn ${scope === 'mine' ? 'active' : ''}`}
                onClick={() => setScope('mine')}
              >
                My Activities
              </button>
              <button
                className={`scope-btn ${scope === 'all' ? 'active' : ''}`}
                onClick={() => setScope('all')}
              >
                All Activities
              </button>
            </div>
          )}
        </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="sc-label">{scope === 'all' ? 'Total Activities' : 'My Activities'}</div>
          <div className="sc-value">{totalActivities}</div>
          <div className="sc-hint">{totalActivities === 0 ? 'No activities yet' : `${activities.filter(a => a.compliancePct === 100).length} fully compliant`}</div>
        </div>
        <div className="summary-card">
          <div className="sc-label">Avg. Compliance</div>
          <div className="sc-value" style={{ color: getComplianceColor(avgCompliance) }}>{avgCompliance}%</div>
          <div className="sc-hint">
            {avgCompliance === 100 ? 'All checkpoints complete' :
             avgCompliance >= 50 ? 'Making good progress' :
             totalActivities === 0 ? 'No data yet' : 'Needs attention'}
          </div>
        </div>
        <div className="summary-card">
          <div className="sc-label">Risk Breakdown</div>
          <div className="risk-pills">
            {riskBreakdown.high > 0 && <span className="risk-pill high">{riskBreakdown.high} High</span>}
            {riskBreakdown.medium > 0 && <span className="risk-pill medium">{riskBreakdown.medium} Medium</span>}
            {riskBreakdown.low > 0 && <span className="risk-pill low">{riskBreakdown.low} Low</span>}
            {totalActivities === 0 && <span className="risk-pill-empty">No activities</span>}
          </div>
        </div>
      </div>

      <div className="inst-grid">
        {/* Recent Activity Feed */}
        <div className="inst-section feed-section">
          <h2>Recent Activity</h2>
          {recentFeed.length === 0 ? (
            <p className="inst-empty">No compliance decisions recorded yet. Document checkpoints in your activities to see them here.</p>
          ) : (
            <div className="feed-list">
              {recentFeed.map((item, i) => (
                <div key={i} className="feed-item">
                  <div className="feed-dot"></div>
                  <div className="feed-body">
                    <div className="feed-main">
                      {scope === 'all' && <strong>{item.owner} </strong>}
                      documented <span className="feed-checkpoint">{item.checkpoint}</span>
                    </div>
                    <div className="feed-meta">
                      {item.activityName} &middot; {new Date(item.loggedAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Activities Table */}
        <div className="inst-section table-section">
          <h2>{scope === 'all' ? 'All Activities' : 'My Activities'}</h2>
          {activities.length === 0 ? (
            <p className="inst-empty">No activities created yet. Create your first activity to get started.</p>
          ) : (
            <table className="activities-table">
              <thead>
                <tr>
                  <th>Activity</th>
                  {scope === 'all' && <th>Owner</th>}
                  <th>Use Case</th>
                  <th>Compliance</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {activities.map(a => (
                  <tr key={a.id}>
                    <td className="at-name">{a.name}</td>
                    {scope === 'all' && <td className="at-owner">{a.owner}</td>}
                    <td className="at-usecase">{USE_CASE_LABELS[a.aiUseCase] || a.aiUseCase}</td>
                    <td>
                      <div className="compliance-cell">
                        <div className="compliance-bar-mini">
                          <div className="compliance-bar-fill" style={{
                            width: `${a.compliancePct}%`,
                            backgroundColor: getComplianceColor(a.compliancePct)
                          }}></div>
                        </div>
                        <span className="compliance-pct">{a.compliancePct}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`risk-badge ${a.risk}`}>
                        {a.risk.charAt(0).toUpperCase() + a.risk.slice(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}

export default InstitutionalDashboard;
