"""Checkpoint generation logic for AI use-case compliance projects.

Moved from views.py to keep views thin. Contains:
- FRAMEWORK_MAP: maps checkpoint IDs to applicable regulatory frameworks
- generate_checkpoints_for_use_case(): returns the right set of checkpoints
  for a given AI use case
"""
from typing import Any

# ============== Framework Mapping ==============

FRAMEWORK_MAP: dict[str, list[str]] = {
    'irb': ['IRB', 'Common Rule'],
    'data_classification': ['NIST AI RMF', 'Institutional Policy'],
    'ai_disclosure': ['Transparency', 'Journal Policy'],
    'data_deidentified': ['HIPAA', 'FERPA', 'NIST AI RMF'],
    'data_storage': ['NIST AI RMF', 'Institutional Policy'],
    'bias_audit': ['NIST AI RMF', 'Fairness'],
    'human_review': ['NIST AI RMF', 'Accountability'],
    'ai_coding_disclosure': ['Transparency', 'Journal Policy'],
    'participant_consent': ['IRB', 'Common Rule', 'FERPA'],
    'ai_writing_disclosure': ['Transparency', 'Journal Policy'],
    'grading_fairness': ['FERPA', 'Fairness', 'Institutional Policy'],
    'ferpa_compliance': ['FERPA'],
    'grading_transparency': ['FERPA', 'Transparency', 'Institutional Policy'],
    'human_override': ['FERPA', 'Accountability'],
    'grading_validation': ['NIST AI RMF', 'Accountability'],
    'content_accuracy': ['NIST AI RMF', 'Institutional Policy'],
    'accessibility_check': ['ADA', 'Section 508'],
    'ip_review': ['Copyright', 'Institutional Policy'],
    'teaching_disclosure': ['Transparency', 'Institutional Policy'],
    'material_review_cycle': ['NIST AI RMF', 'Institutional Policy'],
    'decision_impact': ['NIST AI RMF', 'Fairness'],
    'appeal_process': ['Accountability', 'Institutional Policy'],
    'admin_bias_audit': ['NIST AI RMF', 'Fairness', 'Civil Rights'],
    'data_minimization': ['NIST AI RMF', 'Privacy'],
    'admin_disclosure': ['Transparency', 'Institutional Policy'],
}


# ============== Checkpoint Generation Logic ==============

def generate_checkpoints_for_use_case(ai_use_case: str, risk_context: dict | None = None) -> list[dict[str, Any]]:
    """Return the right set of checkpoints depending on use case and risk context.

    risk_context keys (all bool):
        involves_student_data — Does this involve student records?
        data_leaves_institution — Does data leave institutional systems?
        affects_decisions — Does this affect grades, admissions, or evaluations?
        involves_human_subjects — Does this involve human subjects research?
    """
    if risk_context is None:
        risk_context = {}

    base: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'irb',
            'label': 'IRB Status Confirmed',
            'category': 'Regulatory',
            'assigned_to': 'pi',
            'what': 'Verify whether your research requires IRB approval and if your current protocol covers AI use.',
            'why': 'IRB approval obtained before AI tools existed may not cover new AI methods. Using AI on human subjects data without proper approval is a compliance violation.',
            'how': 'Check your IRB protocol. If AI is not mentioned, contact your IRB office to determine if an amendment is needed.',
        },
        {
            'checkpoint_id': 'data_classification',
            'label': 'Data Classification Determined',
            'category': 'Data',
            'assigned_to': 'pi',
            'what': 'Identify what type of data you are using and its sensitivity level.',
            'why': 'Different data types have different handling requirements. Identifiable health data requires stricter controls than public datasets.',
            'how': 'Categorize your data: Public, Internal, Confidential, or Restricted. Check if it contains PII, PHI, or other sensitive information.',
        },
        {
            'checkpoint_id': 'ai_disclosure',
            'label': 'AI Use Disclosure Planned',
            'category': 'Transparency',
            'assigned_to': 'pi',
            'what': 'Plan how you will disclose AI use in publications, presentations, and to participants.',
            'why': 'Most journals and conferences now require AI disclosure. Transparency builds trust and is increasingly required by publishers.',
            'how': 'Draft a disclosure statement describing which AI tools were used and for what purpose. Include in your methods section.',
        },
    ]

    data_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'data_deidentified',
            'label': 'Data De-identification Verified',
            'category': 'Data',
            'assigned_to': 'student',
            'what': 'Ensure personal identifiers are removed before AI processing.',
            'why': 'Sending identifiable data to AI systems (especially cloud-based) may violate privacy regulations and IRB requirements.',
            'how': 'Remove or mask: names, dates, locations, ID numbers, photos, and any combination that could identify someone. Use established de-identification standards (HIPAA Safe Harbor or Expert Determination).',
        },
        {
            'checkpoint_id': 'data_storage',
            'label': 'Secure Storage Confirmed',
            'category': 'Data',
            'assigned_to': 'student',
            'what': 'Verify that data and AI outputs are stored securely.',
            'why': 'Research data requires protection from unauthorized access. Cloud AI services may retain data unless configured otherwise.',
            'how': 'Use institutional approved storage. Check AI service data retention policies. Enable encryption at rest and in transit.',
        },
    ]

    model_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'bias_audit',
            'label': 'Bias Audit Conducted',
            'category': 'Model',
            'assigned_to': 'student',
            'what': 'Test your AI model for unfair or biased outcomes across different groups.',
            'why': 'AI models can perpetuate or amplify biases in training data, leading to unfair outcomes for certain populations.',
            'how': 'Evaluate model performance across demographic subgroups (age, gender, race if applicable). Compare error rates and outcomes. Document any disparities found and mitigation steps taken.',
        },
        {
            'checkpoint_id': 'human_review',
            'label': 'Human Review Process Defined',
            'category': 'Model',
            'assigned_to': 'pi',
            'what': 'Establish how humans will review and validate AI outputs.',
            'why': 'AI systems make errors. Human oversight catches mistakes and maintains accountability, especially for consequential decisions.',
            'how': 'Define: Who reviews AI outputs? What percentage is reviewed? What are the criteria for acceptance/rejection? Document the review process.',
        },
    ]

    qualitative_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'ai_coding_disclosure',
            'label': 'AI-Assisted Coding Disclosed',
            'category': 'Transparency',
            'assigned_to': 'student',
            'what': 'Document how AI was used in qualitative coding or analysis.',
            'why': 'Using AI to code interviews or analyze text changes the methodology. Reviewers and readers need to evaluate this.',
            'how': 'Describe the AI tool used, what it did (initial codes, theme suggestions), and how human researchers validated or modified the output.',
        },
        {
            'checkpoint_id': 'participant_consent',
            'label': 'Participant Consent Covers AI',
            'category': 'Regulatory',
            'assigned_to': 'pi',
            'what': 'Ensure consent forms mention AI processing of participant data.',
            'why': 'Participants have a right to know their data will be processed by AI systems, especially if using cloud-based tools.',
            'how': 'Review consent forms. If AI use was not mentioned, consult IRB about whether re-consent or notification is needed.',
        },
    ]

    writing_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'ai_writing_disclosure',
            'label': 'AI Writing Assistance Disclosed',
            'category': 'Transparency',
            'assigned_to': 'student',
            'what': 'Document any AI assistance in drafting or editing text.',
            'why': 'Journals require disclosure of AI writing tools. Undisclosed use may be considered a form of misconduct.',
            'how': 'List AI tools used (e.g., ChatGPT, Grammarly AI). Describe the extent: grammar checking, sentence rephrasing, content generation. Place in acknowledgments or methods.',
        },
    ]

    grading_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'grading_fairness',
            'label': 'Grading Fairness Audit',
            'category': 'Assessment',
            'assigned_to': 'pi',
            'what': 'Verify AI grading produces equitable outcomes across student demographics.',
            'why': 'AI grading tools can carry biases from training data, leading to unfair outcomes for certain student groups.',
            'how': 'Compare AI-generated grades across demographic subgroups. Check for statistically significant disparities. Document findings and any corrections made.',
        },
        {
            'checkpoint_id': 'ferpa_compliance',
            'label': 'FERPA Compliance Verified',
            'category': 'Regulatory',
            'assigned_to': 'pi',
            'what': 'Confirm student records processed by AI are handled per FERPA requirements.',
            'why': 'Student education records are protected under FERPA. Sending them to external AI services may violate federal law.',
            'how': 'Verify AI processing happens on FERPA-compliant systems. Check vendor data processing agreements. Confirm no student data is retained by third-party AI services.',
        },
        {
            'checkpoint_id': 'grading_transparency',
            'label': 'Grading Criteria Disclosed to Students',
            'category': 'Transparency',
            'assigned_to': 'pi',
            'what': 'Ensure students are informed that AI is used in the grading process.',
            'why': 'Students have a right to know how their work is evaluated. Transparency builds trust and meets institutional policy requirements.',
            'how': 'Update your syllabus to include AI grading disclosure. Communicate in class and provide an opt-out or appeal mechanism if required by policy.',
        },
        {
            'checkpoint_id': 'human_override',
            'label': 'Human Override Process Defined',
            'category': 'Assessment',
            'assigned_to': 'pi',
            'what': 'Define a process for students to appeal or request human review of AI-assisted grades.',
            'why': 'Students must have recourse when they believe an AI grade is incorrect. This is both an ethical and often institutional requirement.',
            'how': 'Establish a clear appeal window (e.g., 7 days). Document the process in the syllabus. Ensure a human instructor reviews all appeals.',
        },
        {
            'checkpoint_id': 'grading_validation',
            'label': 'AI Grading Output Validated',
            'category': 'Assessment',
            'assigned_to': 'pi',
            'what': 'Sample and validate AI-generated grades against instructor judgment.',
            'why': 'AI grading must be verified for accuracy before being applied at scale. Unvalidated AI grades risk harming student outcomes.',
            'how': 'Review a random 20-25% sample of AI grades. Compare with your own assessment. Document agreement rate and any adjustments made.',
        },
    ]

    teaching_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'content_accuracy',
            'label': 'Content Accuracy Verified',
            'category': 'Quality',
            'assigned_to': 'pi',
            'what': 'Review AI-generated teaching materials for factual accuracy.',
            'why': 'AI can produce plausible-sounding but incorrect information. Distributing inaccurate materials undermines educational quality.',
            'how': 'Have a subject matter expert review all AI-generated content. Cross-reference claims with authoritative sources. Flag and correct any inaccuracies.',
        },
        {
            'checkpoint_id': 'accessibility_check',
            'label': 'Accessibility Standards Met',
            'category': 'Quality',
            'assigned_to': 'pi',
            'what': 'Ensure AI-generated materials meet accessibility requirements (ADA/Section 508).',
            'why': 'Institutions must provide accessible materials to all students. AI-generated content often lacks proper accessibility features.',
            'how': 'Test materials with screen readers. Ensure alt text, proper heading structure, and sufficient color contrast. Follow WCAG 2.1 AA guidelines.',
        },
        {
            'checkpoint_id': 'ip_review',
            'label': 'Intellectual Property Reviewed',
            'category': 'Regulatory',
            'assigned_to': 'pi',
            'what': 'Confirm AI-generated content does not infringe on existing copyrights.',
            'why': 'AI models trained on copyrighted material may reproduce protected content. Using such content in teaching materials creates legal risk.',
            'how': 'Check AI output for close similarity to known sources. Understand your institution\'s IP policy regarding AI-generated content. Add attribution where appropriate.',
        },
        {
            'checkpoint_id': 'teaching_disclosure',
            'label': 'AI Use Disclosed to Students',
            'category': 'Transparency',
            'assigned_to': 'pi',
            'what': 'Inform students that course materials include AI-generated content.',
            'why': 'Transparency about AI use in teaching sets expectations and models responsible AI practices for students.',
            'how': 'Add a disclosure statement to your syllabus. Label AI-generated materials clearly. Discuss AI\'s role in course material creation during the first class.',
        },
        {
            'checkpoint_id': 'material_review_cycle',
            'label': 'Periodic Review Cycle Established',
            'category': 'Quality',
            'assigned_to': 'pi',
            'what': 'Schedule regular reviews of AI-generated teaching materials for continued accuracy.',
            'why': 'AI-generated content may become outdated as knowledge evolves. Regular review ensures materials remain current and accurate.',
            'how': 'Set a review schedule (e.g., quarterly or each semester). Document review dates and any updates made. Assign responsibility for ongoing review.',
        },
    ]

    admin_checkpoints: list[dict[str, Any]] = [
        {
            'checkpoint_id': 'decision_impact',
            'label': 'Decision Impact Assessment Completed',
            'category': 'Governance',
            'assigned_to': 'pi',
            'what': 'Document who is affected by AI-assisted administrative decisions and how.',
            'why': 'Administrative decisions (admissions, resource allocation, scheduling) carry high-stakes consequences for individuals and groups.',
            'how': 'Identify all stakeholders affected. Estimate the number of people impacted. Assess potential consequences of incorrect decisions. Document findings.',
        },
        {
            'checkpoint_id': 'appeal_process',
            'label': 'Appeal / Recourse Process Defined',
            'category': 'Governance',
            'assigned_to': 'pi',
            'what': 'Ensure individuals affected by AI-informed decisions can challenge them.',
            'why': 'People affected by automated decisions have a right to human review. This is both an ethical obligation and increasingly a legal requirement.',
            'how': 'Create a written appeal process with clear timelines. Ensure a human decision-maker reviews all appeals. Publish the process where affected parties can find it.',
        },
        {
            'checkpoint_id': 'admin_bias_audit',
            'label': 'Bias Audit for Administrative Decisions',
            'category': 'Governance',
            'assigned_to': 'pi',
            'what': 'Test for disparate impact on protected groups in AI-assisted decisions.',
            'why': 'AI systems can perpetuate or amplify existing institutional biases, leading to discrimination in administrative outcomes.',
            'how': 'Analyze decision outcomes across demographic groups. Use disparate impact ratio (4/5ths rule) to identify potential bias. Document findings and corrective actions.',
        },
        {
            'checkpoint_id': 'data_minimization',
            'label': 'Data Minimization Verified',
            'category': 'Data',
            'assigned_to': 'pi',
            'what': 'Confirm only necessary data is used in administrative AI processing.',
            'why': 'Using excessive personal data increases privacy risk and potential for misuse without improving decision quality.',
            'how': 'Audit which data fields the AI system uses. Remove any fields not essential to the decision. Document the rationale for each retained field.',
        },
        {
            'checkpoint_id': 'admin_disclosure',
            'label': 'AI Use Disclosed to Affected Parties',
            'category': 'Transparency',
            'assigned_to': 'pi',
            'what': 'Notify people affected by decisions that AI was involved in the process.',
            'why': 'Transparency about AI involvement in decisions builds trust and is increasingly required by institutional policy and regulation.',
            'how': 'Include AI disclosure in decision notification letters/emails. Add disclosure to relevant web pages and application forms. Make the disclosure clear and prominent.',
        },
    ]

    involves_student_data = risk_context.get('involves_student_data', False)
    data_leaves = risk_context.get('data_leaves_institution', False)
    affects_decisions = risk_context.get('affects_decisions', False)
    involves_human_subjects = risk_context.get('involves_human_subjects', False)

    # Start with use-case-specific checkpoints
    checkpoints: list[dict[str, Any]] = []

    if ai_use_case == 'data_analysis':
        checkpoints += data_checkpoints + model_checkpoints
    elif ai_use_case == 'qualitative':
        checkpoints += data_checkpoints + qualitative_checkpoints
    elif ai_use_case == 'ml_model':
        checkpoints += data_checkpoints + model_checkpoints
    elif ai_use_case == 'writing':
        checkpoints += writing_checkpoints
    elif ai_use_case == 'literature':
        checkpoints += writing_checkpoints
    elif ai_use_case == 'grading':
        checkpoints += grading_checkpoints
    elif ai_use_case == 'teaching':
        checkpoints += teaching_checkpoints
    elif ai_use_case == 'admin':
        checkpoints += admin_checkpoints

    # Risk-based additions — add checkpoints based on context, not just use case
    existing_ids = {cp['checkpoint_id'] for cp in checkpoints}

    # If student data is involved, ensure FERPA + de-identification checkpoints
    if involves_student_data:
        for cp in data_checkpoints:
            if cp['checkpoint_id'] not in existing_ids:
                checkpoints.append(cp)
                existing_ids.add(cp['checkpoint_id'])

    # If data leaves institutional systems, ensure storage + de-identification
    if data_leaves:
        for cp in data_checkpoints:
            if cp['checkpoint_id'] not in existing_ids:
                checkpoints.append(cp)
                existing_ids.add(cp['checkpoint_id'])

    # If it affects grades/admissions/evaluations, ensure human review + bias audit
    if affects_decisions:
        decision_cps = [cp for cp in model_checkpoints if cp['checkpoint_id'] in ('bias_audit', 'human_review')]
        for cp in decision_cps:
            if cp['checkpoint_id'] not in existing_ids:
                checkpoints.append(cp)
                existing_ids.add(cp['checkpoint_id'])

    # If human subjects research, ensure IRB + consent are in base
    if involves_human_subjects:
        for cp in qualitative_checkpoints:
            if cp['checkpoint_id'] == 'participant_consent' and cp['checkpoint_id'] not in existing_ids:
                checkpoints.append(cp)
                existing_ids.add(cp['checkpoint_id'])

    # Build base checkpoints — filter IRB out if not research and not human subjects
    filtered_base = []
    for cp in base:
        if cp['checkpoint_id'] == 'irb' and not involves_human_subjects:
            # Skip IRB for non-research activities (grading, teaching, admin)
            if ai_use_case in ('grading', 'teaching', 'admin'):
                continue
        filtered_base.append(cp)

    checkpoints = filtered_base + checkpoints

    # Faculty-only use cases: assign ALL checkpoints to PI
    faculty_only_cases = {'grading', 'teaching', 'admin'}
    if ai_use_case in faculty_only_cases:
        checkpoints = [{**cp, 'assigned_to': 'pi'} for cp in checkpoints]

    # Inject framework tags from the mapping
    checkpoints = [{**cp, 'frameworks': FRAMEWORK_MAP.get(cp['checkpoint_id'], [])} for cp in checkpoints]

    return checkpoints
