export const CRITICAL_CHECKPOINT_IDS = [
  'irb',
  'data_deidentified',
  'participant_consent',
  'ferpa_compliance',
  'grading_fairness',
  'decision_impact',
];

export const MEDIUM_CHECKPOINT_IDS = [
  'bias_audit',
  'human_review',
  'ai_disclosure',
  'human_override',
  'admin_bias_audit',
  'content_accuracy',
];

export function getCompletionPercentage(checkpoints) {
  if (!checkpoints || checkpoints.length === 0) return 0;
  const completed = checkpoints.filter(c => c.completed).length;
  return Math.round((completed / checkpoints.length) * 100);
}

export function getRiskAssessment({ allCheckpoints, myCheckpoints, role, completion }) {
  const checkpointsToCheck = role === 'compliance' ? allCheckpoints : myCheckpoints;
  const incompleteCheckpoints = checkpointsToCheck.filter(c => !c.completed);
  const incompleteCritical = incompleteCheckpoints.filter(c => CRITICAL_CHECKPOINT_IDS.includes(c.id));
  const incompleteMedium = incompleteCheckpoints.filter(c => MEDIUM_CHECKPOINT_IDS.includes(c.id));

  const risks = [];
  if (incompleteCritical.length > 0) {
    risks.push({
      level: 'high',
      message: `${incompleteCritical.length} critical compliance item(s) pending`,
      items: incompleteCritical.map(c => c.label),
    });
  }
  if (incompleteMedium.length > 0) {
    risks.push({
      level: 'medium',
      message: `${incompleteMedium.length} transparency/quality item(s) pending`,
      items: incompleteMedium.map(c => c.label),
    });
  }

  let overallRisk = 'low';
  if (risks.some(r => r.level === 'high')) {
    overallRisk = 'high';
  } else if (risks.some(r => r.level === 'medium') || completion < 50) {
    overallRisk = 'medium';
  }

  return { overallRisk, risks, completion };
}
