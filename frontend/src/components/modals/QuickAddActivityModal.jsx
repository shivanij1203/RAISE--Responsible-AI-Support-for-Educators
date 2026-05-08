import { useState } from 'react';
import { parseQuickAddActivity, createProject } from '../../services/api';
import { USE_CASE_LABELS_SHORT } from '../../constants/useCases';

const RISK_LABELS = {
  involves_student_data: 'Involves student data',
  data_leaves_institution: 'Data leaves institutional systems',
  affects_decisions: 'Affects grades, admissions, or evaluations',
  involves_human_subjects: 'Involves human subjects research',
};

const EXAMPLES = [
  'Using Claude to grade essays in MIS 4123 this fall.',
  'Running ChatGPT on interview transcripts for thematic analysis.',
  'Building an admissions screening model from applicant data.',
];

function QuickAddActivityModal({ onClose, onCreated, initialDescription = '' }) {
  const [description, setDescription] = useState(initialDescription);
  const [draft, setDraft] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [shareAsExample, setShareAsExample] = useState(false);

  async function handleParse() {
    if (!description.trim()) {
      setError('Describe what AI you will use and for what.');
      return;
    }
    setError('');
    setParsing(true);
    try {
      const parsed = await parseQuickAddActivity(description.trim());
      setDraft(parsed);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not parse description.');
    } finally {
      setParsing(false);
    }
  }

  async function handleConfirm() {
    if (!draft) return;
    setError('');
    setCreating(true);
    try {
      const project = await createProject(
        draft.name,
        draft.description,
        draft.ai_use_case,
        draft.suggested_tool_ids || [],
        '',
        '',
        draft.risk_context || {},
        shareAsExample,
      );
      onCreated(project);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create activity.');
    } finally {
      setCreating(false);
    }
  }

  function updateDraftField(field, value) {
    setDraft({ ...draft, [field]: value });
  }

  function toggleRisk(field) {
    setDraft({
      ...draft,
      risk_context: { ...draft.risk_context, [field]: !draft.risk_context[field] },
    });
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Add a New Activity</h2>
        <p className="qa-subtitle">
          RAISE picks the use case, flags the risks, and generates the right
          compliance checkpoints automatically from your description.
        </p>

        {!draft ? (
          <>
            <div className="form-group">
              <label>What AI will you use, and for what?</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Using Claude to grade essays in MIS 4123 this fall."
                rows={4}
                autoFocus
              />
            </div>

            <div className="qa-examples">
              <span className="qa-examples-label">Try:</span>
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  className="qa-example-chip"
                  type="button"
                  onClick={() => setDescription(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>

            {error && <p className="error-text">{error}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
              <button className="btn-primary" onClick={handleParse} disabled={parsing}>
                {parsing ? 'Parsing...' : 'Parse'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="qa-notes">
              {(draft.notes || []).map((n, i) => (
                <div key={i} className="qa-note-line">{n}</div>
              ))}
            </div>

            <div className="form-group">
              <label>Activity Name</label>
              <input
                type="text"
                value={draft.name}
                onChange={(e) => updateDraftField('name', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Use Case</label>
              <select
                value={draft.ai_use_case}
                onChange={(e) => updateDraftField('ai_use_case', e.target.value)}
              >
                {Object.entries(USE_CASE_LABELS_SHORT).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Risk Flags (review and adjust)</label>
              <div className="qa-risk-list">
                {Object.entries(RISK_LABELS).map(([field, label]) => (
                  <label key={field} className="qa-risk-item">
                    <input
                      type="checkbox"
                      checked={!!draft.risk_context?.[field]}
                      onChange={() => toggleRisk(field)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={draft.description}
                onChange={(e) => updateDraftField('description', e.target.value)}
                rows={3}
              />
            </div>

            <div className="qa-share-toggle">
              <label className="qa-share-label">
                <input
                  type="checkbox"
                  checked={shareAsExample}
                  onChange={(e) => setShareAsExample(e.target.checked)}
                />
                <div>
                  <span className="qa-share-text">Share this activity as an anonymized example</span>
                  <span className="qa-share-hint">
                    Off by default. When on, this activity (without your name) appears in the institutional
                    Use Cases tab so other faculty and students can learn from it. You can change this
                    later from the activity's Edit menu.
                  </span>
                </div>
              </label>
            </div>

            {error && <p className="error-text">{error}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setDraft(null)}>Back</button>
              <button className="btn-primary" onClick={handleConfirm} disabled={creating}>
                {creating ? 'Creating...' : 'Confirm & Create'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default QuickAddActivityModal;
