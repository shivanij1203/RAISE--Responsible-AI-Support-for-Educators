export const CHECKPOINT_EXAMPLES = {
  irb: 'e.g., IRB protocol #2024-0123 approved on 01/15/2024 includes AI analysis methods',
  data_classification: 'e.g., Data classified as Confidential - contains de-identified health records',
  ai_disclosure: 'e.g., Will include AI disclosure in methods section per journal requirements',
  data_deidentified: 'e.g., Removed all 18 HIPAA identifiers using Safe Harbor method',
  data_storage: 'e.g., Data stored on institutional secure server with encryption at rest',
  bias_audit: 'e.g., Tested model across age groups - no significant performance disparities found',
  human_review: 'e.g., Two reviewers validate 20% random sample of AI outputs weekly',
  ai_coding_disclosure: 'e.g., Used GPT-4 for initial theme suggestions, all codes verified by research team',
  participant_consent: 'e.g., Consent form v2.1 updated to include AI processing disclosure',
  ai_writing_disclosure: 'e.g., Used Grammarly and ChatGPT for grammar/clarity edits only',
  grading_fairness: 'e.g., Compared AI grades across demographics - no statistically significant disparities',
  ferpa_compliance: 'e.g., Confirmed student data processed only on FERPA-compliant institutional systems',
  grading_transparency: 'e.g., Syllabus updated to disclose AI-assisted grading with opt-out provision',
  human_override: 'e.g., Students can request manual re-grading within 7 days of grade posting',
  grading_validation: 'e.g., Instructor reviewed 25% random sample - 96% agreement with AI grades',
  content_accuracy: 'e.g., All AI-generated lecture materials reviewed by subject matter expert',
  accessibility_check: 'e.g., Materials tested with screen reader and meet WCAG 2.1 AA standards',
  ip_review: 'e.g., AI-generated content checked against copyright database - no infringement found',
  teaching_disclosure: 'e.g., Course syllabus includes AI-generated content disclosure statement',
  material_review_cycle: 'e.g., Quarterly review scheduled - next review April 2026',
  decision_impact: 'e.g., Impact assessment completed - affects 500 applicants across 3 programs',
  appeal_process: 'e.g., Written appeal process published - 30-day review window with human committee',
  admin_bias_audit: 'e.g., Disparate impact analysis completed - no protected group disadvantaged',
  data_minimization: 'e.g., Reduced data fields from 45 to 12 essential variables for AI processing',
  admin_disclosure: 'e.g., Notification sent to all applicants that AI assists in initial screening',
};

const DEFAULT_EXAMPLE = 'e.g., Describe what action was taken';

export function getExampleForCheckpoint(checkpointId) {
  return CHECKPOINT_EXAMPLES[checkpointId] || DEFAULT_EXAMPLE;
}
