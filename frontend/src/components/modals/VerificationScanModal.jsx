import { useState } from 'react';
import { scanFileForPII, classifyData, runBiasAudit, getFileColumns } from '../../services/api';

const BIAS_CHECKPOINTS = ['bias_audit', 'admin_bias_audit'];

function VerificationScanModal({ checkpointId, onClose }) {
  const [scanResult, setScanResult] = useState(null);
  const [classifyResult, setClassifyResult] = useState(null);
  const [classifyText, setClassifyText] = useState('');
  const [scanning, setScanning] = useState(false);

  const [biasFile, setBiasFile] = useState(null);
  const [biasColumns, setBiasColumns] = useState([]);
  const [outcomeColumn, setOutcomeColumn] = useState('');
  const [protectedColumn, setProtectedColumn] = useState('');
  const [positiveValue, setPositiveValue] = useState('');
  const [biasResult, setBiasResult] = useState(null);

  async function handleFileScan(file) {
    setScanning(true);
    setScanResult(null);
    try {
      const scanType = checkpointId === 'ferpa_compliance' ? 'ferpa' : 'pii';
      const result = await scanFileForPII(file, scanType);
      setScanResult(result);
    } catch {
      setScanResult({ error: 'Scan failed. Please try again.' });
    } finally {
      setScanning(false);
    }
  }

  async function handleClassify() {
    if (!classifyText.trim()) return;
    setScanning(true);
    setClassifyResult(null);
    try {
      const result = await classifyData(classifyText);
      setClassifyResult(result);
    } catch {
      setClassifyResult({ error: 'Classification failed.' });
    } finally {
      setScanning(false);
    }
  }

  async function handleBiasFile(file) {
    setBiasFile(file);
    setBiasResult(null);
    setBiasColumns([]);
    setOutcomeColumn('');
    setProtectedColumn('');
    setPositiveValue('');
    try {
      const result = await getFileColumns(file);
      if (result.columns && result.columns.length > 0) {
        setBiasColumns(result.columns);
      } else {
        setBiasResult({ error: result.error || 'Could not read columns from file.' });
      }
    } catch {
      setBiasResult({ error: 'Could not read columns from file.' });
    }
  }

  async function handleRunBiasAudit() {
    if (!biasFile || !outcomeColumn || !protectedColumn) return;
    setScanning(true);
    setBiasResult(null);
    try {
      const result = await runBiasAudit(biasFile, outcomeColumn, protectedColumn, positiveValue);
      setBiasResult(result);
    } catch {
      setBiasResult({ error: 'Audit failed. Please try again.' });
    } finally {
      setScanning(false);
    }
  }

  if (BIAS_CHECKPOINTS.includes(checkpointId)) {
    const hasVerdict = biasResult && biasResult.verdict;
    const verdictClass = biasResult?.verdict === 'PASS' ? 'scan-pass' : 'scan-fail';
    const canRun = biasColumns.length > 0 && !hasVerdict;
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
          <h2>Bias Audit</h2>
          <p className="modal-subtitle">
            Upload a CSV of decisions to check for disparate impact across protected groups.
            Uses the 4/5ths rule and statistical parity difference.
          </p>
          <div className="form-group">
            <label>Upload CSV file (max 10MB)</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                const file = e.target.files[0];
                if (file) handleBiasFile(file);
              }}
            />
          </div>
          {canRun && (
            <>
              <div className="form-group">
                <label>Outcome column (the decision being audited)</label>
                <select value={outcomeColumn} onChange={(e) => setOutcomeColumn(e.target.value)}>
                  <option value="">Select column...</option>
                  {biasColumns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Protected column (group attribute, e.g. race, gender)</label>
                <select value={protectedColumn} onChange={(e) => setProtectedColumn(e.target.value)}>
                  <option value="">Select column...</option>
                  {biasColumns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Positive outcome value (optional, auto-detected if blank)</label>
                <input
                  type="text"
                  value={positiveValue}
                  onChange={(e) => setPositiveValue(e.target.value)}
                  placeholder="e.g., advance, hired, approved"
                />
              </div>
            </>
          )}
          {scanning && <div className="scan-loading">Running bias audit...</div>}
          {hasVerdict && (
            <div className={`scan-result ${verdictClass}`}>
              <div className="scan-verdict-label">Verdict: {biasResult.verdict}</div>
              <p className="scan-verdict-text">{biasResult.verdictMessage}</p>
              <div className="scan-stats">
                <span>{biasResult.totalRecords} records</span>
                <span>{biasResult.uniqueGroups} groups</span>
                <span>Positive outcome: {biasResult.positiveOutcome}</span>
              </div>
              <div className="scan-findings">
                <div className="scan-findings-label">Outcome rate by group:</div>
                {biasResult.groupStats.map(g => (
                  <div key={g.group} className="scan-finding">
                    <span className="finding-type">{g.group}</span>
                    <span className="finding-msg">
                      {g.positive} of {g.total} positive ({g.rate}%)
                    </span>
                  </div>
                ))}
              </div>
              <div className="scan-findings">
                <div className="scan-findings-label">Fairness metrics:</div>
                <div className={`scan-finding ${biasResult.metrics.disparateImpact.pass ? 'low' : 'high'}`}>
                  <span className="finding-type">Disparate impact ratio</span>
                  <span className="finding-msg">
                    {biasResult.metrics.disparateImpact.value} (threshold {biasResult.metrics.disparateImpact.threshold} or higher): {biasResult.metrics.disparateImpact.pass ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <div className={`scan-finding ${biasResult.metrics.statisticalParity.pass ? 'low' : 'high'}`}>
                  <span className="finding-type">Statistical parity difference</span>
                  <span className="finding-msg">
                    {biasResult.metrics.statisticalParity.value} (threshold {biasResult.metrics.statisticalParity.threshold} or lower): {biasResult.metrics.statisticalParity.pass ? 'PASS' : 'FAIL'}
                  </span>
                </div>
              </div>
            </div>
          )}
          {biasResult?.error && (
            <div className="scan-result scan-fail"><p>{biasResult.error}</p></div>
          )}
          <div className="modal-actions">
            <button className="btn-secondary" onClick={onClose}>Close</button>
            {canRun && (
              <button
                className="btn-primary"
                onClick={handleRunBiasAudit}
                disabled={!outcomeColumn || !protectedColumn || scanning}
              >
                {scanning ? 'Auditing...' : 'Run Audit'}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (checkpointId === 'data_classification') {
    const riskyLevel = classifyResult?.suggestedLevel === 'restricted' || classifyResult?.suggestedLevel === 'confidential';
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
          <h2>Data Classification Check</h2>
          <p className="modal-subtitle">Describe your data and we will suggest a classification level.</p>
          <div className="form-group">
            <label>Describe the data you are working with</label>
            <textarea
              value={classifyText}
              onChange={(e) => setClassifyText(e.target.value)}
              placeholder="e.g., Student enrollment records including names, majors, and GPA from Fall 2025..."
              rows={4}
            />
          </div>
          {classifyResult && !classifyResult.error && (
            <div className={`scan-result ${riskyLevel ? 'scan-fail' : 'scan-pass'}`}>
              <div className="scan-verdict-label">Suggested Classification</div>
              <div className="scan-verdict-level">{classifyResult.suggestedLevel.toUpperCase()}</div>
              <p className="scan-verdict-text">{classifyResult.reasoning}</p>
            </div>
          )}
          {classifyResult?.error && (
            <div className="scan-result scan-fail"><p>{classifyResult.error}</p></div>
          )}
          <div className="modal-actions">
            <button className="btn-secondary" onClick={onClose}>Close</button>
            <button className="btn-primary" onClick={handleClassify} disabled={!classifyText.trim() || scanning}>
              {scanning ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isFerpa = checkpointId === 'ferpa_compliance';
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>{isFerpa ? 'FERPA Compliance Check' : 'PII Detection Scan'}</h2>
        <p className="modal-subtitle">
          {isFerpa
            ? 'Upload a CSV of your student data to check for FERPA-protected fields.'
            : 'Upload a CSV of your dataset to scan for personally identifiable information.'}
        </p>
        <div className="form-group">
          <label>Upload CSV file (max 10MB)</label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) handleFileScan(file);
            }}
          />
        </div>
        {scanning && <div className="scan-loading">Scanning file for identifiable data...</div>}
        {scanResult && !scanResult.error && (
          <div className={`scan-result ${scanResult.hasPII ? 'scan-fail' : 'scan-pass'}`}>
            <div className="scan-verdict-label">{scanResult.hasPII ? 'Issues Found' : 'No Issues Found'}</div>
            <p className="scan-verdict-text">{scanResult.verdict}</p>
            <div className="scan-stats">
              <span>{scanResult.totalColumns} columns scanned</span>
              <span>{scanResult.rowsScanned} rows checked</span>
              <span>{scanResult.flaggedColumns} column{scanResult.flaggedColumns !== 1 ? 's' : ''} flagged</span>
            </div>
            {scanResult.findings.length > 0 && (
              <div className="scan-findings">
                <div className="scan-findings-label">Findings:</div>
                {scanResult.findings.map((f, i) => (
                  <div key={i} className={`scan-finding ${f.severity}`}>
                    <span className="finding-type">{f.type.replace(/_/g, ' ')}</span>
                    <span className="finding-msg">{f.message}</span>
                    {f.sample && <span className="finding-sample">Sample: {f.sample}</span>}
                  </div>
                ))}
              </div>
            )}
            {isFerpa && scanResult.ferpaSpecific && (
              <div className="scan-ferpa-extra">
                <div className="scan-verdict-label" style={{ marginTop: '12px' }}>
                  {scanResult.ferpaSpecific.hasFerpaData ? 'FERPA-Protected Data Detected' : 'No FERPA-Specific Fields Found'}
                </div>
                <p className="scan-verdict-text">{scanResult.ferpaSpecific.verdict}</p>
              </div>
            )}
          </div>
        )}
        {scanResult?.error && (
          <div className="scan-result scan-fail"><p>{scanResult.error}</p></div>
        )}
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default VerificationScanModal;
