import { useState, useEffect } from 'react';
import { toggleCheckpoint, logDecision, fetchTools } from '../services/api';
import UserMenu from './UserMenu';
import LogDecisionModal from './modals/LogDecisionModal';
import VerificationScanModal from './modals/VerificationScanModal';
import DisclosureModal from './modals/DisclosureModal';
import EditActivityModal from './modals/EditActivityModal';
import DashboardHeader from './dashboard/DashboardHeader';
import ProgressOverview from './dashboard/ProgressOverview';
import CheckpointItem from './dashboard/CheckpointItem';
import { getCompletionPercentage, getRiskAssessment } from '../utils/risk';
import { generateDisclosure } from '../utils/disclosure';
import { generateComplianceReport } from '../utils/complianceReport';

function ProjectDashboard({ project: initialProject, user, role, onBack, onLogout, onProjectUpdated, onViewToolRegistry, onViewDashboard }) {
  const [project, setProject] = useState(initialProject);
  const [expandedCheckpoint, setExpandedCheckpoint] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  const [logCheckpointId, setLogCheckpointId] = useState(null);
  const [scanCheckpointId, setScanCheckpointId] = useState(null);
  const [showDisclosure, setShowDisclosure] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);

  useEffect(() => {
    fetchTools().then(setAvailableTools).catch(() => {});
  }, []);

  function showToast(message) {
    setToast(message);
    setTimeout(() => setToast(''), 2500);
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

  function toggleExpanded(checkpointId) {
    setExpandedCheckpoint(prev => (prev === checkpointId ? null : checkpointId));
  }

  return (
    <div className="project-dashboard">
      {toast && <div className="toast-notification">{toast}</div>}

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

      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
          <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Library</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      <div className="pd-content">
        <DashboardHeader
          project={project}
          onEdit={() => setShowEditModal(true)}
          onDisclosure={() => setShowDisclosure(true)}
          onExport={handleExportReport}
        />

        <ProgressOverview
          completed={myCheckpoints.filter(c => c.completed).length}
          total={myCheckpoints.length}
          completion={completion}
          riskLevel={riskAssessment.overallRisk}
        />

        <div className="dashboard-tabs">
          <button className="tab active">Compliance Tracker</button>
        </div>

        <div className="checkpoints-section">
          {categories.map(category => (
            <div key={category} className="checkpoint-category">
              <h3 className="category-title">{category}</h3>
              <div className="checkpoint-list">
                {myCheckpoints
                  .filter(c => c.category === category)
                  .map(checkpoint => (
                    <CheckpointItem
                      key={checkpoint.id}
                      checkpoint={checkpoint}
                      role={role}
                      saving={saving}
                      expanded={expandedCheckpoint === checkpoint.id}
                      decisions={(project.decisions || []).filter(d => d.checkpoint === checkpoint.id)}
                      projectId={project.id}
                      onToggleExpanded={() => toggleExpanded(checkpoint.id)}
                      onLog={() => setLogCheckpointId(checkpoint.id)}
                      onVerify={() => setScanCheckpointId(checkpoint.id)}
                      onReopen={() => handleCheckpointToggle(checkpoint.id)}
                    />
                  ))}
              </div>
            </div>
          ))}
        </div>

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
