// Categorizes checkpoint IDs by which RAISE flow can complete them.
// Used by the "What to do next" card and to suppress the per-checkpoint
// Log button on items that have a smarter automated path.

export const SCANNABLE_CHECKPOINTS = new Set([
  'data_deidentified',
  'ferpa_compliance',
  'data_classification',
  'bias_audit',
  'admin_bias_audit',
]);

export const DRAFTABLE_CHECKPOINTS = new Set([
  'irb',
  'ai_disclosure',
  'ai_writing_disclosure',
  'ai_coding_disclosure',
  'admin_disclosure',
  'teaching_disclosure',
  'data_minimization',
  'data_storage',
  'human_review',
  'human_override',
  'decision_impact',
  'grading_fairness',
  'grading_transparency',
  'grading_validation',
  'appeal_process',
  'content_accuracy',
  'material_review_cycle',
  'accessibility_check',
  'participant_consent',
  'ip_review',
]);

export function categorizeCheckpoint(checkpointId) {
  if (SCANNABLE_CHECKPOINTS.has(checkpointId)) return 'scannable';
  if (DRAFTABLE_CHECKPOINTS.has(checkpointId)) return 'draftable';
  return 'manual';
}

export function bucketCounts(checkpoints) {
  const counts = { scannable: 0, draftable: 0, manual: 0 };
  for (const cp of checkpoints) {
    if (cp.completed) continue;
    counts[categorizeCheckpoint(cp.id)] += 1;
  }
  return counts;
}
