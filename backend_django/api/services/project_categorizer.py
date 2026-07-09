"""Keyword-based classifier for Project.category.

Used by the 0017 data migration to backfill existing activities, and
available at runtime for any future feature that wants to suggest a
category from an activity's text.
"""

PROJECT_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    'grading': [
        'grading',
        'grade',
        'grader',
        'rubric',
        'assess',
        'score',
    ],
    'teaching': [
        'rubric drafting',
        'course materials',
        'lesson',
        'syllabus',
        'teaching',
        'feedback rubric',
    ],
    'admin': [
        'admissions',
        'screening',
        'applications',
        'scheduling',
        'hiring',
    ],
    'research': [
        'qualitative coding',
        'interview',
        'research',
        'irb',
        'transcripts',
        'study',
    ],
}

# Tie-break order when two keywords have the same length.
CATEGORY_PRIORITY: list[str] = ['grading', 'teaching', 'admin', 'research']

DEFAULT_CATEGORY = 'research'


def classify_activity(text: str | None) -> str:
    """Pick a category for an activity using keyword matching.

    Algorithm: find every keyword hit across all categories. The longest
    matched keyword wins (more specific phrase = more accurate signal).
    Ties are broken by CATEGORY_PRIORITY. If no keywords match anywhere
    in the text, fall back to DEFAULT_CATEGORY.
    """
    if not text:
        return DEFAULT_CATEGORY

    lowered = text.lower()
    matches: list[tuple[int, int, str]] = []  # (-length, priority_index, category)
    for category, keywords in PROJECT_CATEGORY_KEYWORDS.items():
        priority_index = CATEGORY_PRIORITY.index(category)
        for kw in keywords:
            if kw.lower() in lowered:
                matches.append((-len(kw), priority_index, category))

    if not matches:
        return DEFAULT_CATEGORY

    matches.sort()  # negative length first (longest), then priority (lowest first)
    return matches[0][2]
