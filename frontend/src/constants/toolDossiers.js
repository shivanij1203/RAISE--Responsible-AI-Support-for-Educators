// Compliance dossiers for commonly-used AI tools.
// Faculty look these up rather than researching tool policies themselves.
// Lookup by lower-cased tool name. Keep neutral, factual phrasing.

export const TOOL_DOSSIERS = {
  claude: {
    vendor: 'Anthropic',
    category: 'Chatbot / general assistant',
    dataRetention: 'API: zero retention by default. Web product: 30-day default with opt-out.',
    trainingOptOut: 'API data is never used for training. Web product opt-out available in settings.',
    ferpaSafe: 'Suitable when used via API with zero retention; not for student PII via consumer web product.',
    euAiActClass: 'Limited risk (general-purpose AI model); high risk if used in high-stakes decisions.',
    recommendedFor: ['Writing', 'Qualitative analysis', 'Grading (with rubric)', 'Coding'],
    notRecommendedFor: ['Direct admissions decisions without human review', 'Storing health data'],
    notes: 'Anthropic publishes a usage policy and a Trust Center. Constitutional AI training reduces some bias risk but does not eliminate it.',
  },
  chatgpt: {
    vendor: 'OpenAI',
    category: 'Chatbot / general assistant',
    dataRetention: 'Free / Plus tier: 30 days, used for training unless opt-out. Enterprise / API: zero retention available.',
    trainingOptOut: 'Plus / Free tier requires explicit opt-out. Enterprise tier opts out by default.',
    ferpaSafe: 'Only via Enterprise tier with signed BAA-style data agreement; not on consumer tier.',
    euAiActClass: 'Limited risk for general use; high risk in regulated decision contexts.',
    recommendedFor: ['Writing', 'Lit review', 'Coding', 'Brainstorming'],
    notRecommendedFor: ['Storing student PII on consumer tier', 'Confidential research data on free tier'],
    notes: 'GPT-4 / GPT-5 models available. Memory feature can persist personal data across sessions; verify off when needed.',
  },
  gemini: {
    vendor: 'Google',
    category: 'Chatbot / general assistant',
    dataRetention: 'Workspace tier: tied to Google Workspace data policies. Consumer tier: stored to improve services.',
    trainingOptOut: 'Workspace customers excluded from training by default; consumer requires opt-out.',
    ferpaSafe: 'Workspace for Education tier only; not consumer Gemini.',
    euAiActClass: 'Limited risk for general use; high risk in regulated decision contexts.',
    recommendedFor: ['Document analysis', 'Research summaries', 'Multimodal tasks'],
    notRecommendedFor: ['Confidential data on consumer tier'],
    notes: 'Tightly integrated with Google Workspace. Long-context capability strong for multi-document workflows.',
  },
  copilot: {
    vendor: 'Microsoft / GitHub',
    category: 'Code assistant',
    dataRetention: 'GitHub Copilot Business / Enterprise: zero retention. Consumer: code snippets used for product improvement.',
    trainingOptOut: 'Business / Enterprise excluded from training. Consumer requires opt-out.',
    ferpaSafe: 'Generally not relevant; code-only context. Avoid pasting student data into prompts.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Coding', 'Code review', 'Research scripts'],
    notRecommendedFor: ['Storing student data via inline comments'],
    notes: 'M365 Copilot is a separate product with broader data scope; review policy before use on student-facing data.',
  },
  perplexity: {
    vendor: 'Perplexity AI',
    category: 'Research / search',
    dataRetention: 'Pro tier supports zero retention; consumer queries logged.',
    trainingOptOut: 'Available on Enterprise tier only.',
    ferpaSafe: 'Not for student PII; treat as a public-facing search tool.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Literature search', 'Citation discovery', 'Background research'],
    notRecommendedFor: ['Confidential research data', 'Anything containing FERPA-protected info'],
    notes: 'Returns sourced answers with citations. Sources should still be verified manually before citing in academic work.',
  },
  otter: {
    vendor: 'Otter.ai',
    category: 'Transcription / qualitative',
    dataRetention: 'Audio and transcripts stored on Otter servers; retention configurable per plan.',
    trainingOptOut: 'Available on Business / Enterprise tier; default for consumer.',
    ferpaSafe: 'Use only with informed consent from all participants and Business tier minimum.',
    euAiActClass: 'Limited risk; care needed under voice biometric provisions.',
    recommendedFor: ['Interview transcription', 'Focus group capture', 'Lecture notes'],
    notRecommendedFor: ['Recording without explicit participant consent'],
    notes: 'Notify all participants in advance. Verify the institution has a contract before storing protected interviews.',
  },
  turnitin: {
    vendor: 'Turnitin',
    category: 'Plagiarism / AI detection',
    dataRetention: 'Submissions stored long-term in the Turnitin similarity database.',
    trainingOptOut: 'Institutional contracts vary; verify training-use clauses with vendor.',
    ferpaSafe: 'Yes when accessed through institutional contract with student-data agreement in place.',
    euAiActClass: 'Limited risk for similarity; AI detection feature is contested in literature.',
    recommendedFor: ['Similarity checking on student submissions'],
    notRecommendedFor: ['Sole basis for academic-integrity decisions; AI-detection accuracy is unreliable'],
    notes: 'AI-detection has documented false-positive bias against non-native English writers. Always pair with human review.',
  },
  gradescope: {
    vendor: 'Turnitin / Gradescope',
    category: 'Grading',
    dataRetention: 'Student work stored for the academic term plus retention window per institutional contract.',
    trainingOptOut: 'AI-grading features have institution-level controls.',
    ferpaSafe: 'Yes under institutional contract.',
    euAiActClass: 'High risk where AI auto-grades consequential assignments.',
    recommendedFor: ['Rubric-based grading', 'Bubble-sheet exams', 'Programming assignments'],
    notRecommendedFor: ['Auto-graded final letter grades without human review'],
    notes: 'Pair AI-suggested grades with the validation step from the Verify Dataset flow.',
  },
  grammarly: {
    vendor: 'Grammarly',
    category: 'Writing assistance',
    dataRetention: 'Drafts stored to provide suggestions; deletable from account.',
    trainingOptOut: 'Business / EDU tier excludes training; consumer requires opt-out.',
    ferpaSafe: 'EDU tier only.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Editing', 'Tone review', 'Grammar checking'],
    notRecommendedFor: ['Pasting student PII into the consumer extension'],
    notes: 'Generative-AI features available; treat their outputs as drafts to review.',
  },
  notebooklm: {
    vendor: 'Google',
    category: 'Research / synthesis',
    dataRetention: 'Notebook contents stored in user account.',
    trainingOptOut: 'NotebookLM does not train on user uploads (per Google product page).',
    ferpaSafe: 'Workspace for Education only; not consumer NotebookLM.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Lit review', 'Source synthesis', 'Notes from PDFs'],
    notRecommendedFor: ['Confidential or unpublished research data without tier verification'],
    notes: 'Strong with multi-document context; cites back to source material.',
  },
  consensus: {
    vendor: 'Consensus.app',
    category: 'Research / evidence search',
    dataRetention: 'Search queries logged per privacy policy.',
    trainingOptOut: 'Verify with vendor; standard SaaS terms.',
    ferpaSafe: 'Not for student PII; designed for paper search.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Evidence-based literature search', 'Meta-analysis prep'],
    notRecommendedFor: ['Anything containing FERPA-protected info'],
    notes: 'Returns aggregated answers across published papers. Always read the cited papers themselves.',
  },
  scite: {
    vendor: 'scite',
    category: 'Research / citation analysis',
    dataRetention: 'Standard SaaS retention; institutional contract details vary.',
    trainingOptOut: 'Per institutional terms.',
    ferpaSafe: 'Not relevant; citation database tool.',
    euAiActClass: 'Limited risk.',
    recommendedFor: ['Citation context analysis', 'Smart citations review'],
    notRecommendedFor: ['Sole judgment of paper quality'],
    notes: 'Surfaces supporting / contrasting citations across the literature.',
  },
};

export function lookupDossier(toolName) {
  if (!toolName) return null;
  const key = toolName.toLowerCase().replace(/[^a-z0-9]/g, '');
  for (const dossierKey of Object.keys(TOOL_DOSSIERS)) {
    if (key.includes(dossierKey) || dossierKey.includes(key)) {
      return TOOL_DOSSIERS[dossierKey];
    }
  }
  return null;
}
