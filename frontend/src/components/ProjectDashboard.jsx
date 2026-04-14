import { useState, useEffect } from 'react';
import html2pdf from 'html2pdf.js';
import { toggleCheckpoint, logDecision, fetchProject, updateProject, fetchTools, scanFileForPII, classifyData } from '../services/api';
import CheckpointComments from './CheckpointComments';
import UserMenu from './UserMenu';

function ProjectDashboard({ project: initialProject, user, role, onBack, onLogout, onProjectUpdated, onViewToolRegistry, onViewDashboard }) {
  const [project, setProject] = useState(initialProject);
  const [activeTab, setActiveTab] = useState('checkpoints');
  const [showLogModal, setShowLogModal] = useState(false);
  const [newDecision, setNewDecision] = useState({ checkpoint: '', description: '', notes: '', proofType: '', proofValue: '', toolUsedId: '' });
  const [expandedCheckpoint, setExpandedCheckpoint] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [showScanModal, setShowScanModal] = useState(null);
  const [classifyText, setClassifyText] = useState('');
  const [classifyResult, setClassifyResult] = useState(null);

  const SCANNABLE_CHECKPOINTS = ['data_deidentified', 'ferpa_compliance', 'data_classification'];

  async function handleFileScan(file, checkpointId) {
    setScanning(true);
    setScanResult(null);
    try {
      const scanType = checkpointId === 'ferpa_compliance' ? 'ferpa' : 'pii';
      const result = await scanFileForPII(file, scanType);
      setScanResult(result);
    } catch (err) {
      setScanResult({ error: 'Scan failed. Please try again.' });
    } finally {
      setScanning(false);
    }
  }

  async function handleClassify() {
    if (!classifyText.trim()) return;
    setScanning(true);
    setClassifyResult(null);
    try {
      const result = await classifyData(classifyText);
      setClassifyResult(result);
    } catch (err) {
      setClassifyResult({ error: 'Classification failed.' });
    } finally {
      setScanning(false);
    }
  }
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description || '');
  const [editCollaboratorEmail, setEditCollaboratorEmail] = useState('');
  const [editError, setEditError] = useState('');
  const [editRiskContext, setEditRiskContext] = useState(project.riskContext || {});
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

  function getExampleForCheckpoint(checkpointId) {
    const examples = {
      'irb': 'e.g., IRB protocol #2024-0123 approved on 01/15/2024 includes AI analysis methods',
      'data_classification': 'e.g., Data classified as Confidential - contains de-identified health records',
      'ai_disclosure': 'e.g., Will include AI disclosure in methods section per journal requirements',
      'data_deidentified': 'e.g., Removed all 18 HIPAA identifiers using Safe Harbor method',
      'data_storage': 'e.g., Data stored on institutional secure server with encryption at rest',
      'bias_audit': 'e.g., Tested model across age groups - no significant performance disparities found',
      'human_review': 'e.g., Two reviewers validate 20% random sample of AI outputs weekly',
      'ai_coding_disclosure': 'e.g., Used GPT-4 for initial theme suggestions, all codes verified by research team',
      'participant_consent': 'e.g., Consent form v2.1 updated to include AI processing disclosure',
      'ai_writing_disclosure': 'e.g., Used Grammarly and ChatGPT for grammar/clarity edits only',
      'grading_fairness': 'e.g., Compared AI grades across demographics - no statistically significant disparities',
      'ferpa_compliance': 'e.g., Confirmed student data processed only on FERPA-compliant institutional systems',
      'grading_transparency': 'e.g., Syllabus updated to disclose AI-assisted grading with opt-out provision',
      'human_override': 'e.g., Students can request manual re-grading within 7 days of grade posting',
      'grading_validation': 'e.g., Instructor reviewed 25% random sample - 96% agreement with AI grades',
      'content_accuracy': 'e.g., All AI-generated lecture materials reviewed by subject matter expert',
      'accessibility_check': 'e.g., Materials tested with screen reader and meet WCAG 2.1 AA standards',
      'ip_review': 'e.g., AI-generated content checked against copyright database - no infringement found',
      'teaching_disclosure': 'e.g., Course syllabus includes AI-generated content disclosure statement',
      'material_review_cycle': 'e.g., Quarterly review scheduled - next review April 2026',
      'decision_impact': 'e.g., Impact assessment completed - affects 500 applicants across 3 programs',
      'appeal_process': 'e.g., Written appeal process published - 30-day review window with human committee',
      'admin_bias_audit': 'e.g., Disparate impact analysis completed - no protected group disadvantaged',
      'data_minimization': 'e.g., Reduced data fields from 45 to 12 essential variables for AI processing',
      'admin_disclosure': 'e.g., Notification sent to all applicants that AI assists in initial screening'
    };
    return examples[checkpointId] || 'e.g., Describe what action was taken';
  }

  async function handleCheckpointToggle(checkpointId) {
    setSaving(true);
    try {
      const result = await toggleCheckpoint(project.id, checkpointId);
      // Update local state
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

  async function handleLogDecision() {
    if (!newDecision.checkpoint || !newDecision.description) return;

    setSaving(true);
    try {
      const result = await logDecision(project.id, {
        checkpoint: newDecision.checkpoint,
        description: newDecision.description,
        notes: newDecision.notes,
        proofType: newDecision.proofType || '',
        proofValue: newDecision.proofValue || '',
        toolUsedId: newDecision.toolUsedId || null,
      });

      // Update local state with the new decision
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

      // Update checkpoint completed status
      const updatedCheckpoints = project.checkpoints.map(cp =>
        cp.id === newDecision.checkpoint
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

      setNewDecision({ checkpoint: '', description: '', notes: '', proofType: '', proofValue: '' });
      setShowLogModal(false);
    } catch (err) {
      console.error('Failed to log decision', err);
      alert('Error saving decision. Please try again.');
    } finally {
      setSaving(false);
    }
  }


  function generateReport(scope = 'full') {
    const roleFilter = scope === 'mine' ? role : null;
    const reportCheckpoints = roleFilter
      ? project.checkpoints.filter(c => c.assignedTo === roleFilter)
      : project.checkpoints;
    const completedCount = reportCheckpoints.filter(c => c.completed).length;
    const totalCount = reportCheckpoints.length;
    const pendingCount = totalCount - completedCount;
    const reportTitle = scope === 'mine' ? 'My Checkpoints Report' : 'Ethics Compliance Report';
    const reportSubtitle = scope === 'mine'
      ? `Showing checkpoints assigned to ${role === 'pi' ? 'Faculty / PI' : 'Student'}`
      : 'Full activity report — all checkpoints across all roles';
    const pct = getCompletionPercentage();
    const risk = getRiskAssessment();
    const decisions = project.decisions || [];

    const useCaseLabels = {
      'data_analysis': 'Quantitative Data Analysis',
      'qualitative': 'Qualitative Analysis',
      'ml_model': 'ML / AI Model Development',
      'literature': 'Literature Review & Synthesis',
      'writing': 'Writing & Editing Assistance',
      'grading': 'Student Grading & Assessment',
      'teaching': 'Teaching Material Development',
      'admin': 'Administrative Decision Making',
      'other': 'Other'
    };

    const riskColors = { low: '#16a34a', medium: '#d97706', high: '#dc2626' };
    const riskLabels = {
      low: 'Low Risk — No critical compliance gaps found.',
      medium: 'Medium Risk — Some items need your attention before this project is fully compliant.',
      high: 'High Risk — Critical compliance steps are missing. Please address these urgently.'
    };

    const summaryLine = pct === 100
      ? 'All compliance steps are complete. This project has passed its ethics review.'
      : `This project is ${pct}% compliant. ${pendingCount} item${pendingCount > 1 ? 's' : ''} still need${pendingCount === 1 ? 's' : ''} attention.`;

    const riskLabel = risk.overallRisk.charAt(0).toUpperCase() + risk.overallRisk.slice(1);
    const categories = [...new Set(reportCheckpoints.map(c => c.category))];
    const now = new Date();

    const html = `
    <div style="font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; line-height: 1.45; padding: 0; max-width: 800px; margin: 0 auto;">
      <!-- LETTERHEAD -->
      <div style="border-bottom: 3px solid #006747; padding-bottom: 10px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <div style="font-family: Arial, sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #006747; font-weight: 700;">University of South Florida</div>
            <div style="font-family: Arial, sans-serif; font-size: 9px; color: #666; margin-top: 2px;">Office of Research Compliance</div>
          </div>
          <div style="text-align: right;">
            <div style="font-family: Arial, sans-serif; font-size: 9px; color: #666;">4202 E. Fowler Avenue</div>
            <div style="font-family: Arial, sans-serif; font-size: 9px; color: #666;">Tampa, FL 33620</div>
          </div>
        </div>
      </div>

      <!-- TITLE -->
      <div style="text-align: center; margin-bottom: 10px;">
        <div style="font-size: 17px; font-weight: 700; color: #1a1a1a; margin-bottom: 2px;">${reportTitle}</div>
        <div style="font-size: 11px; color: #555;">Generated ${now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
        <div style="font-size: 10px; color: #888; margin-top: 3px; font-style: italic;">${reportSubtitle}</div>
      </div>

      <!-- ABOUT THIS REPORT -->
      <div style="font-size: 10px; color: #444; line-height: 1.5; margin-bottom: 12px; padding: 6px 10px; border-left: 3px solid #006747; background: #fafafa;">
        This report documents the ethics compliance status for an activity involving the use of artificial intelligence. Produced by RAISE (Responsible AI Standards &amp; Ethics) at the University of South Florida, it includes a summary of the activity, required compliance steps, decisions made, and any outstanding items. Intended for faculty, researchers, students, and compliance officers.
      </div>

      <!-- ACTIVITY INFORMATION TABLE -->
      <div style="margin-bottom: 16px;">
        <div style="font-family: Arial, sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #006747; margin-bottom: 6px;">1. Activity Information</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600; width: 180px;">Activity Name</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${project.name}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Use Case</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${useCaseLabels[project.aiUseCase] || 'Not specified'}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Description</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${project.description || 'None provided'}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Date Created</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${new Date(project.createdAt).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Compliance Status</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${pct}% complete (${completedCount} of ${totalCount} steps)${scope === 'mine' ? ` — ${project.checkpoints.filter(c => c.completed).length}/${project.checkpoints.length} overall` : ''}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Risk Level</td><td style="border: 1px solid #ccc; padding: 6px 10px; color: ${riskColors[risk.overallRisk]}; font-weight: 600;">${riskLabel}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Decisions Logged</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${decisions.length}</td></tr>
        </table>
      </div>

      <!-- COMPLIANCE CHECKLIST TABLE -->
      <div style="margin-bottom: 16px;">
        <div style="font-family: Arial, sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #006747; margin-bottom: 6px;">2. Compliance Checklist</div>
        ${categories.map(category => {
          const catCps = reportCheckpoints.filter(c => c.category === category);
          const catDone = catCps.filter(c => c.completed).length;
          return `
          <div style="font-size: 10px; font-weight: 700; color: #333; margin: 10px 0 3px; text-transform: uppercase;">${category} (${catDone}/${catCps.length})</div>
          <table style="width: 100%; border-collapse: collapse; font-size: 10px; margin-bottom: 2px;">
            <tr style="background: #f5f5f5;">
              <th style="border: 1px solid #ccc; padding: 3px 6px; text-align: left; width: 55%;">Checkpoint</th>
              <th style="border: 1px solid #ccc; padding: 3px 6px; text-align: left; width: 15%;">Assigned To</th>
              <th style="border: 1px solid #ccc; padding: 3px 6px; text-align: center; width: 12%;">Status</th>
              <th style="border: 1px solid #ccc; padding: 3px 6px; text-align: left; width: 18%;">Date</th>
            </tr>
            ${catCps.map(cp => {
              const done = cp.completed;
              const assignedLabel = cp.assignedTo === 'pi' ? 'Faculty / PI' : 'Student';
              return `
            <tr>
              <td style="border: 1px solid #ccc; padding: 3px 6px;">${cp.label}</td>
              <td style="border: 1px solid #ccc; padding: 3px 6px;">${assignedLabel}</td>
              <td style="border: 1px solid #ccc; padding: 3px 6px; text-align: center; font-weight: 600; color: ${done ? '#006747' : '#b91c1c'};">${done ? 'Complete' : 'Pending'}</td>
              <td style="border: 1px solid #ccc; padding: 3px 6px;">${done && cp.completedAt ? new Date(cp.completedAt).toLocaleDateString() : '—'}</td>
            </tr>`;
            }).join('')}
          </table>`;
        }).join('')}
      </div>

      <!-- DECISION AUDIT LOG -->
      <div style="margin-bottom: 16px;">
        <div style="font-family: Arial, sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #006747; margin-bottom: 6px;">3. Decision Audit Trail</div>
        ${decisions.length === 0
          ? `<p style="font-size: 12px; color: #666; font-style: italic;">No decisions have been logged for this activity.</p>`
          : `<table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr style="background: #f5f5f5;">
              <th style="border: 1px solid #ccc; padding: 5px 8px; text-align: left; width: 15%;">Date</th>
              <th style="border: 1px solid #ccc; padding: 5px 8px; text-align: left; width: 25%;">Checkpoint</th>
              <th style="border: 1px solid #ccc; padding: 5px 8px; text-align: left; width: 40%;">Decision</th>
              <th style="border: 1px solid #ccc; padding: 5px 8px; text-align: left; width: 20%;">Evidence</th>
            </tr>
            ${decisions.map(d => {
              const cpLabel = project.checkpoints.find(c => c.id === d.checkpoint)?.label || 'General';
              return `
            <tr>
              <td style="border: 1px solid #ccc; padding: 5px 8px;">${new Date(d.loggedAt).toLocaleDateString()}</td>
              <td style="border: 1px solid #ccc; padding: 5px 8px;">${cpLabel}</td>
              <td style="border: 1px solid #ccc; padding: 5px 8px;">${d.description}${d.notes ? '<br/><em style="color:#666;">Note: ' + d.notes + '</em>' : ''}</td>
              <td style="border: 1px solid #ccc; padding: 5px 8px;">${d.proofValue || '—'}</td>
            </tr>`;
            }).join('')}
          </table>`
        }
      </div>

      <!-- OUTSTANDING ITEMS -->
      ${pendingCount > 0 ? `
      <div style="margin-bottom: 16px; page-break-before: always;">
        <div style="font-family: Arial, sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #006747; margin-bottom: 6px;">4. Outstanding Items</div>
        <p style="font-size: 11px; color: #333; margin-bottom: 6px;">The following ${pendingCount} step${pendingCount > 1 ? 's' : ''} must be completed before this activity is fully compliant:</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
          <tr style="background: #f5f5f5;">
            <th style="border: 1px solid #ccc; padding: 4px 6px; text-align: left; width: 5%;">#</th>
            <th style="border: 1px solid #ccc; padding: 4px 6px; text-align: left; width: 28%;">Checkpoint</th>
            <th style="border: 1px solid #ccc; padding: 4px 6px; text-align: left; width: 67%;">How to Complete</th>
          </tr>
          ${reportCheckpoints.filter(c => !c.completed).map((cp, i) => `
          <tr>
            <td style="border: 1px solid #ccc; padding: 4px 6px;">${i + 1}</td>
            <td style="border: 1px solid #ccc; padding: 4px 6px; font-weight: 600;">${cp.label}</td>
            <td style="border: 1px solid #ccc; padding: 4px 6px;">${cp.how || '—'}</td>
          </tr>`).join('')}
        </table>
      </div>` : ''}

      <!-- FOOTER -->
      <div style="border-top: 2px solid #006747; padding-top: 10px; margin-top: 16px; page-break-inside: avoid;">
        <div style="font-family: Arial, sans-serif; font-size: 9px; color: #888; text-align: center; line-height: 1.6;">
          RAISE &mdash; Responsible AI Standards &amp; Ethics<br/>
          University of South Florida &nbsp;&bull;&nbsp; 4202 E. Fowler Avenue, Tampa, FL 33620<br/>
          Report generated on ${now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} at ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}<br/>
          For compliance questions, contact your IRB office.
        </div>
      </div>
    </div>`;

    const container = document.createElement('div');
    container.innerHTML = html;
    document.body.appendChild(container);

    html2pdf().set({
      margin: [0.5, 0.4, 0.6, 0.4],
      filename: `${project.name.replace(/\s+/g, '_')}_Compliance_Report.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'] }
    }).from(container).save().then(() => {
      document.body.removeChild(container);
    });
  }

  function getCompletionPercentage() {
    if (!project.checkpoints || project.checkpoints.length === 0) return 0;
    const completed = project.checkpoints.filter(c => c.completed).length;
    return Math.round((completed / project.checkpoints.length) * 100);
  }

  function showToast(message) {
    setToast(message);
    setTimeout(() => setToast(''), 2500);
  }

  // Filter checkpoints based on role
  const getMyCheckpoints = () => {
    if (role === 'compliance') {
      return project.checkpoints || [];
    }
    return project.checkpoints?.filter(c => c.assignedTo === role) || [];
  };

  const myCheckpoints = getMyCheckpoints();
  const allCheckpoints = project.checkpoints || [];
  const categories = [...new Set(myCheckpoints.map(c => c.category))];

  const getMyCompletionPercentage = () => {
    if (myCheckpoints.length === 0) return 0;
    const completed = myCheckpoints.filter(c => c.completed).length;
    return Math.round((completed / myCheckpoints.length) * 100);
  };

  const completion = role === 'compliance' ? getCompletionPercentage() : getMyCompletionPercentage();

  function getRiskAssessment() {
    const risks = [];
    const checkpointsToCheck = role === 'compliance' ? allCheckpoints : myCheckpoints;
    const incompleteCheckpoints = checkpointsToCheck.filter(c => !c.completed);

    const criticalCheckpoints = ['irb', 'data_deidentified', 'participant_consent', 'ferpa_compliance', 'grading_fairness', 'decision_impact'];
    const incompleteCritical = incompleteCheckpoints.filter(c => criticalCheckpoints.includes(c.id));

    if (incompleteCritical.length > 0) {
      risks.push({
        level: 'high',
        message: `${incompleteCritical.length} critical compliance item(s) pending`,
        items: incompleteCritical.map(c => c.label)
      });
    }

    const mediumCheckpoints = ['bias_audit', 'human_review', 'ai_disclosure', 'human_override', 'admin_bias_audit', 'content_accuracy'];
    const incompleteMedium = incompleteCheckpoints.filter(c => mediumCheckpoints.includes(c.id));

    if (incompleteMedium.length > 0) {
      risks.push({
        level: 'medium',
        message: `${incompleteMedium.length} transparency/quality item(s) pending`,
        items: incompleteMedium.map(c => c.label)
      });
    }

    let overallRisk = 'low';
    if (risks.some(r => r.level === 'high')) {
      overallRisk = 'high';
    } else if (risks.some(r => r.level === 'medium') || completion < 50) {
      overallRisk = 'medium';
    }

    return { overallRisk, risks, completion };
  }

  const riskAssessment = getRiskAssessment();

  const useCaseLabelsShort = {
    'data_analysis': 'Data Analysis',
    'qualitative': 'Qualitative Analysis',
    'ml_model': 'ML / Model Development',
    'literature': 'Literature Review',
    'writing': 'Writing Assistance',
    'grading': 'Grading & Assessment',
    'teaching': 'Teaching Materials',
    'admin': 'Administrative',
    'other': 'Other',
  };

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
              <span>{useCaseLabelsShort[project.aiUseCase] || project.aiUseCase}</span>
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
              return <button className="pd-export-btn" onClick={() => generateReport('full')}>Export Report</button>;
            }
            return (
              <div className="export-dropdown-wrap">
                <button className="pd-export-btn" onClick={() => setShowExportMenu(!showExportMenu)}>Export Report ▾</button>
                {showExportMenu && (
                  <div className="export-dropdown">
                    <button onClick={() => { generateReport('mine'); setShowExportMenu(false); }}>My Checkpoints</button>
                    <button onClick={() => { generateReport('full'); setShowExportMenu(false); }}>Full Activity Report</button>
                  </div>
                )}
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
                            onClick={() => { setShowScanModal(checkpoint.id); setScanResult(null); setClassifyResult(null); setClassifyText(''); }}
                            title="Auto-verify this checkpoint"
                          >
                            Verify
                          </button>
                        )}
                        {role !== 'compliance' && !checkpoint.completed && (
                          <button
                            className="log-btn primary"
                            onClick={() => {
                              setNewDecision({ ...newDecision, checkpoint: checkpoint.id });
                              setShowLogModal(true);
                            }}
                            title="Log completion"
                          >
                            Log
                          </button>
                        )}
                        {role !== 'compliance' && checkpoint.completed && (
                          <>
                            <button
                              className="log-btn secondary"
                              onClick={() => {
                                setNewDecision({ ...newDecision, checkpoint: checkpoint.id });
                                setShowLogModal(true);
                              }}
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



      {/* Document Checkpoint Modal */}
      {showLogModal && (
        <div className="modal-overlay" onClick={() => setShowLogModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Document Checkpoint</h2>
            <p className="modal-subtitle">
              {project.checkpoints?.find(c => c.id === newDecision.checkpoint)?.label}
            </p>

            <div className="form-group">
              <label>What was done? *</label>
              <input
                type="text"
                value={newDecision.description}
                onChange={(e) => setNewDecision({ ...newDecision, description: e.target.value })}
                placeholder={getExampleForCheckpoint(newDecision.checkpoint)}
              />
            </div>

            {availableTools.length > 0 && (
              <div className="form-group">
                <label>Tool used (optional)</label>
                <select
                  value={newDecision.toolUsedId}
                  onChange={(e) => setNewDecision({ ...newDecision, toolUsedId: e.target.value })}
                >
                  <option value="">None</option>
                  {availableTools.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Additional Notes (optional)</label>
              <textarea
                value={newDecision.notes}
                onChange={(e) => setNewDecision({ ...newDecision, notes: e.target.value })}
                placeholder="Any additional context, reference numbers, dates..."
                rows={2}
              />
            </div>

            <div className="form-group">
              <label>Attach Evidence (optional)</label>
              <select
                value={newDecision.proofType}
                onChange={(e) => setNewDecision({ ...newDecision, proofType: e.target.value, proofValue: '' })}
                className="proof-type-select"
              >
                <option value="">No attachment</option>
                <option value="url">URL / Link</option>
                <option value="file">File Reference</option>
              </select>
            </div>

            {newDecision.proofType === 'url' && (
              <div className="form-group">
                <label>URL</label>
                <input
                  type="url"
                  value={newDecision.proofValue}
                  onChange={(e) => setNewDecision({ ...newDecision, proofValue: e.target.value })}
                  placeholder="https://example.com/irb-approval.pdf"
                />
                <p className="form-hint">Link to document, approval letter, or supporting evidence</p>
              </div>
            )}

            {newDecision.proofType === 'file' && (
              <div className="form-group">
                <label>File Reference</label>
                <input
                  type="text"
                  value={newDecision.proofValue}
                  onChange={(e) => setNewDecision({ ...newDecision, proofValue: e.target.value })}
                  placeholder="IRB_Approval_2024.pdf (in project folder)"
                />
                <p className="form-hint">Name and location of the file for reference</p>
              </div>
            )}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowLogModal(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleLogDecision}
                disabled={!newDecision.checkpoint || !newDecision.description || saving}
              >
                {saving ? 'Saving...' : 'Save Documentation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Verification Scan Modal */}
      {showScanModal && (
        <div className="modal-overlay" onClick={() => setShowScanModal(null)}>
          <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
            {showScanModal === 'data_classification' ? (
              <>
                <h2>Data Classification Check</h2>
                <p className="modal-subtitle">Describe your data and we will suggest a classification level.</p>
                <div className="form-group">
                  <label>Describe the data you are working with</label>
                  <textarea
                    value={classifyText}
                    onChange={(e) => setClassifyText(e.target.value)}
                    placeholder="e.g., Student enrollment records including names, majors, and GPA from Fall 2025..."
                    rows={4}
                  />
                </div>
                {classifyResult && !classifyResult.error && (
                  <div className={`scan-result ${classifyResult.suggestedLevel === 'restricted' || classifyResult.suggestedLevel === 'confidential' ? 'scan-fail' : 'scan-pass'}`}>
                    <div className="scan-verdict-label">Suggested Classification</div>
                    <div className="scan-verdict-level">{classifyResult.suggestedLevel.toUpperCase()}</div>
                    <p className="scan-verdict-text">{classifyResult.reasoning}</p>
                  </div>
                )}
                {classifyResult?.error && (
                  <div className="scan-result scan-fail"><p>{classifyResult.error}</p></div>
                )}
                <div className="modal-actions">
                  <button className="btn-secondary" onClick={() => setShowScanModal(null)}>Close</button>
                  <button className="btn-primary" onClick={handleClassify} disabled={!classifyText.trim() || scanning}>
                    {scanning ? 'Analyzing...' : 'Analyze'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2>{showScanModal === 'ferpa_compliance' ? 'FERPA Compliance Check' : 'PII Detection Scan'}</h2>
                <p className="modal-subtitle">
                  {showScanModal === 'ferpa_compliance'
                    ? 'Upload a CSV of your student data to check for FERPA-protected fields.'
                    : 'Upload a CSV of your dataset to scan for personally identifiable information.'}
                </p>
                <div className="form-group">
                  <label>Upload CSV file (max 10MB)</label>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) handleFileScan(file, showScanModal);
                    }}
                  />
                </div>
                {scanning && <div className="scan-loading">Scanning file for identifiable data...</div>}
                {scanResult && !scanResult.error && (
                  <div className={`scan-result ${scanResult.hasPII ? 'scan-fail' : 'scan-pass'}`}>
                    <div className="scan-verdict-label">{scanResult.hasPII ? 'Issues Found' : 'No Issues Found'}</div>
                    <p className="scan-verdict-text">{scanResult.verdict}</p>
                    <div className="scan-stats">
                      <span>{scanResult.totalColumns} columns scanned</span>
                      <span>{scanResult.rowsScanned} rows checked</span>
                      <span>{scanResult.flaggedColumns} column{scanResult.flaggedColumns !== 1 ? 's' : ''} flagged</span>
                    </div>
                    {scanResult.findings.length > 0 && (
                      <div className="scan-findings">
                        <div className="scan-findings-label">Findings:</div>
                        {scanResult.findings.map((f, i) => (
                          <div key={i} className={`scan-finding ${f.severity}`}>
                            <span className="finding-type">{f.type.replace(/_/g, ' ')}</span>
                            <span className="finding-msg">{f.message}</span>
                            {f.sample && <span className="finding-sample">Sample: {f.sample}</span>}
                          </div>
                        ))}
                      </div>
                    )}
                    {showScanModal === 'ferpa_compliance' && scanResult.ferpaSpecific && (
                      <div className="scan-ferpa-extra">
                        <div className="scan-verdict-label" style={{marginTop: '12px'}}>
                          {scanResult.ferpaSpecific.hasFerpaData ? 'FERPA-Protected Data Detected' : 'No FERPA-Specific Fields Found'}
                        </div>
                        <p className="scan-verdict-text">{scanResult.ferpaSpecific.verdict}</p>
                      </div>
                    )}
                  </div>
                )}
                {scanResult?.error && (
                  <div className="scan-result scan-fail"><p>{scanResult.error}</p></div>
                )}
                <div className="modal-actions">
                  <button className="btn-secondary" onClick={() => setShowScanModal(null)}>Close</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Edit Activity Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Edit Activity</h2>
            <div className="form-group">
              <label>Activity Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={3}
              />
            </div>
            <div className="form-group">
              <label>Use Case</label>
              <input type="text" value={useCaseLabelsShort[project.aiUseCase] || project.aiUseCase} disabled style={{background: '#f1f5f9', color: '#64748b'}} />
              <p className="form-hint">Use case cannot be changed after creation as it determines the compliance checkpoints</p>
            </div>
            <div className="form-group">
              <label>{role === 'pi' ? 'Student Collaborator Email' : 'Faculty Advisor Email'}</label>
              <input
                type="email"
                value={editCollaboratorEmail}
                onChange={(e) => setEditCollaboratorEmail(e.target.value)}
                placeholder={role === 'pi' ? 'e.g., student@usf.edu' : 'e.g., advisor@usf.edu'}
              />
              {role === 'pi' && project.studentCollaborator && (
                <p className="form-hint">Currently shared with: {project.studentCollaborator.name} ({project.studentCollaborator.email})</p>
              )}
              {role !== 'pi' && project.facultyAdvisor && (
                <p className="form-hint">Currently shared with: {project.facultyAdvisor.name} ({project.facultyAdvisor.email})</p>
              )}
              {!project.facultyAdvisor && role !== 'pi' && (
                <p className="form-hint">Your faculty advisor will see this activity and complete checkpoints assigned to them</p>
              )}
            </div>
            <div className="risk-questions">
              <div className="risk-questions-label">Risk assessment</div>
              <p className="risk-questions-hint">Updating these may add new compliance steps. Existing completed steps are never removed.</p>
              <label className="risk-question">
                <input
                  type="checkbox"
                  checked={editRiskContext.involves_student_data || false}
                  onChange={(e) => setEditRiskContext({ ...editRiskContext, involves_student_data: e.target.checked })}
                />
                <div>
                  <span className="rq-text">This involves student records or data</span>
                  <span className="rq-hint">Names, IDs, grades, submissions, enrollment info</span>
                </div>
              </label>
              <label className="risk-question">
                <input
                  type="checkbox"
                  checked={editRiskContext.data_leaves_institution || false}
                  onChange={(e) => setEditRiskContext({ ...editRiskContext, data_leaves_institution: e.target.checked })}
                />
                <div>
                  <span className="rq-text">Data is sent to an external service</span>
                  <span className="rq-hint">Cloud tools like ChatGPT, Copilot, or any non-institutional system</span>
                </div>
              </label>
              <label className="risk-question">
                <input
                  type="checkbox"
                  checked={editRiskContext.affects_decisions || false}
                  onChange={(e) => setEditRiskContext({ ...editRiskContext, affects_decisions: e.target.checked })}
                />
                <div>
                  <span className="rq-text">This affects grades, admissions, or evaluations</span>
                  <span className="rq-hint">Any outcome that directly impacts a person's academic record</span>
                </div>
              </label>
              <label className="risk-question">
                <input
                  type="checkbox"
                  checked={editRiskContext.involves_human_subjects || false}
                  onChange={(e) => setEditRiskContext({ ...editRiskContext, involves_human_subjects: e.target.checked })}
                />
                <div>
                  <span className="rq-text">This is part of a human subjects research study</span>
                  <span className="rq-hint">Requires or may require IRB approval</span>
                </div>
              </label>
            </div>

            {editError && <p className="error-text">{editError}</p>}
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => { setShowEditModal(false); setEditError(''); }}>Cancel</button>
              <button className="btn-primary" onClick={async () => {
                setEditError('');
                try {
                  const updateData = { name: editName.trim(), description: editDescription, risk_context: editRiskContext };
                  if (editCollaboratorEmail.trim()) {
                    const field = role === 'pi' ? 'student_collaborator_email' : 'faculty_advisor_email';
                    updateData[field] = editCollaboratorEmail.trim();
                  }
                  const updated = await updateProject(project.id, updateData);
                  setProject(updated);
                  if (onProjectUpdated) onProjectUpdated(updated);
                  setShowEditModal(false);
                  setEditCollaboratorEmail('');
                  showToast('Activity updated');
                } catch (err) {
                  setEditError(err.response?.data?.error || 'Failed to update');
                }
              }} disabled={!editName.trim()}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

export default ProjectDashboard;
