import { useState } from 'react';
import { getExampleForCheckpoint } from '../../constants/checkpointExamples';

function LogDecisionModal({ checkpointId, checkpointLabel, availableTools, saving, onClose, onSave }) {
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  const [proofType, setProofType] = useState('');
  const [proofValue, setProofValue] = useState('');
  const [toolUsedId, setToolUsedId] = useState('');

  async function handleSave() {
    await onSave({
      checkpoint: checkpointId,
      description,
      notes,
      proofType,
      proofValue,
      toolUsedId: toolUsedId || null,
    });
  }

  const canSave = Boolean(checkpointId) && Boolean(description) && !saving;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Document Checkpoint</h2>
        <p className="modal-subtitle">{checkpointLabel}</p>

        <div className="form-group">
          <label>What was done? *</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={getExampleForCheckpoint(checkpointId)}
          />
        </div>

        {availableTools.length > 0 && (
          <div className="form-group">
            <label>Tool used (optional)</label>
            <select
              value={toolUsedId}
              onChange={(e) => setToolUsedId(e.target.value)}
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
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any additional context, reference numbers, dates..."
            rows={2}
          />
        </div>

        <div className="form-group">
          <label>Attach Evidence (optional)</label>
          <select
            value={proofType}
            onChange={(e) => { setProofType(e.target.value); setProofValue(''); }}
            className="proof-type-select"
          >
            <option value="">No attachment</option>
            <option value="url">URL / Link</option>
            <option value="file">File Reference</option>
          </select>
        </div>

        {proofType === 'url' && (
          <div className="form-group">
            <label>URL</label>
            <input
              type="url"
              value={proofValue}
              onChange={(e) => setProofValue(e.target.value)}
              placeholder="https://example.com/irb-approval.pdf"
            />
            <p className="form-hint">Link to document, approval letter, or supporting evidence</p>
          </div>
        )}

        {proofType === 'file' && (
          <div className="form-group">
            <label>File Reference</label>
            <input
              type="text"
              value={proofValue}
              onChange={(e) => setProofValue(e.target.value)}
              placeholder="IRB_Approval_2024.pdf (in project folder)"
            />
            <p className="form-hint">Name and location of the file for reference</p>
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={!canSave}>
            {saving ? 'Saving...' : 'Save Documentation'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default LogDecisionModal;
