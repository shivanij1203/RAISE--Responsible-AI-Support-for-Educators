import { useState } from 'react';
import { anonymizeDocuments } from '../../services/api';

const ACCEPTED = '.zip,.pdf,.docx,.txt,.md';

/** Trigger a browser download for a Blob. */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** Decode a base64 ZIP payload into a Blob. */
function base64ToZipBlob(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: 'application/zip' });
}

/**
 * @typedef {Object} DocumentAnonymizerModalProps
 * @property {() => void} onClose
 */

/**
 * Anonymizes a batch of student document submissions (PDF / DOCX / TXT, or a
 * ZIP of them) before they are sent to an external AI grading tool.
 * @param {DocumentAnonymizerModalProps} props
 */
function DocumentAnonymizerModal({ onClose }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [roster, setRoster] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  function handleFileSelect(fileList) {
    setSelectedFiles(Array.from(fileList || []));
    setError('');
    setResult(null);
  }

  async function handleAnonymize() {
    if (selectedFiles.length === 0) {
      setError('Choose a ZIP archive or one or more document files first.');
      return;
    }
    const zips = selectedFiles.filter((f) => f.name.toLowerCase().endsWith('.zip'));
    const docs = selectedFiles.filter((f) => !f.name.toLowerCase().endsWith('.zip'));

    setProcessing(true);
    setError('');
    try {
      const data = await anonymizeDocuments({
        archive: zips[0] || null,
        files: docs,
        roster: roster.trim(),
      });
      downloadBlob(base64ToZipBlob(data.anonymizedZipBase64), 'anonymized_submissions.zip');
      downloadBlob(
        new Blob([data.nameKeyCsv], { type: 'text/csv;charset=utf-8' }),
        'name_key.csv',
      );
      setResult({ ...data.summary, extraZips: zips.length > 1 ? zips.length - 1 : 0 });
    } catch (err) {
      setError(err.response?.data?.error || 'Could not anonymize the documents. Please try again.');
    } finally {
      setProcessing(false);
    }
  }

  const rosterCount = roster
    .split(/[\r\n,]+/)
    .map((n) => n.trim())
    .filter(Boolean).length;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Anonymize Document Submissions</h2>
        <p className="dv-subtitle">
          Upload student documents — PDF, Word, or text, individually or as a ZIP. RAISE
          renames each file to a neutral code, removes personal information from inside the
          documents, and returns an anonymized bundle plus a private name key so you can
          re-attach grades afterward.
        </p>

        <div className="dv-upload">
          <label className="dv-upload-label">
            <input
              type="file"
              accept={ACCEPTED}
              multiple
              onChange={(e) => handleFileSelect(e.target.files)}
            />
            <span>
              {selectedFiles.length > 0
                ? `${selectedFiles.length} file(s) selected`
                : 'Choose ZIP or document files'}
            </span>
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <ul className="da-file-list">
            {selectedFiles.map((f) => (
              <li key={f.name}>{f.name}</li>
            ))}
          </ul>
        )}

        <div className="form-group">
          <label>
            Class roster (optional, strongly recommended)
            {rosterCount > 0 && <span className="da-roster-count"> — {rosterCount} name(s)</span>}
          </label>
          <textarea
            value={roster}
            onChange={(e) => setRoster(e.target.value)}
            placeholder={'One student name per line, e.g.\nJane Doe\nBob Lee'}
            rows={5}
          />
          <p className="da-hint">
            Student names cannot be detected automatically. Without a roster, RAISE removes
            emails, phone numbers, and IDs but <strong>names inside the documents will
            remain</strong>. Paste the roster so those names are reliably redacted.
          </p>
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="btn-primary" onClick={handleAnonymize} disabled={processing}>
          {processing ? 'Anonymizing...' : 'Anonymize and download'}
        </button>

        {result && (
          <div className="dv-redact-panel da-result">
            <div className="dv-redact-title">
              Anonymized {result.fileCount} file(s): {result.codeRange}
            </div>
            <div className="dv-redact-summary">
              Removed {result.totalRedactions} personal detail(s) across{' '}
              {result.contentRedactedCount} document(s).{' '}
              {result.renamedOnlyCount > 0 &&
                `${result.renamedOnlyCount} file(s) were renamed only — see notes below.`}
            </div>

            {result.rosterNamesProvided === 0 && (
              <div className="da-warn">
                No roster was provided, so <strong>student names inside the documents were
                not removed</strong> — only emails, phone numbers, and IDs. Add a roster and
                re-run if names need to be redacted for FERPA de-identification.
              </div>
            )}
            {result.extraZips > 0 && (
              <div className="da-warn">
                {result.extraZips} extra ZIP file(s) were ignored — only the first archive is
                processed. Upload one ZIP at a time.
              </div>
            )}

            <ul className="da-file-summary">
              {result.perFile.map((f) => (
                <li key={f.code} className={f.contentRedacted ? '' : 'da-file-flagged'}>
                  <span className="da-file-code">{f.code}</span>
                  <span className="da-file-orig">{f.originalName}</span>
                  <span className="da-file-meta">
                    {f.contentRedacted
                      ? `${f.redactionCount} redaction(s)`
                      : 'renamed only'}
                    {f.note ? ` — ${f.note}` : ''}
                  </span>
                </li>
              ))}
            </ul>

            <div className="da-hint">
              The anonymized ZIP is what you give the AI grading tool. The name key is
              private — keep it somewhere only you can access, then use it with the
              &ldquo;Re-attach grades&rdquo; step once grading is done. Note: RAISE cannot
              remove <em>indirect</em> identifiers (a student describing a unique personal
              experience) — review the documents before sharing.
            </div>
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default DocumentAnonymizerModal;
