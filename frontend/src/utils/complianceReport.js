import html2pdf from 'html2pdf.js';
import { USE_CASE_LABELS_LONG } from '../constants/useCases';

const RISK_COLORS = { low: '#16a34a', medium: '#d97706', high: '#dc2626' };

function buildReportHTML({ project, role, scope, completion, riskAssessment }) {
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
  const decisions = project.decisions || [];

  const riskLabel = riskAssessment.overallRisk.charAt(0).toUpperCase() + riskAssessment.overallRisk.slice(1);
  const categories = [...new Set(reportCheckpoints.map(c => c.category))];
  const now = new Date();

  const overallCompletedCount = project.checkpoints.filter(c => c.completed).length;
  const overallTotalCount = project.checkpoints.length;
  const overallNote = scope === 'mine' ? ` — ${overallCompletedCount}/${overallTotalCount} overall` : '';

  return `
    <div style="font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; line-height: 1.45; padding: 0; max-width: 800px; margin: 0 auto;">
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

      <div style="text-align: center; margin-bottom: 10px;">
        <div style="font-size: 17px; font-weight: 700; color: #1a1a1a; margin-bottom: 2px;">${reportTitle}</div>
        <div style="font-size: 11px; color: #555;">Generated ${now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
        <div style="font-size: 10px; color: #888; margin-top: 3px; font-style: italic;">${reportSubtitle}</div>
      </div>

      <div style="font-size: 10px; color: #444; line-height: 1.5; margin-bottom: 12px; padding: 6px 10px; border-left: 3px solid #006747; background: #fafafa;">
        This report documents the ethics compliance status for an activity involving the use of artificial intelligence. Produced by RAISE (Responsible AI Standards &amp; Ethics) at the University of South Florida, it includes a summary of the activity, required compliance steps, decisions made, and any outstanding items. Intended for faculty, researchers, students, and compliance officers.
      </div>

      <div style="margin-bottom: 16px;">
        <div style="font-family: Arial, sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #006747; margin-bottom: 6px;">1. Activity Information</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600; width: 180px;">Activity Name</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${project.name}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Use Case</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${USE_CASE_LABELS_LONG[project.aiUseCase] || 'Not specified'}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Description</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${project.description || 'None provided'}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Date Created</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${new Date(project.createdAt).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Compliance Status</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${completion}% complete (${completedCount} of ${totalCount} steps)${overallNote}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Risk Level</td><td style="border: 1px solid #ccc; padding: 6px 10px; color: ${RISK_COLORS[riskAssessment.overallRisk]}; font-weight: 600;">${riskLabel}</td></tr>
          <tr><td style="border: 1px solid #ccc; padding: 6px 10px; background: #f5f5f5; font-weight: 600;">Decisions Logged</td><td style="border: 1px solid #ccc; padding: 6px 10px;">${decisions.length}</td></tr>
        </table>
      </div>

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

      <div style="border-top: 2px solid #006747; padding-top: 10px; margin-top: 16px; page-break-inside: avoid;">
        <div style="font-family: Arial, sans-serif; font-size: 9px; color: #888; text-align: center; line-height: 1.6;">
          RAISE &mdash; Responsible AI Standards &amp; Ethics<br/>
          University of South Florida &nbsp;&bull;&nbsp; 4202 E. Fowler Avenue, Tampa, FL 33620<br/>
          Report generated on ${now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} at ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}<br/>
          For compliance questions, contact your IRB office.
        </div>
      </div>
    </div>`;
}

export function generateComplianceReport({ project, role, scope, completion, riskAssessment }) {
  const html = buildReportHTML({ project, role, scope, completion, riskAssessment });
  const container = document.createElement('div');
  container.innerHTML = html;
  document.body.appendChild(container);

  html2pdf().set({
    margin: [0.5, 0.4, 0.6, 0.4],
    filename: `${project.name.replace(/\s+/g, '_')}_Compliance_Report.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
    pagebreak: { mode: ['css', 'legacy'] },
  }).from(container).save().then(() => {
    document.body.removeChild(container);
  });
}
