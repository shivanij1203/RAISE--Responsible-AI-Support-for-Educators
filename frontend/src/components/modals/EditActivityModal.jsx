import { useState } from 'react';
import { updateProject } from '../../services/api';
import { USE_CASE_LABELS_SHORT } from '../../constants/useCases';

function EditActivityModal({ project, role, onClose, onSaved }) {
  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description || '');
  const [editCollaboratorEmail, setEditCollaboratorEmail] = useState('');
  const [editRiskContext, setEditRiskContext] = useState(project.riskContext || {});
  const [editError, setEditError] = useState('');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    setEditError('');
    try {
      const updateData = {
        name: editName.trim(),
        description: editDescription,
        risk_context: editRiskContext,
      };
      if (editCollaboratorEmail.trim()) {
        const field = role === 'pi' ? 'student_collaborator_email' : 'faculty_advisor_email';
        updateData[field] = editCollaboratorEmail.trim();
      }
      const updated = await updateProject(project.id, updateData);
      onSaved(updated);
    } catch (err) {
      setEditError(err.response?.data?.error || 'Failed to update');
    } finally {
      setSaving(false);
    }
  }

  function toggleRisk(field, checked) {
    setEditRiskContext({ ...editRiskContext, [field]: checked });
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
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
          <input
            type="text"
            value={USE_CASE_LABELS_SHORT[project.aiUseCase] || project.aiUseCase}
            disabled
            style={{ background: '#f1f5f9', color: '#64748b' }}
          />
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
              onChange={(e) => toggleRisk('involves_student_data', e.target.checked)}
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
              onChange={(e) => toggleRisk('data_leaves_institution', e.target.checked)}
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
              onChange={(e) => toggleRisk('affects_decisions', e.target.checked)}
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
              onChange={(e) => toggleRisk('involves_human_subjects', e.target.checked)}
            />
            <div>
              <span className="rq-text">This is part of a human subjects research study</span>
              <span className="rq-hint">Requires or may require IRB approval</span>
            </div>
          </label>
        </div>

        {editError && <p className="error-text">{editError}</p>}
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={!editName.trim() || saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default EditActivityModal;
