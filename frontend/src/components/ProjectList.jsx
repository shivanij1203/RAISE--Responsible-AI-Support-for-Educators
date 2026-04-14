import { useState, useEffect } from 'react';
import { fetchProjects, createProject, fetchTools, updateProject } from '../services/api';
import UserMenu from './UserMenu';

function ProjectList({ user, role, onSelectProject, onLogout, onViewDashboard, onViewToolRegistry }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', aiUseCase: '', aiToolIds: [], facultyEmail: '', studentEmail: '', riskContext: {} });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [availableTools, setAvailableTools] = useState([]);
  const [editingProject, setEditingProject] = useState(null);
  const [editFacultyEmail, setEditFacultyEmail] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (showCreateModal && availableTools.length === 0) {
      fetchTools().then(setAvailableTools).catch(() => {});
    }
  }, [showCreateModal]);

  async function loadProjects() {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects', err);
      setLoadError('Could not load activities. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProject() {
    if (!newProject.name.trim() || !newProject.aiUseCase) return;

    setCreating(true);
    setCreateError('');
    try {
      const project = await createProject(
        newProject.name,
        newProject.description,
        newProject.aiUseCase,
        newProject.aiToolIds,
        newProject.facultyEmail,
        newProject.studentEmail,
        newProject.riskContext
      );
      setProjects([project, ...projects]);
      setNewProject({ name: '', description: '', aiUseCase: '', aiToolIds: [], facultyEmail: '', studentEmail: '', riskContext: {} });
      setShowCreateModal(false);
      onSelectProject(project);
    } catch (err) {
      console.error('Failed to create project', err);
      setCreateError(err.response?.data?.error || 'Error creating project. Please try again.');
    } finally {
      setCreating(false);
    }
  }

  function getCompletionPercentage(project) {
    if (!project.checkpoints || project.checkpoints.length === 0) return 0;
    const completed = project.checkpoints.filter(c => c.completed).length;
    return Math.round((completed / project.checkpoints.length) * 100);
  }

  function getStatusColor(percentage) {
    if (percentage === 100) return '#006747';
    if (percentage >= 50) return '#006747';
    return '#006747';
  }

  const aiUseCases = [
    { value: 'data_analysis', label: 'Data Analysis (quantitative research)' },
    { value: 'qualitative', label: 'Qualitative Analysis (interviews, text coding)' },
    { value: 'ml_model', label: 'ML / AI Model Development' },
    { value: 'literature', label: 'Literature Review & Synthesis' },
    { value: 'writing', label: 'Writing & Editing Assistance' },
    { value: 'grading', label: 'Student Grading & Assessment' },
    { value: 'teaching', label: 'Teaching Material Development' },
    { value: 'admin', label: 'Administrative Decision Making' },
    { value: 'other', label: 'Other' },
  ];

  if (loading) {
    return (
      <div className="project-list">
        <div className="pl-topbar">
          <div className="pl-topbar-inner">
            <div className="pl-topbar-brand">
              <img src="/usf-logo.svg" alt="USF" className="pl-topbar-logo" />
              <div className="pl-topbar-text">
                <span className="pl-topbar-uni">University of South Florida</span>
                <span className="pl-topbar-app">RAISE Ethics Toolkit</span>
              </div>
            </div>
          </div>
        </div>
        <div className="pl-nav">
          <div className="pl-nav-inner">
            <button className="pl-nav-tab active">My Activities</button>
          </div>
        </div>
        <div className="projects-grid" style={{ padding: '2rem 2.5rem', maxWidth: '1160px', margin: '0 auto' }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="project-card skeleton-card">
              <div className="skeleton-line skeleton-title"></div>
              <div className="skeleton-line skeleton-text"></div>
              <div className="skeleton-line skeleton-bar"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="project-list">
      {/* USF-style top bar */}
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

      {/* Tab navigation */}
      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab active">My Activities</button>
          <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Library</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      {loadError && (
        <div className="error-banner">
          {loadError}
          <button className="error-retry" onClick={loadProjects}>Retry</button>
        </div>
      )}

      {projects.length === 0 ? (
        <div className="empty-state">
          <h2>No Activities Yet</h2>
          <p>Create your first activity to start tracking AI ethics compliance</p>
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            + Create Activity
          </button>
        </div>
      ) : (
        <>
          <div className="projects-grid">
            {projects.map((project) => {
              const completion = getCompletionPercentage(project);
              return (
                <div
                  key={project.id}
                  className="project-card"
                  onClick={() => onSelectProject(project)}
                >
                  <div className="project-header">
                    <h3>{project.name}</h3>
                    <span className="project-date">
                      Created {new Date(project.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="project-description">{project.description || 'No description'}</p>

                  <div className="project-progress">
                    <div className="progress-bar-container">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${completion}%` }}
                      />
                    </div>
                    <span className="progress-text">{completion}% complete</span>
                  </div>

                  <div className="project-stats">
                    <span>{project.checkpoints?.filter(c => c.completed).length || 0}/{project.checkpoints?.length || 0} checkpoints</span>
                    <span>{project.decisions?.length || 0} decisions logged</span>
                  </div>
                  {project.facultyAdvisor && (
                    <div className="project-advisor-tag">
                      Faculty: {project.facultyAdvisor.name}
                    </div>
                  )}
                  {project.studentCollaborator && (
                    <div className="project-advisor-tag">
                      Student: {project.studentCollaborator.name}
                    </div>
                  )}
                  {!project.facultyAdvisor && role === 'student' && project.ownerEmail === user?.email && (
                    <button className="btn-link" onClick={(e) => { e.stopPropagation(); setEditingProject(project); setEditFacultyEmail(''); setEditError(''); }}>
                      + Invite Faculty Advisor
                    </button>
                  )}
                  {!project.studentCollaborator && role === 'pi' && project.ownerEmail === user?.email && (
                    <button className="btn-link" onClick={(e) => { e.stopPropagation(); setEditingProject(project); setEditFacultyEmail(''); setEditError(''); }}>
                      + Invite Student
                    </button>
                  )}
                </div>
              );
            })}

            <div
              className="project-card add-card"
              onClick={() => setShowCreateModal(true)}
            >
              <div className="add-icon">+</div>
              <span>New Activity</span>
            </div>
          </div>
        </>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Activity</h2>

            <div className="form-group">
              <label>Activity Name *</label>
              <input
                type="text"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                placeholder="e.g., AI-Assisted Grading for CSE 101"
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                placeholder="Brief description of the project..."
                rows={3}
              />
            </div>

            <div className="form-group">
              <label>Primary AI Use Case *</label>
              <select
                value={newProject.aiUseCase}
                onChange={(e) => setNewProject({ ...newProject, aiUseCase: e.target.value })}
              >
                <option value="">Select use case...</option>
                {aiUseCases.map((uc) => (
                  <option key={uc.value} value={uc.value}>{uc.label}</option>
                ))}
              </select>
              <p className="form-hint">This determines which compliance checkpoints are relevant</p>
            </div>

            {newProject.aiUseCase && (
              <div className="risk-questions">
                <div className="risk-questions-label">Quick risk assessment</div>
                <p className="risk-questions-hint">These questions determine how many compliance steps are needed. Fewer risks = fewer steps.</p>
                <label className="risk-question">
                  <input
                    type="checkbox"
                    checked={newProject.riskContext?.involves_student_data || false}
                    onChange={(e) => setNewProject({ ...newProject, riskContext: { ...newProject.riskContext, involves_student_data: e.target.checked } })}
                  />
                  <div>
                    <span className="rq-text">This involves student records or data</span>
                    <span className="rq-hint">Names, IDs, grades, submissions, enrollment info</span>
                  </div>
                </label>
                <label className="risk-question">
                  <input
                    type="checkbox"
                    checked={newProject.riskContext?.data_leaves_institution || false}
                    onChange={(e) => setNewProject({ ...newProject, riskContext: { ...newProject.riskContext, data_leaves_institution: e.target.checked } })}
                  />
                  <div>
                    <span className="rq-text">Data is sent to an external service</span>
                    <span className="rq-hint">Cloud tools like ChatGPT, Copilot, or any non-USF system</span>
                  </div>
                </label>
                <label className="risk-question">
                  <input
                    type="checkbox"
                    checked={newProject.riskContext?.affects_decisions || false}
                    onChange={(e) => setNewProject({ ...newProject, riskContext: { ...newProject.riskContext, affects_decisions: e.target.checked } })}
                  />
                  <div>
                    <span className="rq-text">This affects grades, admissions, or evaluations</span>
                    <span className="rq-hint">Any outcome that directly impacts a person's academic record</span>
                  </div>
                </label>
                <label className="risk-question">
                  <input
                    type="checkbox"
                    checked={newProject.riskContext?.involves_human_subjects || false}
                    onChange={(e) => setNewProject({ ...newProject, riskContext: { ...newProject.riskContext, involves_human_subjects: e.target.checked } })}
                  />
                  <div>
                    <span className="rq-text">This is part of a human subjects research study</span>
                    <span className="rq-hint">Requires or may require IRB approval</span>
                  </div>
                </label>
              </div>
            )}

            {role === 'student' && (
              <div className="form-group">
                <label>Faculty Advisor Email *</label>
                <input
                  type="email"
                  value={newProject.facultyEmail}
                  onChange={(e) => setNewProject({ ...newProject, facultyEmail: e.target.value })}
                  placeholder="e.g., advisor@usf.edu"
                />
                <p className="form-hint">Required — your faculty advisor will see this activity and complete checkpoints assigned to them</p>
              </div>
            )}
            {role === 'pi' && (
              <div className="form-group">
                <label>Student Collaborator Email (optional)</label>
                <input
                  type="email"
                  value={newProject.studentEmail}
                  onChange={(e) => setNewProject({ ...newProject, studentEmail: e.target.value })}
                  placeholder="e.g., student@usf.edu"
                />
                <p className="form-hint">The student will be able to see this activity and complete checkpoints assigned to them</p>
              </div>
            )}

            {availableTools.length > 0 && (
              <div className="form-group">
                <label>Tools Used (optional)</label>
                <div className="tool-multiselect">
                  {availableTools.filter(t => t.status !== 'not_recommended').map(tool => (
                    <label key={tool.id} className="tool-option">
                      <input
                        type="checkbox"
                        checked={newProject.aiToolIds.includes(tool.id)}
                        onChange={(e) => {
                          const ids = e.target.checked
                            ? [...newProject.aiToolIds, tool.id]
                            : newProject.aiToolIds.filter(id => id !== tool.id);
                          setNewProject({ ...newProject, aiToolIds: ids });
                        }}
                      />
                      <span className="tool-option-name">{tool.name}</span>
                    </label>
                  ))}
                </div>
                <p className="form-hint">Select tools from the institutional registry</p>
              </div>
            )}

            {createError && <p className="error-text">{createError}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => { setShowCreateModal(false); setCreateError(''); }}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleCreateProject}
                disabled={!newProject.name.trim() || !newProject.aiUseCase || creating || (role === 'student' && !newProject.facultyEmail.trim())}
              >
                {creating ? 'Creating...' : 'Create Activity'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Invite Collaborator Modal */}
      {editingProject && (
        <div className="modal-overlay" onClick={() => setEditingProject(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{role === 'pi' ? 'Invite Student' : 'Invite Faculty Advisor'}</h2>
            <p className="modal-subtitle">{editingProject.name}</p>

            <div className="form-group">
              <label>{role === 'pi' ? 'Student Email' : 'Faculty Advisor Email'}</label>
              <input
                type="email"
                value={editFacultyEmail}
                onChange={(e) => setEditFacultyEmail(e.target.value)}
                placeholder={role === 'pi' ? 'e.g., student@usf.edu' : 'e.g., advisor@usf.edu'}
              />
              <p className="form-hint">
                {role === 'pi'
                  ? 'The student will see this activity and complete checkpoints assigned to them'
                  : 'They will see this activity and complete checkpoints assigned to faculty'}
              </p>
            </div>

            {editError && <p className="error-text">{editError}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setEditingProject(null)}>Cancel</button>
              <button
                className="btn-primary"
                disabled={!editFacultyEmail.trim() || editSaving}
                onClick={async () => {
                  setEditSaving(true);
                  setEditError('');
                  try {
                    const field = role === 'pi' ? 'student_collaborator_email' : 'faculty_advisor_email';
                    const updated = await updateProject(editingProject.id, { [field]: editFacultyEmail.trim() });
                    setProjects(projects.map(p => p.id === updated.id ? updated : p));
                    setEditingProject(null);
                  } catch (err) {
                    setEditError(err.response?.data?.error || 'Could not send invite.');
                  } finally {
                    setEditSaving(false);
                  }
                }}
              >
                {editSaving ? 'Saving...' : 'Invite'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectList;
