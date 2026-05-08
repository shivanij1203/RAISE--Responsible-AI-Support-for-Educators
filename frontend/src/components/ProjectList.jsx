import { useState, useEffect } from 'react';
import { fetchProjects, updateProject } from '../services/api';
import UserMenu from './UserMenu';
import NotificationBell from './NotificationBell';
import QuickAddActivityModal from './modals/QuickAddActivityModal';

function ProjectList({ user, role, onSelectProject, onLogout, onViewDashboard, onViewToolRegistry, onViewUseCases, templateSeed, onTemplateConsumed }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [editFacultyEmail, setEditFacultyEmail] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (templateSeed) {
      setShowQuickAdd(true);
    }
  }, [templateSeed]);

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

  function getCompletionPercentage(project) {
    if (!project.checkpoints || project.checkpoints.length === 0) return 0;
    const completed = project.checkpoints.filter(c => c.completed).length;
    return Math.round((completed / project.checkpoints.length) * 100);
  }

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
            <NotificationBell onOpenProject={(id) => {
              const p = projects.find((x) => x.id === id);
              if (p) onSelectProject(p);
            }} />
            <UserMenu user={user} role={role} onLogout={onLogout} />
          </div>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab active">My Activities</button>
          <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Insights</button>
          <button className="pl-nav-tab" onClick={onViewUseCases}>Use Cases</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      {loadError && (
        <div className="error-banner">
          {loadError}
          <button className="error-retry" onClick={loadProjects}>Retry</button>
        </div>
      )}

      <div className="pl-intro">
        <h2 className="pl-intro-title">My Activities</h2>
        <p className="pl-intro-tagline">
          Use AI responsibly and confidently in your academic work, with RAISE.
        </p>
        <p className="pl-intro-text">
          <strong>What does 'activity' mean here?</strong>
          <br />
          Any time you use an AI tool such as Claude, ChatGPT,
          Copilot, or Gradescope in your academic work, that's an activity. Grading essays, analyzing
          interview data, screening applications, drafting a paper, building course materials. Each
          one carries different compliance requirements under FERPA, IRB rules, the EU AI Act, the
          Colorado AI Act, and USF policy. This page is where you track all of them in one place.
        </p>
        <p className="pl-intro-text">
          <strong>How RAISE helps.</strong> Describe your activity in one sentence and RAISE picks
          the use case, flags the risks, and generates the right compliance checkpoints. Run
          <em> Verify Dataset</em> to auto-complete data checks (personal info, FERPA, fairness
          audit) in one click. Click <em>Pre-fill Checkpoints</em> to draft answers for the rest.
          The completed activity becomes an audit-ready record you can export for IRB review,
          accreditation, or institutional governance.
        </p>
        <p className="pl-intro-text pl-intro-meta">
          For faculty, researchers, graduate students, and administrators using AI in their work.
        </p>
      </div>

      {projects.length === 0 ? (
        <div className="empty-state">
          <h2>No Activities Yet</h2>
          <p>Register your first AI activity by describing it in one sentence.</p>
          <div className="empty-state-actions">
            <button className="btn-primary" onClick={() => setShowQuickAdd(true)}>
              Add a New Activity
            </button>
          </div>
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
              className="project-card add-card add-card-quick"
              onClick={() => setShowQuickAdd(true)}
              title="Add a new activity by describing it in one sentence"
            >
              <div className="add-icon">+</div>
              <span>Add a New Activity</span>
              <span className="add-card-hint">Describe what you'll do with AI</span>
            </div>
          </div>
        </>
      )}

      {showQuickAdd && (
        <QuickAddActivityModal
          initialDescription={templateSeed?.description || ''}
          onClose={() => {
            setShowQuickAdd(false);
            if (onTemplateConsumed) onTemplateConsumed();
          }}
          onCreated={(project) => {
            setProjects([project, ...projects]);
            setShowQuickAdd(false);
            if (onTemplateConsumed) onTemplateConsumed();
            onSelectProject(project);
          }}
        />
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
