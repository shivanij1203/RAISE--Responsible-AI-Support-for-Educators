"""Smart Defaults — pre-fill draft answers for non-scannable checkpoints.

Most compliance checkpoints are policy attestations, not data-driven checks.
They cannot be auto-verified from a CSV, but they can be answered with high
confidence given the activity's intake context (use case, description, risk
flags, attached tools). RAISE generates a draft attestation per checkpoint
that the user reviews and confirms in one click.

The four scannable checkpoints (data_deidentified, ferpa_compliance,
data_classification, bias_audit / admin_bias_audit) are intentionally
excluded — those have their own automated verification flow.
"""

from __future__ import annotations

from typing import Callable

SCANNABLE_CHECKPOINTS = {
    'data_deidentified',
    'ferpa_compliance',
    'data_classification',
    'bias_audit',
    'admin_bias_audit',
}


def _ctx_use_case_label(ctx: dict) -> str:
    labels = {
        'grading': 'grading and assessment',
        'teaching': 'teaching material development',
        'admin': 'administrative decision-making',
        'qualitative': 'qualitative analysis',
        'data_analysis': 'quantitative data analysis',
        'ml_model': 'AI/ML model development',
        'literature': 'literature review and synthesis',
        'writing': 'writing and editing',
    }
    return labels.get(ctx.get('use_case', ''), ctx.get('use_case', 'this activity'))


def _ctx_tool_phrase(ctx: dict) -> str:
    tools = ctx.get('tools') or []
    if not tools:
        return 'the AI tool used for this activity'
    if len(tools) == 1:
        return tools[0]
    return f"{', '.join(tools[:-1])} and {tools[-1]}"


def _draft_irb(ctx: dict) -> dict:
    use_case = ctx.get('use_case')
    if ctx.get('risk', {}).get('involves_human_subjects'):
        return {
            'description': 'IRB protocol covers AI use for this human-subjects research. An amendment will be filed if AI methods are added or changed.',
            'notes': 'Confirm with PI that the current IRB protocol mentions AI methods. If not, file an amendment before proceeding.',
            'confidence': 'medium',
        }
    if use_case in {'grading', 'teaching', 'admin'}:
        return {
            'description': f'This {_ctx_use_case_label(ctx)} activity is not human-subjects research and does not require IRB approval. Course-related AI use falls outside IRB scope per USF guidance.',
            'notes': 'Reconfirm if any portion of this activity becomes part of a published study.',
            'confidence': 'high',
        }
    return {
        'description': 'IRB review status confirmed for this activity. No human-subjects research is involved at this stage.',
        'notes': 'If activity scope changes to include human subjects, file an IRB amendment.',
        'confidence': 'medium',
    }


def _draft_ai_disclosure(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    use_case_label = _ctx_use_case_label(ctx)
    return {
        'description': f'AI use will be disclosed in the relevant venue (syllabus, methods section, or report) with the following language: "{tool} was used to assist with {use_case_label}. All outputs were reviewed before use."',
        'notes': 'Adjust the disclosure language for the specific publication venue or audience.',
        'confidence': 'high',
    }


def _draft_ai_writing_disclosure(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Writing assistance from {tool} will be disclosed in author notes or methods section: "{tool} was used to assist with drafting and editing. All ideas and final wording are the author\'s responsibility."',
        'notes': 'Required by most journals and conferences for AI-assisted writing.',
        'confidence': 'high',
    }


def _draft_ai_coding_disclosure(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Use of {tool} for code generation will be documented in the project README and any publication: model name, version, and prompts retained for reproducibility.',
        'notes': 'Keep prompt history and tool version in version control alongside the code.',
        'confidence': 'high',
    }


def _draft_admin_disclosure(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Affected stakeholders (applicants, employees, or students) will be informed that {tool} is used in this administrative process, and that human review applies before any final decision.',
        'notes': 'Required under the Colorado AI Act §6-1-1707 for consequential decisions, and aligns with EU AI Act Article 86.',
        'confidence': 'high',
    }


def _draft_teaching_disclosure(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Students will be informed in the course syllabus that {tool} was used to develop teaching materials, and which materials were AI-assisted.',
        'notes': 'Add to syllabus AI Use section before the term begins.',
        'confidence': 'high',
    }


def _draft_data_minimization(ctx: dict) -> dict:
    return {
        'description': f'Only the minimum data necessary for {_ctx_use_case_label(ctx)} will be processed. Identifying fields are removed where possible before any AI tool sees the data.',
        'notes': 'Run the Verify Dataset → Personal info scan / Blind grading flow in RAISE to enforce this automatically.',
        'confidence': 'high',
    }


def _draft_data_storage(ctx: dict) -> dict:
    if ctx.get('risk', {}).get('data_leaves_institution'):
        return {
            'description': 'Data sent to external AI service is not retained beyond the active session. Institutional copies stored on USF-approved storage and disposed at end of semester.',
            'notes': 'Confirm zero-retention setting on the AI tool. For Anthropic Claude, this is the API default; for ChatGPT, requires Enterprise tier or opt-out.',
            'confidence': 'medium',
        }
    return {
        'description': 'Data stored on USF-approved institutional storage for the duration of the activity. Disposed per USF records retention schedule at the end of the semester.',
        'notes': 'Verify storage location complies with USF IT data classification policy.',
        'confidence': 'high',
    }


def _draft_human_review(ctx: dict) -> dict:
    return {
        'description': 'Every AI output is reviewed by a qualified human reviewer before any action is taken on it. No AI decision is auto-applied.',
        'notes': 'For grading, faculty reviews each AI-suggested grade before posting.',
        'confidence': 'high',
    }


def _draft_human_override(ctx: dict) -> dict:
    return {
        'description': 'Faculty retains full authority to override any AI recommendation. AI output is advisory; the final decision is human.',
        'notes': 'Document any case where AI was overridden, for the audit record.',
        'confidence': 'high',
    }


def _draft_decision_impact(ctx: dict) -> dict:
    use_case = ctx.get('use_case', '')
    impact = {
        'grading': 'student grades and academic standing',
        'admin': 'admissions, hiring, or evaluation outcomes',
        'teaching': 'course content reaching students',
    }.get(use_case, 'a person\'s academic record')
    return {
        'description': f'This activity affects {impact}. Human-in-the-loop applies: AI does not finalize any decision without human review.',
        'notes': 'Triggers EU AI Act Article 86 right-to-explanation for affected individuals.',
        'confidence': 'high',
    }


def _draft_grading_fairness(ctx: dict) -> dict:
    return {
        'description': 'Bias audit run on AI grading outputs (4/5ths rule + statistical parity). Grading rubric applied identically across all submissions, with fairness ratio above 0.80.',
        'notes': 'Re-run the bias audit if the rubric, model, or course population changes.',
        'confidence': 'high',
    }


def _draft_grading_transparency(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Students were informed in the course syllabus that {tool} would be used in grading. The AI Use Disclosure section explains how AI assists and where human judgment applies.',
        'notes': 'Distribute syllabus before the first day of class.',
        'confidence': 'high',
    }


def _draft_grading_validation(ctx: dict) -> dict:
    return {
        'description': 'A sample of AI-suggested grades is hand-validated by faculty before any grade is posted. Discrepancies above one rubric band trigger full review.',
        'notes': 'Validate at least 10% of submissions, or 5 per cohort, whichever is higher.',
        'confidence': 'high',
    }


def _draft_appeal_process(ctx: dict) -> dict:
    return {
        'description': 'Students may appeal any AI-influenced grade through the standard course grade-appeal process. The faculty member is the responsible decision-maker on appeal.',
        'notes': 'Reference the syllabus grade-appeal section in the AI Use Disclosure.',
        'confidence': 'high',
    }


def _draft_content_accuracy(ctx: dict) -> dict:
    return {
        'description': 'All AI-generated content is fact-checked by a subject-matter expert before being shared with students or stakeholders. Citations and figures are verified against primary sources.',
        'notes': 'Especially important for AI-generated lecture content and example problem sets.',
        'confidence': 'high',
    }


def _draft_material_review_cycle(ctx: dict) -> dict:
    return {
        'description': 'AI-developed teaching materials are reviewed each semester for accuracy, currency, and alignment with learning outcomes. Updates logged in this activity.',
        'notes': 'Schedule the review at the start of each term.',
        'confidence': 'high',
    }


def _draft_accessibility_check(ctx: dict) -> dict:
    return {
        'description': 'AI-generated content reviewed for accessibility per WCAG 2.1 AA: alt text on images, readable structure, color-contrast checked, no auto-playing media.',
        'notes': 'Run materials through USF Accessibility Checker before publishing.',
        'confidence': 'medium',
    }


def _draft_participant_consent(ctx: dict) -> dict:
    return {
        'description': 'Participants gave informed consent to AI use as part of the IRB-approved consent form. Consent language explicitly names the AI tool and its role.',
        'notes': 'If AI was added after consent was obtained, file an IRB amendment and re-consent.',
        'confidence': 'medium',
    }


def _draft_ip_review(ctx: dict) -> dict:
    tool = _ctx_tool_phrase(ctx)
    return {
        'description': f'Outputs from {tool} reviewed against USF intellectual property policy. No copyrighted training data was reproduced verbatim. Generated content is treated as derivative work and attributed.',
        'notes': 'Especially relevant for AI-generated images, code, and creative writing.',
        'confidence': 'medium',
    }


TEMPLATES: dict[str, Callable[[dict], dict]] = {
    'irb': _draft_irb,
    'ai_disclosure': _draft_ai_disclosure,
    'ai_writing_disclosure': _draft_ai_writing_disclosure,
    'ai_coding_disclosure': _draft_ai_coding_disclosure,
    'admin_disclosure': _draft_admin_disclosure,
    'teaching_disclosure': _draft_teaching_disclosure,
    'data_minimization': _draft_data_minimization,
    'data_storage': _draft_data_storage,
    'human_review': _draft_human_review,
    'human_override': _draft_human_override,
    'decision_impact': _draft_decision_impact,
    'grading_fairness': _draft_grading_fairness,
    'grading_transparency': _draft_grading_transparency,
    'grading_validation': _draft_grading_validation,
    'appeal_process': _draft_appeal_process,
    'content_accuracy': _draft_content_accuracy,
    'material_review_cycle': _draft_material_review_cycle,
    'accessibility_check': _draft_accessibility_check,
    'participant_consent': _draft_participant_consent,
    'ip_review': _draft_ip_review,
}


def generate_smart_defaults(
    use_case: str,
    risk_context: dict,
    tools: list[str],
    incomplete_checkpoints: list[dict],
) -> list[dict]:
    """Return draft attestations for incomplete non-scannable checkpoints.

    incomplete_checkpoints: list of {checkpoint_id, label} for checkpoints
    on the project that are not yet completed.
    """
    ctx = {
        'use_case': use_case,
        'risk': risk_context or {},
        'tools': tools or [],
    }

    drafts: list[dict] = []
    for cp in incomplete_checkpoints:
        cp_id = cp.get('checkpoint_id')
        if cp_id in SCANNABLE_CHECKPOINTS:
            continue
        template = TEMPLATES.get(cp_id)
        if not template:
            continue
        try:
            draft_body = template(ctx)
        except Exception:
            continue
        drafts.append({
            'checkpointId': cp_id,
            'checkpointLabel': cp.get('label', cp_id),
            'suggestedDescription': draft_body['description'],
            'suggestedNotes': draft_body.get('notes', ''),
            'confidence': draft_body.get('confidence', 'medium'),
        })
    return drafts
