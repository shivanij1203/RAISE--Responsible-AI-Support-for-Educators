import { useState, useEffect } from 'react';
import { toggleCheckpoint, logDecision, fetchProject, fetchTools } from '../services/api';
import CheckpointComments from './CheckpointComments';
import UserMenu from './UserMenu';
import LogDecisionModal from './modals/LogDecisionModal';
import VerificationScanModal from './modals/VerificationScanModal';
import DisclosureModal from './modals/DisclosureModal';
import EditActivityModal from './modals/EditActivityModal';
import { USE_CASE_LABELS_SHORT } from '../constants/useCases';
import { getCompletionPercentage, getRiskAssessment } from '../utils/risk';
import { generateDisclosure } from '../utils/disclosure';
import { generateComplianceReport } from '../utils/complianceReport';

const SCANNABLE_CHECKPOINTS = ['data_deidentified', 'ferpa_compliance', 'data_classification'];

function ProjectDashboard({ project: initialProject, user, role, onBack, onLogout, onProjectUpdated, onViewToolRegistry, onViewDashboard }) {
  const [project, setProject] = useState(initialProject);
  const [activeTab, setActiveTab] = useState('checkpoints');
  const [expandedCheckpoint, setExpandedCheckpoint] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [logCheckpointId, setLogCheckpointId] = useState(null);
  const [scanCheckpointId, setScanCheckpointId] = useState(null);
  const [showDisclosure, setShowDisclosure] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);

  useEffect(() => {
    fetchTools().then(setAvailableTools).catch(() => {});
  }, []);

  // Refresh project data from API
  async function refreshProject() {
    try {
      const updated = await fetchProject(project.id);
      setProject(updated);
      if (onProjectUpdated) onProjectUpdated(updated);
    } catch (err) {
      console.error('Failed to refresh project', err);
    }
  }

  async function handleCheckpointToggle(checkpointId) {
    setSaving(true);
    try {
      const result = await toggleCheckpoint(project.id, checkpointId);
      const updatedCheckpoints = project.checkpoints.map(cp =>
        cp.id === checkpointId
          ? { ...cp, completed: result.completed, completedAt: result.completedAt }
          : cp
      );
      const updatedProject = { ...project, checkpoints: updatedCheckpoints };
      setProject(updatedProject);
      if (onProjectUpdated) onProjectUpdated(updatedProject);
      showToast(result.completed ? 'Checkpoint complete ✓' : 'Checkpoint unchecked');
    } catch (err) {
      console.error('Failed to toggle checkpoint', err);
    } finally {
      setSaving(false);
    }
  }

  async function handleLogDecision(data) {
    if (!data.checkpoint || !data.description) return;
    setSaving(true);
    try {
      const result = await logDecision(project.id, data);
      const newDecisionObj = {
        id: result.id,
        checkpoint: result.checkpoint,
        description: result.description,
        notes: result.notes,
        proofType: result.proofType,
        proofValue: result.proofValue,
        toolUsed: result.toolUsed,
        loggedAt: result.loggedAt,
      };
      const updatedCheckpoints = project.checkpoints.map(cp =>
        cp.id === data.checkpoint
          ? { ...cp, completed: result.checkpointCompleted, completedAt: result.checkpointCompletedAt }
          : cp
      );
      const updatedProject = {
        ...project,
        checkpoints: updatedCheckpoints,
        decisions: [newDecisionObj, ...(project.decisions || [])],
      };
      setProject(updatedProject);
      if (onProjectUpdated) onProjectUpdated(updatedProject);
      setLogCheckpointId(null);
    } catch (err) {
      console.error('Failed to log decision', err);
      alert('Error saving decision. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  function showToast(message) {
    setToast(message);
    setTimeout(() => setToast(''), 2500);
  }

  const allCheckpoints = project.checkpoints || [];
  const myCheckpoints = role === 'compliance'
    ? allCheckpoints
    : allCheckpoints.filter(c => c.assignedTo === role);
  const categories = [...new Set(myCheckpoints.map(c => c.category))];
  const completion = role === 'compliance'
    ? getCompletionPercentage(allCheckpoints)
    : getCompletionPercentage(myCheckpoints);
  const riskAssessment = getRiskAssessment({ allCheckpoints, myCheckpoints, role, completion });

  function handleExportReport(scope) {
    generateComplianceReport({ project, role, scope, completion, riskAssessment });
  }

  return (
    <div className="project-dashboard">
      {toast && <div className="toast-notification">{toast}</div>}

      {/* USF Top Bar */}
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
            <UserMenu user={user} role={role} onLogout={onLogout} />
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
          <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Library</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      <div className="pd-content">
        <header className="pd-header">
          <div className="pd-header-left">
            <h1 className="pd-title">{project.name} <button className="edit-name-btn" onClick={() => setShowEditModal(true)} title="Edit"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button></h1>
            <div className="pd-meta">
              <span>{USE_CASE_LABELS_SHORT[project.aiUseCase] || project.aiUseCase}</span>
              <span className="pd-meta-sep">&middot;</span>
              <span>Started {new Date(project.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
            </div>
            {project.description && (
              <p className="pd-description">{project.description}</p>
            )}
          </div>
          {(() => {
            const roles = [...new Set(project.checkpoints?.map(c => c.assignedTo) || [])];
            const hasMultipleRoles = roles.length > 1;
            if (!hasMultipleRoles) {
              return (
                <div className="pd-header-actions">
                  <button className="pd-disclosure-btn" onClick={() => setShowDisclosure(true)}>Disclosure</button>
                  <button className="pd-export-btn" onClick={() => handleExportReport('full')}>Export Report</button>
                </div>
              );
            }
            return (
              <div className="pd-header-actions">
                <button className="pd-disclosure-btn" onClick={() => setShowDisclosure(true)}>Disclosure</button>
                <div className="export-dropdown-wrap">
                  <button className="pd-export-btn" onClick={() => setShowExportMenu(!showExportMenu)}>Export Report ▾</button>
                  {showExportMenu && (
                    <div className="export-dropdown">
                      <button onClick={() => { handleExportReport('mine'); setShowExportMenu(false); }}>My Checkpoints</button>
                      <button onClick={() => { handleExportReport('full'); setShowExportMenu(false); }}>Full Activity Report</button>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}
        </header>

        {/* Progress Summary */}
        <div className="progress-overview">
          <div className="progress-bar-section">
            <div className="progress-bar-header">
              <span className="progress-bar-label">
                {myCheckpoints.filter(c => c.completed).length} of {myCheckpoints.length} steps complete
              </span>
              <span className="progress-bar-pct">{completion}%</span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill-linear" style={{ width: `${completion}%` }}></div>
            </div>
          </div>
          <div className={`risk-indicator risk-${riskAssessment.overallRisk}`}>
            {riskAssessment.overallRisk === 'low' ? 'On Track' :
             riskAssessment.overallRisk === 'medium' ? 'Needs Attention' :
             'Action Required'}
          </div>
        </div>

      {/* Section Header */}
      <div className="dashboard-tabs">
        <button className="tab active">Compliance Tracker</button>
      </div>

      {/* Checkpoints Tab */}
      {activeTab === 'checkpoints' && (
        <div className="checkpoints-section">

          {categories.map(category => (
            <div key={category} className="checkpoint-category">
              <h3 className="category-title">{category}</h3>
              <div className="checkpoint-list">
                {myCheckpoints
                  .filter(c => c.category === category)
                  .map(checkpoint => (
                    <div
                      key={checkpoint.id}
                      className={`checkpoint-item ${checkpoint.completed ? 'completed' : 'pending'} ${expandedCheckpoint === checkpoint.id ? 'expanded' : ''}`}
                    >
                      <div className="checkpoint-main">
                        <div className="checkpoint-status-icon">
                          {checkpoint.completed ? (
                            <span className="status-complete">{'\u2713'}</span>
                          ) : (
                            <span className="status-pending">{'\u25CB'}</span>
                          )}
                        </div>
                        <div className="checkpoint-content">
                          <span className="checkpoint-label">{checkpoint.label}</span>
                          {checkpoint.frameworks && checkpoint.frameworks.length > 0 && (
                            <div className="framework-badges">
                              {checkpoint.frameworks.map(fw => (
                                <span key={fw} className={`framework-badge fw-${fw.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>{fw}</span>
                              ))}
                            </div>
                          )}
                          {checkpoint.completed ? (
                            <span className="checkpoint-date completed-date">
                              Completed {new Date(checkpoint.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                          ) : (
                            <span className="checkpoint-date pending-date">
                              Pending
                            </span>
                          )}
                        </div>
                        {(role === 'student' || !checkpoint.what) ? null : (
                          <button
                            className="help-btn"
                            onClick={() => setExpandedCheckpoint(expandedCheckpoint === checkpoint.id ? null : checkpoint.id)}
                            title="Learn more about this checkpoint"
                          >
                            {expandedCheckpoint === checkpoint.id ? 'Hide' : 'Info'}
                          </button>
                        )}
                        {role === 'student' && (
                          <button
                            className="help-btn always-visible"
                            onClick={() => setExpandedCheckpoint(expandedCheckpoint === checkpoint.id ? null : checkpoint.id)}
                            title="Learn what this means"
                          >
                            {expandedCheckpoint === checkpoint.id ? 'Hide' : 'Guide'}
                          </button>
                        )}
                        {role !== 'compliance' && SCANNABLE_CHECKPOINTS.includes(checkpoint.id) && !checkpoint.completed && (
                          <button
                            className="log-btn scan"
                            onClick={() => setScanCheckpointId(checkpoint.id)}
                            title="Auto-verify this checkpoint"
                          >
                            Verify
                          </button>
                        )}
                        {role !== 'compliance' && !checkpoint.completed && (
                          <button
                            className="log-btn primary"
                            onClick={() => setLogCheckpointId(checkpoint.id)}
                            title="Log completion"
                          >
                            Log
                          </button>
                        )}
                        {role !== 'compliance' && checkpoint.completed && (
                          <>
                            <button
                              className="log-btn secondary"
                              onClick={() => setLogCheckpointId(checkpoint.id)}
                              title="Add note"
                            >
                              Add Note
                            </button>
                            <button
                              className="log-btn undo"
                              onClick={() => handleCheckpointToggle(checkpoint.id)}
                              disabled={saving}
                              title="Reopen"
                            >
                              Reopen
                            </button>
                          </>
                        )}
                        {role === 'compliance' && (
                          <span className="compliance-status-label">
                            {checkpoint.completed ? 'Documented' : 'Pending'}
                          </span>
                        )}
                      </div>
                      {expandedCheckpoint === checkpoint.id && (
                        <div className="checkpoint-expanded">
                          {checkpoint.what && (
                            <div className="checkpoint-help">
                              <div className="help-section">
                                <strong>What:</strong>
                                <p>{checkpoint.what}</p>
                              </div>
                              <div className="help-section">
                                <strong>Why it matters:</strong>
                                <p>{checkpoint.why}</p>
                              </div>
                              <div className="help-section">
                                <strong>How to complete:</strong>
                                <p>{checkpoint.how}</p>
                              </div>
                            </div>
                          )}
                          {/* Inline decisions for this checkpoint */}
                          {(() => {
                            const cpDecisions = (project.decisions || []).filter(d => d.checkpoint === checkpoint.id);
                            if (cpDecisions.length === 0) return null;
                            return (
                              <div className="inline-decisions">
                                <div className="inline-decisions-label">Audit Trail ({cpDecisions.length})</div>
                                {cpDecisions.map(d => (
                                  <div key={d.id} className="inline-decision-item">
                                    <div className="inline-decision-date">{new Date(d.loggedAt).toLocaleDateString()}</div>
                                    <div className="inline-decision-body">
                                      <div className="inline-decision-desc">{d.description}</div>
                                      {d.toolUsed && <div className="inline-decision-tool">Tool: {d.toolUsed.name}</div>}
                                      {d.notes && <div className="inline-decision-notes">{d.notes}</div>}
                                      {d.proofValue && (
                                        <div className="inline-decision-proof">
                                          {d.proofType === 'url'
                                            ? <a href={d.proofValue} target="_blank" rel="noopener noreferrer">{d.proofValue}</a>
                                            : <span>File: {d.proofValue}</span>}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            );
                          })()}
                          <CheckpointComments projectId={project.id} checkpointId={checkpoint.id} />
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}



      {logCheckpointId && (
        <LogDecisionModal
          checkpointId={logCheckpointId}
          checkpointLabel={project.checkpoints?.find(c => c.id === logCheckpointId)?.label}
          availableTools={availableTools}
          saving={saving}
          onClose={() => setLogCheckpointId(null)}
          onSave={handleLogDecision}
        />
      )}

      {scanCheckpointId && (
        <VerificationScanModal
          checkpointId={scanCheckpointId}
          onClose={() => setScanCheckpointId(null)}
        />
      )}

      {showDisclosure && (
        <DisclosureModal
          initialText={generateDisclosure(project)}
          filename={`${project.name.replace(/\s+/g, '_')}_Disclosure.txt`}
          onClose={() => setShowDisclosure(false)}
          onCopied={() => showToast('Copied to clipboard')}
        />
      )}

      {showEditModal && (
        <EditActivityModal
          project={project}
          role={role}
          onClose={() => setShowEditModal(false)}
          onSaved={(updated) => {
            setProject(updated);
            if (onProjectUpdated) onProjectUpdated(updated);
            setShowEditModal(false);
            showToast('Activity updated');
          }}
        />
      )}
      </div>
    </div>
  );
}

export default ProjectDashboard;
