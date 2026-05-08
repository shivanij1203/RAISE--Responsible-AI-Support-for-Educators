import CheckpointComments from '../CheckpointComments';

function frameworkClass(fw) {
  return `framework-badge fw-${fw.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;
}

function AuditTrail({ decisions }) {
  if (decisions.length === 0) return null;
  return (
    <div className="inline-decisions">
      <div className="inline-decisions-label">Audit Trail ({decisions.length})</div>
      {decisions.map(d => (
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
}

function CheckpointItem({ checkpoint, role, saving, expanded, decisions, projectId, onToggleExpanded, onLog, onReopen }) {
  const isCompliance = role === 'compliance';
  const isStudent = role === 'student';
  const showLog = !isCompliance && !checkpoint.completed;
  const showCompletedActions = !isCompliance && checkpoint.completed;
  const showInfoBtn = !isStudent && checkpoint.what;

  const completedDate = checkpoint.completedAt
    ? new Date(checkpoint.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : null;

  return (
    <div className={`checkpoint-item ${checkpoint.completed ? 'completed' : 'pending'} ${expanded ? 'expanded' : ''}`}>
      <div className="checkpoint-main">
        <div className="checkpoint-status-icon">
          {checkpoint.completed
            ? <span className="status-complete">{'✓'}</span>
            : <span className="status-pending">{'○'}</span>}
        </div>
        <div className="checkpoint-content">
          <span className="checkpoint-label">{checkpoint.label}</span>
          {checkpoint.frameworks?.length > 0 && (
            <div className="framework-badges">
              {checkpoint.frameworks.map(fw => (
                <span key={fw} className={frameworkClass(fw)}>{fw}</span>
              ))}
            </div>
          )}
          {checkpoint.completed ? (
            <span className="checkpoint-date completed-date">Completed {completedDate}</span>
          ) : (
            <span className="checkpoint-date pending-date">Pending</span>
          )}
        </div>
        {showInfoBtn && (
          <button className="help-btn" onClick={onToggleExpanded} title="Learn more about this checkpoint">
            {expanded ? 'Hide' : 'Info'}
          </button>
        )}
        {isStudent && (
          <button className="help-btn always-visible" onClick={onToggleExpanded} title="Learn what this means">
            {expanded ? 'Hide' : 'Guide'}
          </button>
        )}
        {showLog && (
          <button className="log-btn primary" onClick={onLog} title="Log completion">Log</button>
        )}
        {showCompletedActions && (
          <>
            <button className="log-btn secondary" onClick={onLog} title="Add note">Add Note</button>
            <button className="log-btn undo" onClick={onReopen} disabled={saving} title="Reopen">Reopen</button>
          </>
        )}
        {isCompliance && (
          <span className="compliance-status-label">
            {checkpoint.completed ? 'Documented' : 'Pending'}
          </span>
        )}
      </div>
      {expanded && (
        <div className="checkpoint-expanded">
          {checkpoint.what && (
            <div className="checkpoint-help">
              <div className="help-section"><strong>What:</strong><p>{checkpoint.what}</p></div>
              <div className="help-section"><strong>Why it matters:</strong><p>{checkpoint.why}</p></div>
              <div className="help-section"><strong>How to complete:</strong><p>{checkpoint.how}</p></div>
            </div>
          )}
          <AuditTrail decisions={decisions} />
          <CheckpointComments projectId={projectId} checkpointId={checkpoint.id} />
        </div>
      )}
    </div>
  );
}

export default CheckpointItem;
