import { useEffect, useState } from 'react';
import {
  scanFileForPII,
  classifyData,
  runBiasAudit,
  getFileColumns,
  logDecision,
  redactPiiInFile,
  generateGradingPrompt,
  extractPdfText,
  blindGradeCsv,
} from '../../services/api';

const PII_CHECKPOINT = 'data_deidentified';
const FERPA_CHECKPOINT = 'ferpa_compliance';
const CLASSIFY_CHECKPOINT = 'data_classification';
const BIAS_CHECKPOINTS = ['bias_audit', 'admin_bias_audit'];

function summarizePiiVerdict(result) {
  const findings = result?.findings || [];
  if (findings.length === 0) {
    return { passed: true, headline: 'No PII detected.', detail: 'Dataset appears de-identified.' };
  }
  const fields = findings.map((f) => f.column || f.type).filter(Boolean);
  return {
    passed: false,
    headline: `PII detected in ${findings.length} column${findings.length === 1 ? '' : 's'}.`,
    detail: fields.length ? `Flagged: ${fields.join(', ')}` : 'See findings for details.',
  };
}

function summarizeFerpaVerdict(result) {
  const ferpa = result?.ferpaSpecific;
  if (!ferpa) return { passed: true, headline: 'No FERPA-protected fields detected.', detail: '' };
  return {
    passed: !ferpa.hasFerpaData,
    headline: ferpa.verdict || (ferpa.hasFerpaData ? 'FERPA-protected fields detected.' : 'No FERPA-protected fields.'),
    detail: ferpa.ferpaFindings?.length ? `${ferpa.ferpaFindings.length} field(s) flagged` : '',
  };
}

function summarizeClassifyVerdict(result) {
  const level = result?.suggestedLevel || result?.suggested_level || result?.level;
  if (!level) return { passed: true, headline: 'Classification suggested.', detail: '' };
  return {
    passed: true,
    headline: `Suggested classification: ${level}.`,
    detail: result?.rationale || result?.reason || '',
  };
}

function summarizeBiasVerdict(result) {
  const ratio = result?.disparateImpactRatio ?? result?.disparate_impact_ratio;
  const verdict = result?.verdict || (ratio !== undefined && ratio < 0.8 ? 'FAIL' : 'PASS');
  return {
    passed: verdict === 'PASS',
    headline: `Bias audit ${verdict}. Disparate impact ratio: ${ratio !== undefined ? Number(ratio).toFixed(3) : 'n/a'}.`,
    detail: result?.summary || '',
  };
}

function ResultCard({ title, status, summary, applied, applying, onApply, exists }) {
  if (!exists) {
    return (
      <div className="dv-result-card dv-result-skip">
        <div className="dv-result-title">{title}</div>
        <div className="dv-result-summary">Checkpoint not in this activity. Skipped.</div>
      </div>
    );
  }
  if (status === 'pending') {
    return (
      <div className="dv-result-card dv-result-pending">
        <div className="dv-result-title">{title}</div>
        <div className="dv-result-summary">Running...</div>
      </div>
    );
  }
  if (status === 'error') {
    return (
      <div className="dv-result-card dv-result-error">
        <div className="dv-result-title">{title}</div>
        <div className="dv-result-summary">{summary?.detail || 'Error running this check.'}</div>
      </div>
    );
  }
  if (status === 'idle') {
    return (
      <div className="dv-result-card">
        <div className="dv-result-title">{title}</div>
        <div className="dv-result-summary">Waiting for input...</div>
      </div>
    );
  }
  const passed = summary?.passed;
  return (
    <div className={`dv-result-card ${passed ? 'dv-result-pass' : 'dv-result-fail'}`}>
      <div className="dv-result-row">
        <div className="dv-result-title">{title}</div>
        <span className={`dv-badge ${passed ? 'dv-badge-pass' : 'dv-badge-fail'}`}>
          {passed ? 'PASS' : 'REVIEW'}
        </span>
      </div>
      <div className="dv-result-headline">{summary?.headline}</div>
      {summary?.detail && <div className="dv-result-detail">{summary.detail}</div>}
      <div className="dv-result-actions">
        {applied ? (
          <span className="dv-applied-tag">Applied to checkpoint ✓</span>
        ) : (
          <button className="btn-secondary dv-apply-btn" onClick={onApply} disabled={applying}>
            {applying ? 'Applying...' : 'Apply to checkpoint'}
          </button>
        )}
      </div>
    </div>
  );
}

function DatasetVerificationModal({ project, onClose, onCheckpointApplied }) {
  const checkpointIds = new Set((project.checkpoints || []).map((c) => c.id));
  const hasPii = checkpointIds.has(PII_CHECKPOINT);
  const hasFerpa = checkpointIds.has(FERPA_CHECKPOINT);
  const hasClassify = checkpointIds.has(CLASSIFY_CHECKPOINT);
  const biasCheckpointId = BIAS_CHECKPOINTS.find((id) => checkpointIds.has(id));
  const hasBias = !!biasCheckpointId;

  const [file, setFile] = useState(null);
  const [piiState, setPiiState] = useState({ status: 'idle', summary: null, raw: null });
  const [ferpaState, setFerpaState] = useState({ status: 'idle', summary: null, raw: null });
  const [classifyState, setClassifyState] = useState({ status: 'idle', summary: null, raw: null });
  const [biasState, setBiasState] = useState({ status: 'idle', summary: null, raw: null });

  const [columns, setColumns] = useState([]);
  const [outcomeColumn, setOutcomeColumn] = useState('');
  const [protectedColumn, setProtectedColumn] = useState('');
  const [positiveValue, setPositiveValue] = useState('');

  const [applied, setApplied] = useState({});
  const [applying, setApplying] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [redacting, setRedacting] = useState(false);
  const [redactSummary, setRedactSummary] = useState(null);
  const [blinding, setBlinding] = useState(false);
  const [blindSummary, setBlindSummary] = useState(null);

  const isGrading = (project.aiUseCase || '').toLowerCase() === 'grading';
  const defaultTool = (project.aiTools && project.aiTools[0]?.name) || '';
  const [rubricText, setRubricText] = useState('');
  const [gradingTool, setGradingTool] = useState(defaultTool);
  const [generatingPrompt, setGeneratingPrompt] = useState(false);
  const [gradingPrompt, setGradingPrompt] = useState(null);
  const [promptCopied, setPromptCopied] = useState(false);
  const [rubricPdfStatus, setRubricPdfStatus] = useState('');
  const [rubricExtracting, setRubricExtracting] = useState(false);

  // Run classification once on mount, since it uses the activity description
  useEffect(() => {
    if (!hasClassify) return;
    const desc = project.description || '';
    if (!desc.trim()) {
      setClassifyState({ status: 'error', summary: { detail: 'Activity has no description to classify.' }, raw: null });
      return;
    }
    setClassifyState({ status: 'pending', summary: null, raw: null });
    classifyData(desc)
      .then((res) => setClassifyState({ status: 'done', summary: summarizeClassifyVerdict(res), raw: res }))
      .catch(() => setClassifyState({ status: 'error', summary: { detail: 'Classification request failed.' }, raw: null }));
  }, [hasClassify, project.description]);

  async function handleFileSelect(selected) {
    if (!selected) return;
    setFile(selected);
    setGlobalError('');

    if (hasPii) {
      setPiiState({ status: 'pending', summary: null, raw: null });
      scanFileForPII(selected, 'pii')
        .then((res) => setPiiState({ status: 'done', summary: summarizePiiVerdict(res), raw: res }))
        .catch(() => setPiiState({ status: 'error', summary: { detail: 'PII scan failed.' }, raw: null }));
    }

    if (hasFerpa) {
      setFerpaState({ status: 'pending', summary: null, raw: null });
      scanFileForPII(selected, 'ferpa')
        .then((res) => setFerpaState({ status: 'done', summary: summarizeFerpaVerdict(res), raw: res }))
        .catch(() => setFerpaState({ status: 'error', summary: { detail: 'FERPA scan failed.' }, raw: null }));
    }

    if (hasBias) {
      try {
        const res = await getFileColumns(selected);
        if (res.columns?.length) {
          setColumns(res.columns);
        } else {
          setGlobalError(res.error || 'Could not read columns from file.');
        }
      } catch {
        setGlobalError('Could not read columns from file.');
      }
    }
  }

  async function handleRunBias() {
    if (!file || !outcomeColumn || !protectedColumn) return;
    setBiasState({ status: 'pending', summary: null, raw: null });
    try {
      const res = await runBiasAudit(file, outcomeColumn, protectedColumn, positiveValue);
      setBiasState({ status: 'done', summary: summarizeBiasVerdict(res), raw: res });
    } catch {
      setBiasState({ status: 'error', summary: { detail: 'Bias audit failed.' }, raw: null });
    }
  }

  function downloadCsv(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function handleBlindGrade() {
    if (!file) return;
    setBlinding(true);
    setGlobalError('');
    try {
      const result = await blindGradeCsv(file);
      const baseName = file.name.replace(/\.csv$/i, '');
      downloadCsv(result.anonymizedContent, `${baseName}_anonymous.csv`);
      if (result.mappingContent) {
        downloadCsv(result.mappingContent, `${baseName}_name_key.csv`);
      }
      setBlindSummary(result.summary);
    } catch {
      setGlobalError('Could not set up blind grading. Try again.');
    } finally {
      setBlinding(false);
    }
  }

  async function handleRubricPdfUpload(pdfFile) {
    if (!pdfFile) return;
    setRubricExtracting(true);
    setRubricPdfStatus('');
    setGlobalError('');
    try {
      const result = await extractPdfText(pdfFile);
      if (!result.text || !result.text.trim()) {
        setRubricPdfStatus(result.warning || 'No text could be extracted from this PDF.');
        return;
      }
      const header = `--- From ${pdfFile.name} ---`;
      const newText = rubricText.trim()
        ? `${rubricText.trim()}\n\n${header}\n${result.text.trim()}`
        : `${header}\n${result.text.trim()}`;
      setRubricText(newText);
      const truncatedNote = result.truncated ? ' (text was truncated)' : '';
      setRubricPdfStatus(`Extracted ${result.pagesRead} of ${result.pageCount} pages${truncatedNote}. Review and edit below.`);
    } catch (err) {
      setRubricPdfStatus(err.response?.data?.error || 'Could not extract text from PDF.');
    } finally {
      setRubricExtracting(false);
    }
  }

  async function handleGeneratePrompt() {
    if (!rubricText.trim()) {
      setGlobalError('Tell RAISE what to look for. Add at least one or two rubric items.');
      return;
    }
    setGlobalError('');
    setGeneratingPrompt(true);
    try {
      const result = await generateGradingPrompt(project.id, rubricText.trim(), gradingTool);
      setGradingPrompt(result);
    } catch (err) {
      setGlobalError(err.response?.data?.error || 'Could not generate prompt.');
    } finally {
      setGeneratingPrompt(false);
    }
  }

  async function handleCopyPrompt() {
    if (!gradingPrompt?.prompt) return;
    try {
      await navigator.clipboard.writeText(gradingPrompt.prompt);
      setPromptCopied(true);
      setTimeout(() => setPromptCopied(false), 2000);
    } catch {
      setGlobalError('Could not copy to clipboard.');
    }
  }

  async function handleRedactDownload() {
    if (!file) return;
    setRedacting(true);
    setGlobalError('');
    try {
      const result = await redactPiiInFile(file);
      const blob = new Blob([result.content], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const baseName = file.name.replace(/\.csv$/i, '');
      a.href = url;
      a.download = `${baseName}_redacted.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setRedactSummary(result.summary);
    } catch {
      setGlobalError('Could not generate cleaned dataset. Try again.');
    } finally {
      setRedacting(false);
    }
  }

  async function applyToCheckpoint(checkpointId, summary, scanLabel) {
    if (!checkpointId || !summary) return;
    setApplying({ ...applying, [checkpointId]: true });
    try {
      const description = `${scanLabel}: ${summary.headline}${summary.detail ? ' ' + summary.detail : ''}`;
      await logDecision(project.id, {
        checkpoint: checkpointId,
        description,
        proofType: 'automated_scan',
        proofValue: scanLabel,
      });
      setApplied({ ...applied, [checkpointId]: true });
      if (onCheckpointApplied) onCheckpointApplied(checkpointId);
    } catch {
      setGlobalError('Could not apply result to checkpoint. Try again.');
    } finally {
      setApplying({ ...applying, [checkpointId]: false });
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Verify Dataset</h2>
        <p className="dv-subtitle">
          Upload your dataset once. RAISE runs every applicable check (PII, FERPA, classification, bias audit)
          and lets you apply each result to its checkpoint with one click.
        </p>

        <div className="dv-upload">
          <label className="dv-upload-label">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => handleFileSelect(e.target.files?.[0])}
            />
            <span>{file ? `Selected: ${file.name}` : 'Choose CSV file'}</span>
          </label>
          {hasClassify && !file && (
            <span className="dv-upload-hint">Data classification runs from your activity description.</span>
          )}
        </div>

        {globalError && <p className="error-text">{globalError}</p>}

        <div className="dv-results-grid">
          <ResultCard
            title="PII Scan"
            exists={hasPii}
            status={piiState.status}
            summary={piiState.summary}
            applied={applied[PII_CHECKPOINT]}
            applying={applying[PII_CHECKPOINT]}
            onApply={() => applyToCheckpoint(PII_CHECKPOINT, piiState.summary, 'PII Scan')}
          />
          <ResultCard
            title="FERPA Compliance"
            exists={hasFerpa}
            status={ferpaState.status}
            summary={ferpaState.summary}
            applied={applied[FERPA_CHECKPOINT]}
            applying={applying[FERPA_CHECKPOINT]}
            onApply={() => applyToCheckpoint(FERPA_CHECKPOINT, ferpaState.summary, 'FERPA Scan')}
          />
          <ResultCard
            title="Data Classification"
            exists={hasClassify}
            status={classifyState.status}
            summary={classifyState.summary}
            applied={applied[CLASSIFY_CHECKPOINT]}
            applying={applying[CLASSIFY_CHECKPOINT]}
            onApply={() => applyToCheckpoint(CLASSIFY_CHECKPOINT, classifyState.summary, 'Classification')}
          />
          <ResultCard
            title="Bias Audit"
            exists={hasBias}
            status={biasState.status}
            summary={biasState.summary}
            applied={applied[biasCheckpointId]}
            applying={applying[biasCheckpointId]}
            onApply={() => applyToCheckpoint(biasCheckpointId, biasState.summary, 'Bias Audit')}
          />
        </div>

        {file && piiState.status === 'done' && piiState.summary && !piiState.summary.passed && isGrading && (
          <div className="dv-redact-panel">
            <div className="dv-redact-header">
              <div>
                <div className="dv-redact-title">Set up Blind Grading</div>
                <div className="dv-redact-sub">
                  Replace names, emails, and IDs with anonymous codes (<code>STUDENT-001</code>, <code>STUDENT-002</code>...).
                  RAISE downloads two files: the anonymous version for the AI tool, and a private name key
                  so you can match grades back to students after grading.
                </div>
              </div>
              <button className="btn-primary" onClick={handleBlindGrade} disabled={blinding}>
                {blinding ? 'Preparing...' : 'Download both files'}
              </button>
            </div>
            {blindSummary && (
              <div className="dv-redact-summary">
                Coded {blindSummary.rowsCoded} row(s) as {blindSummary.codeRange}.
                Anonymous file is for the AI. Name key is private — keep it where only you can see it.
              </div>
            )}
          </div>
        )}

        {file && piiState.status === 'done' && piiState.summary && !piiState.summary.passed && !isGrading && (
          <div className="dv-redact-panel">
            <div className="dv-redact-header">
              <div>
                <div className="dv-redact-title">Remove personal info</div>
                <div className="dv-redact-sub">
                  Replaces names, emails, phone numbers, SSNs, addresses, and DOB values with{' '}
                  <code>[REDACTED]</code>. Grades, enrollment, and other research fields stay intact.
                </div>
              </div>
              <button className="btn-primary" onClick={handleRedactDownload} disabled={redacting}>
                {redacting ? 'Cleaning...' : 'Download cleaned CSV'}
              </button>
            </div>
            {redactSummary && (
              <div className="dv-redact-summary">
                Cleaned. Redacted {redactSummary.cellsRedactedByColumn} cell(s) across{' '}
                {redactSummary.columnsRedacted?.length || 0} identity column(s).
                {redactSummary.cellsScrubbedInline > 0
                  ? ` Also scrubbed ${redactSummary.cellsScrubbedInline} stray inline value(s).`
                  : ''}
              </div>
            )}
          </div>
        )}

        {isGrading && (
          <div className="dv-prompt-panel">
            <div className="dv-prompt-title">Grading prompt for {gradingTool || 'your AI tool'}</div>
            <div className="dv-prompt-sub">
              RAISE writes a copy-paste prompt that tells the AI what to look for, with FERPA notice
              and fairness language built in. The same text is your audit trail.
            </div>

            <div className="form-group">
              <label>What should the AI look for? (your rubric)</label>
              <div className="dv-rubric-upload">
                <label className="dv-rubric-upload-btn">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleRubricPdfUpload(f);
                      e.target.value = '';
                    }}
                  />
                  <span>{rubricExtracting ? 'Reading PDF...' : 'Upload rubric or instructions PDF'}</span>
                </label>
                {rubricPdfStatus && <span className="dv-rubric-status">{rubricPdfStatus}</span>}
              </div>
              <textarea
                value={rubricText}
                onChange={(e) => setRubricText(e.target.value)}
                placeholder="e.g., Reward clear thesis, specific examples, and citations to course readings. Penalize vague claims without support. Score 0–100."
                rows={6}
              />
            </div>

            <div className="form-group">
              <label>AI tool the faculty will use</label>
              <input
                type="text"
                value={gradingTool}
                onChange={(e) => setGradingTool(e.target.value)}
                placeholder="e.g., Claude, ChatGPT, Gemini"
              />
            </div>

            <button className="btn-primary" onClick={handleGeneratePrompt} disabled={generatingPrompt}>
              {generatingPrompt ? 'Generating...' : (gradingPrompt ? 'Regenerate' : 'Generate Grading Prompt')}
            </button>

            {gradingPrompt && (
              <div className="dv-prompt-output">
                <div className="dv-prompt-output-header">
                  <span className="dv-prompt-output-title">Ready to paste into {gradingPrompt.tool}</span>
                  <button className="btn-secondary dv-copy-btn" onClick={handleCopyPrompt}>
                    {promptCopied ? 'Copied ✓' : 'Copy'}
                  </button>
                </div>
                <pre className="dv-prompt-text">{gradingPrompt.prompt}</pre>
                <div className="dv-prompt-includes">
                  Built-in guardrails: {gradingPrompt.includes.join(', ')}
                </div>
              </div>
            )}
          </div>
        )}

        {hasBias && file && columns.length > 0 && biasState.status !== 'done' && (
          <div className="dv-bias-config">
            <div className="dv-bias-config-title">Bias audit needs two columns from your dataset</div>
            <div className="dv-bias-config-grid">
              <div className="form-group">
                <label>Outcome column (the AI's decision)</label>
                <select value={outcomeColumn} onChange={(e) => setOutcomeColumn(e.target.value)}>
                  <option value="">Select column...</option>
                  {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Protected attribute column (e.g., race, gender)</label>
                <select value={protectedColumn} onChange={(e) => setProtectedColumn(e.target.value)}>
                  <option value="">Select column...</option>
                  {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Positive outcome value (optional)</label>
                <input
                  type="text"
                  value={positiveValue}
                  onChange={(e) => setPositiveValue(e.target.value)}
                  placeholder="e.g., admit, approve, 1"
                />
              </div>
            </div>
            <button
              className="btn-primary"
              onClick={handleRunBias}
              disabled={!outcomeColumn || !protectedColumn || biasState.status === 'pending'}
            >
              {biasState.status === 'pending' ? 'Running audit...' : 'Run Bias Audit'}
            </button>
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default DatasetVerificationModal;
