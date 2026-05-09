import { bucketCounts } from '../../constants/checkpointCategories';

function WhatToDoNext({ project, onVerifyDataset, onDraftCheckpoints, onScrollToManual }) {
  const checkpoints = project.checkpoints || [];
  const total = checkpoints.length;
  const completed = checkpoints.filter((c) => c.completed).length;
  if (total === 0) return null;
  if (completed === total) return null;

  const counts = bucketCounts(checkpoints);
  const steps = [];
  if (counts.scannable > 0) {
    steps.push({
      key: 'verify',
      title: `Run Verify Dataset to auto-complete ${counts.scannable} data check${counts.scannable === 1 ? '' : 's'}`,
      hint: 'PII, FERPA, classification, and bias audit run from one CSV upload.',
      cta: 'Open Verify Dataset',
      action: onVerifyDataset,
    });
  }
  if (counts.draftable > 0) {
    steps.push({
      key: 'draft',
      title: `Use Draft Checkpoints to draft ${counts.draftable} policy answer${counts.draftable === 1 ? '' : 's'}`,
      hint: 'RAISE writes a starting answer based on your activity context. You review and save what you like.',
      cta: 'Open Draft Checkpoints',
      action: onDraftCheckpoints,
    });
  }
  if (counts.manual > 0) {
    steps.push({
      key: 'manual',
      title: `Manually log ${counts.manual} checkpoint${counts.manual === 1 ? '' : 's'} that need your input`,
      hint: 'These are activity-specific items only you can answer.',
      cta: 'Show me',
      action: onScrollToManual,
    });
  }

  if (steps.length === 0) return null;

  const next = steps[0];
  const remaining = steps.slice(1);

  return (
    <div className="wtdn-card">
      <div className="wtdn-header">
        <span className="wtdn-eyebrow">What to do next</span>
        <span className="wtdn-progress">{completed} of {total} complete</span>
      </div>
      <div className="wtdn-step wtdn-step-primary">
        <div className="wtdn-step-num">1</div>
        <div className="wtdn-step-body">
          <div className="wtdn-step-title">{next.title}</div>
          <div className="wtdn-step-hint">{next.hint}</div>
        </div>
        <button className="btn-primary wtdn-cta" onClick={next.action}>{next.cta}</button>
      </div>
      {remaining.length > 0 && (
        <div className="wtdn-rest">
          <div className="wtdn-rest-label">Then:</div>
          <ol className="wtdn-rest-list">
            {remaining.map((s, i) => (
              <li key={s.key}>
                <span className="wtdn-rest-num">{i + 2}.</span>
                <span className="wtdn-rest-title">{s.title}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export default WhatToDoNext;
