import { useState } from 'react';
import { USE_CASE_LABELS_SHORT } from '../../constants/useCases';

function EditIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function DashboardHeader({ project, onEdit, onDisclosure, onExport }) {
  const [showExportMenu, setShowExportMenu] = useState(false);
  const roles = [...new Set(project.checkpoints?.map(c => c.assignedTo) || [])];
  const hasMultipleRoles = roles.length > 1;

  const startedDate = new Date(project.createdAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <header className="pd-header">
      <div className="pd-header-left">
        <h1 className="pd-title">
          {project.name}{' '}
          <button className="edit-name-btn" onClick={onEdit} title="Edit">
            <EditIcon />
          </button>
        </h1>
        <div className="pd-meta">
          <span>{USE_CASE_LABELS_SHORT[project.aiUseCase] || project.aiUseCase}</span>
          <span className="pd-meta-sep">&middot;</span>
          <span>Started {startedDate}</span>
        </div>
        {project.description && <p className="pd-description">{project.description}</p>}
      </div>
      <div className="pd-header-actions">
        <button className="pd-disclosure-btn" onClick={onDisclosure}>Disclosure</button>
        {hasMultipleRoles ? (
          <div className="export-dropdown-wrap">
            <button className="pd-export-btn" onClick={() => setShowExportMenu(!showExportMenu)}>
              Export Report ▾
            </button>
            {showExportMenu && (
              <div className="export-dropdown">
                <button onClick={() => { onExport('mine'); setShowExportMenu(false); }}>My Checkpoints</button>
                <button onClick={() => { onExport('full'); setShowExportMenu(false); }}>Full Activity Report</button>
              </div>
            )}
          </div>
        ) : (
          <button className="pd-export-btn" onClick={() => onExport('full')}>Export Report</button>
        )}
      </div>
    </header>
  );
}

export default DashboardHeader;
