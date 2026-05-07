"""Quick Add parser.

Converts a one-sentence description of an AI activity into the structured
fields RAISE needs: use case, risk context, suggested tools, and a sensible
default name. Today this is deterministic keyword extraction. The signature
is designed so an LLM-backed implementation can replace the body without
touching callers.
"""

from __future__ import annotations

import re
from typing import Iterable

USE_CASE_KEYWORDS: list[tuple[str, list[str]]] = [
    ('grading', [
        r'\bgrad(e|es|ed|ing)\b',
        r'\bscor(e|es|ed|ing)\b',
        r'\bessay(s)?\b',
        r'\bsubmission(s)?\b',
        r'\bmark(s|ed|ing)\b',
        r'\bexam(s|ination)?\b',
        r'\bassessment(s)?\b',
        r'\bassign\w*\b',
    ]),
    ('teaching', [
        r'\bteach(ing)?\b',
        r'\bsyllab\w+\b',
        r'\blesson\b',
        r'\blecture\b',
        r'\btutor\w*\b',
        r'\bcourse material\b',
        r'\bcurriculum\b',
    ]),
    ('admin', [
        r'\badmission(s)?\b',
        r'\bhir\w+\b',
        r'\brecruit\w*\b',
        r'\bschedul\w*\b',
        r'\badministrat\w*\b',
        r'\bemail(s)?\b',
        r'\breport(ing)?\b',
        r'\bapplicant(s)?\b',
        r'\bscreen(ing)?\b',
    ]),
    ('qualitative', [
        r'\binterview(s|ing)?\b',
        r'\btranscrib\w*\b',
        r'\bqualitative\b',
        r'\bthematic\b',
        r'\bopen-?ended\b',
        r'\bfocus group\b',
        r'\bethnograph\w*\b',
    ]),
    ('ml_model', [
        r'\btrain(ing)? a (model|classifier|network)\b',
        r'\bmachine learning\b',
        r'\bneural network\b',
        r'\bdeep learning\b',
        r'\bclassifier\b',
        r'\bpredict\w*\b',
        r'\bbuild(ing)? a model\b',
    ]),
    ('literature', [
        r'\bliterature review\b',
        r'\bsystematic review\b',
        r'\bscoping review\b',
        r'\bcitation(s)?\b',
        r'\breference(s)? \w*\b',
        r'\bpaper(s)?\b',
        r'\bmeta-?analysis\b',
    ]),
    ('writing', [
        r'\bwrit(e|ing|ten)\b',
        r'\bedit(ing|or)?\b',
        r'\bsummar\w+\b',
        r'\bdraft\w*\b',
        r'\bmanuscript\b',
        r'\bproofread\w*\b',
        r'\brewrite\w*\b',
    ]),
    ('data_analysis', [
        r'\bdata analysis\b',
        r'\bregression\b',
        r'\bstatist\w+\b',
        r'\bspreadsheet\b',
        r'\bcsv\b',
        r'\bdataset(s)?\b',
        r'\banalyz\w+ data\b',
    ]),
]

USE_CASE_LABELS: dict[str, str] = {
    'data_analysis': 'Data Analysis',
    'qualitative': 'Qualitative Analysis',
    'ml_model': 'Machine Learning Model',
    'writing': 'Writing & Editing',
    'literature': 'Literature Review',
    'grading': 'Grading & Assessment',
    'teaching': 'Teaching Materials',
    'admin': 'Administrative',
}

STUDENT_DATA_PATTERNS = [
    r'\bstudent(s|\'s)?\b',
    r'\bessay(s)?\b',
    r'\bsubmission(s)?\b',
    r'\bcourse\b',
    r'\bclass\b',
    r'\bferpa\b',
    r'\bgrade(s|d|book)?\b',
    r'\bexam(s)?\b',
    r'\bapplicant(s)?\b',
    r'\benrollee?(s)?\b',
    r'\b[A-Z]{2,4}\s?\d{3,4}[A-Z]?\b',
]

DECISION_PATTERNS = [
    r'\bgrad(e|es|ed|ing)\b',
    r'\badmission(s)?\b',
    r'\bhir\w+\b',
    r'\bevaluat\w+\b',
    r'\bscor(e|es|ed|ing)\b',
    r'\bdecid\w+\b',
    r'\bscreen(ing)?\b',
    r'\bapprov\w+\b',
    r'\brank\w*\b',
    r'\bselect\w+\b',
]

HUMAN_SUBJECTS_PATTERNS = [
    r'\binterview(s|ing|ee|s)?\b',
    r'\bsurvey(s)?\b',
    r'\bparticipant(s)?\b',
    r'\bhuman subjects?\b',
    r'\brespondent(s)?\b',
    r'\bfocus group\b',
    r'\binformed consent\b',
]

EXTERNAL_SERVICE_PATTERNS = [
    r'\bchatgpt\b',
    r'\bopenai\b',
    r'\banthropic\b',
    r'\bclaude\b',
    r'\bgemini\b',
    r'\bcopilot\b',
    r'\bperplexity\b',
    r'\bgrammarly\b',
    r'\botter\b',
    r'\bturnitin\b',
    r'\bgradescope\b',
    r'\bapi\b',
    r'\bthird[- ]party\b',
    r'\bcloud\b',
    r'\bexternal\b',
]


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _detect_use_case(text: str) -> str:
    """Return the highest-scoring use case, or 'data_analysis' as a safe default."""
    scores: dict[str, int] = {}
    for use_case, patterns in USE_CASE_KEYWORDS:
        hits = sum(1 for p in patterns if re.search(p, text, flags=re.IGNORECASE))
        if hits:
            scores[use_case] = hits
    if not scores:
        return 'data_analysis'
    return max(scores.items(), key=lambda kv: kv[1])[0]


def _detect_risk_context(text: str) -> dict[str, bool]:
    return {
        'involves_student_data': _matches_any(text, STUDENT_DATA_PATTERNS),
        'data_leaves_institution': _matches_any(text, EXTERNAL_SERVICE_PATTERNS),
        'affects_decisions': _matches_any(text, DECISION_PATTERNS),
        'involves_human_subjects': _matches_any(text, HUMAN_SUBJECTS_PATTERNS),
    }


def _match_tools(text: str, available_tools: list[dict]) -> list[int]:
    """Return AITool ids whose names appear in the text (case-insensitive substring)."""
    text_lower = text.lower()
    matched: list[int] = []
    for tool in available_tools:
        name = (tool.get('name') or '').strip().lower()
        if not name or len(name) < 3:
            continue
        if name in text_lower:
            matched.append(tool['id'])
    return matched


def _build_name(text: str, use_case: str, matched_tool_names: list[str]) -> str:
    label = USE_CASE_LABELS.get(use_case, use_case.replace('_', ' ').title())
    if matched_tool_names:
        primary = matched_tool_names[0]
        return f'{primary} for {label}'
    snippet = text.strip().rstrip('.').split('.')[0][:60]
    return snippet or label


def _build_notes(use_case: str, risk_context: dict[str, bool], matched_tool_names: list[str]) -> list[str]:
    notes: list[str] = []
    notes.append(f'Use case detected: {USE_CASE_LABELS.get(use_case, use_case)}.')
    if matched_tool_names:
        notes.append(f'Tool(s) recognized from registry: {", ".join(matched_tool_names)}.')
    triggers = [k.replace('_', ' ') for k, v in risk_context.items() if v]
    if triggers:
        notes.append('Risk flags inferred: ' + ', '.join(triggers) + '.')
    else:
        notes.append('No high-risk signals detected. Review and edit if needed.')
    return notes


def parse_activity_description(description: str, available_tools: list[dict]) -> dict:
    """Parse a free-text description into a draft activity.

    available_tools: list of {id, name} dicts from the AITool registry.
    Returns a draft suitable for review and confirmation, not a saved record.
    """
    text = (description or '').strip()
    if not text:
        return {
            'name': '',
            'description': '',
            'ai_use_case': 'data_analysis',
            'risk_context': {
                'involves_student_data': False,
                'data_leaves_institution': False,
                'affects_decisions': False,
                'involves_human_subjects': False,
            },
            'suggested_tool_ids': [],
            'notes': ['No description provided.'],
        }

    use_case = _detect_use_case(text)
    risk_context = _detect_risk_context(text)
    suggested_tool_ids = _match_tools(text, available_tools)

    tools_by_id = {t['id']: t for t in available_tools}
    matched_tool_names = [tools_by_id[tid]['name'] for tid in suggested_tool_ids if tid in tools_by_id]

    return {
        'name': _build_name(text, use_case, matched_tool_names),
        'description': text,
        'ai_use_case': use_case,
        'risk_context': risk_context,
        'suggested_tool_ids': suggested_tool_ids,
        'notes': _build_notes(use_case, risk_context, matched_tool_names),
    }
