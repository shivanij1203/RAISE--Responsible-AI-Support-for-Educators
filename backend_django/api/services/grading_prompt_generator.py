"""Grading Prompt Generator.

Builds a structured grading prompt for an external AI tool (Claude, ChatGPT,
Gemini, Copilot) given an activity and the faculty's rubric. The output is
intended to be copy-pasted into the AI tool, and the same text is stored as
audit evidence against the activity so there is a record of exactly how the
AI was instructed.
"""

from __future__ import annotations

from datetime import datetime, timezone


TOOL_TAG_STYLE = {
    'claude': 'xml',
    'anthropic': 'xml',
    'chatgpt': 'markdown',
    'openai': 'markdown',
    'gpt': 'markdown',
    'gemini': 'markdown',
    'google': 'markdown',
    'copilot': 'markdown',
    'perplexity': 'markdown',
}


def _tag_style_for(tool_name: str | None) -> str:
    if not tool_name:
        return 'markdown'
    name = tool_name.lower()
    for key, style in TOOL_TAG_STYLE.items():
        if key in name:
            return style
    return 'markdown'


def _wrap(label: str, body: str, style: str) -> str:
    body = body.strip()
    if style == 'xml':
        tag = label.lower().replace(' ', '_')
        return f'<{tag}>\n{body}\n</{tag}>'
    return f'### {label}\n{body}'


def _compliance_block(risk_context: dict) -> list[str]:
    lines: list[str] = []
    if risk_context.get('involves_student_data'):
        lines.append(
            'This data is protected under FERPA. Do not retain it after grading. '
            'Do not use it to train, fine-tune, or improve any model.'
        )
    if risk_context.get('affects_decisions'):
        lines.append(
            'Your output will inform an academic decision affecting a student. '
            'Apply the rubric consistently across every submission. '
            'Do not consider any visible student identity (name, email, ID, demographic). '
            'If you encounter such information, ignore it.'
        )
    if not lines:
        lines.append(
            'Apply the rubric consistently across every submission. '
            'Do not consider any visible student identity. '
            'Treat the work, not the author.'
        )
    return lines


def _output_format_block() -> str:
    return (
        'Return one JSON object per submission, in a JSON array. Each object must contain:\n'
        '  - "submission_id": the anonymous code on the submission\n'
        '  - "score": numeric score (use the scale defined in the rubric)\n'
        '  - "rationale": 2 to 3 sentences explaining the score against the rubric\n'
        '  - "concerns": null, or a short string describing why a submission could not be graded\n'
        '\n'
        'Do not produce any text outside the JSON array. Do not echo the rubric. '
        'If a submission cannot be graded, set "score" to null and explain in "concerns".'
    )


def generate_grading_prompt(
    activity_name: str,
    activity_description: str,
    rubric_text: str,
    risk_context: dict | None = None,
    ai_tool_name: str | None = None,
) -> dict:
    """Generate a copy-pasteable grading prompt plus metadata.

    Returns a dict with:
      - prompt: the assembled text the faculty pastes into the AI tool
      - tool: the resolved tool name (or 'AI tool' if unknown)
      - tag_style: 'xml' or 'markdown'
      - includes: list of guardrails that were inserted, for the audit record
      - generated_at: ISO timestamp
    """
    risk_context = risk_context or {}
    style = _tag_style_for(ai_tool_name)
    tool_label = ai_tool_name or 'the AI tool'

    role = (
        f'You are an unbiased academic grader assisting with the activity '
        f'"{activity_name.strip()}". Your job is to apply the rubric below to each '
        f'student submission and produce a structured grade.'
    )

    task = activity_description.strip() or (
        'Grade the student submissions that follow. Use the rubric below as the '
        'sole basis for scoring.'
    )

    compliance_lines = _compliance_block(risk_context)
    compliance = '\n'.join(f'- {line}' for line in compliance_lines)

    sections = [
        _wrap('Role', role, style),
        _wrap('Task', task, style),
        _wrap('Rubric', rubric_text.strip(), style),
        _wrap('Hard requirements', compliance, style),
        _wrap('Output format', _output_format_block(), style),
        _wrap(
            'Submissions',
            'The submissions appear below this block. Each carries an anonymous code '
            'such as STUDENT-001. Use that code as the submission_id in your output.',
            style,
        ),
    ]

    prompt = '\n\n'.join(sections)

    includes = ['rubric', 'fairness_language', 'output_format']
    if risk_context.get('involves_student_data'):
        includes.append('ferpa_notice')
    if risk_context.get('affects_decisions'):
        includes.append('decision_warning')

    return {
        'prompt': prompt,
        'tool': tool_label,
        'tagStyle': style,
        'includes': includes,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
    }
