import { useEffect, useState } from 'react';
import { fetchSmartDefaults, logDecision } from '../../services/api';

function SmartDefaultsModal({ project, onClose, onCheckpointApplied }) {
  const [drafts, setDrafts] = useState(null);
  const [edits, setEdits] = useState({});
  const [skipped, setSkipped] = useState({});
  const [applied, setApplied] = useState({});
  const [savingAll, setSavingAll] = useState(false);
  const [savingOne, setSavingOne] = useState({});
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSmartDefaults(project.id)
      .then((res) => {
        setDrafts(res.drafts || []);
        const init = {};
        (res.drafts || []).forEach((d) => {
          init[d.checkpointId] = {
            description: d.suggestedDescription,
            notes: d.suggestedNotes || '',
          };
        });
        setEdits(init);
      })
      .catch(() => setError('Could not load drafts.'));
  }, [project.id]);

  function updateField(checkpointId, field, value) {
    setEdits({
      ...edits,
      [checkpointId]: { ...edits[checkpointId], [field]: value },
    });
  }

  function toggleSkip(checkpointId) {
    setSkipped({ ...skipped, [checkpointId]: !skipped[checkpointId] });
  }

  async function applyOne(checkpointId) {
    const fields = edits[checkpointId];
    if (!fields?.description?.trim()) return;
    setSavingOne({ ...savingOne, [checkpointId]: true });
    try {
      await logDecision(project.id, {
        checkpoint: checkpointId,
        description: fields.description.trim(),
        notes: fields.notes || '',
        proofType: 'smart_default',
      });
      setApplied({ ...applied, [checkpointId]: true });
      if (onCheckpointApplied) onCheckpointApplied(checkpointId);
    } catch {
      setError('Could not save this checkpoint.');
    } finally {
      setSavingOne({ ...savingOne, [checkpointId]: false });
    }
  }

  async function applyAll() {
    setSavingAll(true);
    setError('');
    const targets = (drafts || []).filter(
      (d) => !applied[d.checkpointId] && !skipped[d.checkpointId]
    );
    for (const d of targets) {
      const fields = edits[d.checkpointId];
      if (!fields?.description?.trim()) continue;
      try {
        await logDecision(project.id, {
          checkpoint: d.checkpointId,
          description: fields.description.trim(),
          notes: fields.notes || '',
          proofType: 'smart_default',
        });
        if (onCheckpointApplied) onCheckpointApplied(d.checkpointId);
        setApplied((prev) => ({ ...prev, [d.checkpointId]: true }));
      } catch {
        setError(`Could not save ${d.checkpointLabel}. Continuing.`);
      }
    }
    setSavingAll(false);
  }

  if (drafts === null) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2>Draft Checkpoints</h2>
          <p>Loading drafts...</p>
        </div>
      </div>
    );
  }

  if (drafts.length === 0) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2>Draft Checkpoints</h2>
          <p className="sd-empty">
            No checkpoints to pre-fill. Either everything is already complete, or the
            remaining items need manual entry.
          </p>
          <div className="modal-actions">
            <button className="btn-primary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  const remaining = drafts.filter(
    (d) => !applied[d.checkpointId] && !skipped[d.checkpointId]
  ).length;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Draft Checkpoints</h2>
        <p className="sd-subtitle">
          RAISE drafted answers for {drafts.length} checkpoints based on your activity
          context. Review each, edit if needed, and save them as evidence in one click.
          Each saved card creates an audit-trail entry on the checkpoint.
        </p>

        {error && <p className="error-text">{error}</p>}

        <div className="sd-cards">
          {drafts.map((d) => {
            const isApplied = !!applied[d.checkpointId];
            const isSkipped = !!skipped[d.checkpointId];
            const isSaving = !!savingOne[d.checkpointId];
            return (
              <div
                key={d.checkpointId}
                className={`sd-card ${isApplied ? 'sd-card-applied' : ''} ${isSkipped ? 'sd-card-skipped' : ''}`}
              >
                <div className="sd-card-header">
                  <div className="sd-card-title">{d.checkpointLabel}</div>
                  <span className={`sd-confidence sd-confidence-${d.confidence}`}>
                    {d.confidence} confidence
                  </span>
                </div>

                <textarea
                  className="sd-card-desc"
                  rows={3}
                  value={edits[d.checkpointId]?.description || ''}
                  onChange={(e) => updateField(d.checkpointId, 'description', e.target.value)}
                  disabled={isApplied || isSkipped}
                />

                {edits[d.checkpointId]?.notes && (
                  <details className="sd-card-notes">
                    <summary>Reviewer notes (optional)</summary>
                    <textarea
                      rows={2}
                      value={edits[d.checkpointId]?.notes || ''}
                      onChange={(e) => updateField(d.checkpointId, 'notes', e.target.value)}
                      disabled={isApplied || isSkipped}
                    />
                  </details>
                )}

                <div className="sd-card-actions">
                  {isApplied ? (
                    <span className="sd-applied-tag">Saved as evidence ✓</span>
                  ) : isSkipped ? (
                    <>
                      <span className="sd-skipped-tag">Skipped</span>
                      <button className="btn-link" onClick={() => toggleSkip(d.checkpointId)}>
                        Undo skip
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn-secondary sd-skip-btn"
                        onClick={() => toggleSkip(d.checkpointId)}
                      >
                        Skip
                      </button>
                      <button
                        className="btn-primary sd-apply-btn"
                        onClick={() => applyOne(d.checkpointId)}
                        disabled={isSaving}
                      >
                        {isSaving ? 'Saving...' : 'Save as evidence'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="modal-actions sd-modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
          <button
            className="btn-primary"
            onClick={applyAll}
            disabled={savingAll || remaining === 0}
          >
            {savingAll ? 'Saving all...' : `Save all ${remaining} as evidence`}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SmartDefaultsModal;
