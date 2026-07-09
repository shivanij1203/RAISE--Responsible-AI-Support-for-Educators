from django.test import SimpleTestCase

from api.services.project_categorizer import classify_activity


class ClassifyActivityTest(SimpleTestCase):
    """Unit tests for the keyword-based category classifier."""

    def test_empty_input_falls_back_to_research(self) -> None:
        self.assertEqual(classify_activity(''), 'research')
        self.assertEqual(classify_activity(None), 'research')

    def test_no_keywords_falls_back_to_research(self) -> None:
        self.assertEqual(classify_activity('Some unrelated activity name'), 'research')

    def test_grading_keyword_picks_grading(self) -> None:
        self.assertEqual(
            classify_activity('Using Claude to grade essays in MIS 4123'),
            'grading',
        )

    def test_grading_assessment_keyword(self) -> None:
        self.assertEqual(
            classify_activity('Claude for Grading & Assessment'),
            'grading',
        )

    def test_specificity_overrides_priority_for_teaching(self) -> None:
        """'feedback rubric' (15 chars, teaching) beats 'rubric' (6 chars, grading)."""
        self.assertEqual(
            classify_activity('Drafting feedback rubrics with AI for IS 6840'),
            'teaching',
        )

    def test_rubric_alone_picks_grading(self) -> None:
        self.assertEqual(
            classify_activity('Building a grading rubric for the final exam'),
            'grading',
        )

    def test_teaching_keywords(self) -> None:
        self.assertEqual(classify_activity('Course materials for MIS 4123'), 'teaching')
        self.assertEqual(classify_activity('Drafting a syllabus for the fall'), 'teaching')
        self.assertEqual(classify_activity('Lesson plan for week 3'), 'teaching')

    def test_admin_keywords(self) -> None:
        self.assertEqual(classify_activity('Admissions screening pilot'), 'admin')
        self.assertEqual(classify_activity('Reviewing applications for the program'), 'admin')
        self.assertEqual(classify_activity('Hiring committee notes'), 'admin')

    def test_research_keywords(self) -> None:
        self.assertEqual(
            classify_activity('Qualitative coding pilot for student perceptions'),
            'research',
        )
        self.assertEqual(classify_activity('IRB protocol for the spring study'), 'research')
        self.assertEqual(classify_activity('Interview transcripts analysis'), 'research')

    def test_priority_breaks_ties_grading_wins(self) -> None:
        """'rubric' (6 grading) and 'lesson' (6 teaching) — priority picks grading."""
        self.assertEqual(classify_activity('rubric lesson'), 'grading')

    def test_case_insensitive(self) -> None:
        self.assertEqual(classify_activity('GRADING essays'), 'grading')
        self.assertEqual(classify_activity('Syllabus DRAFT'), 'teaching')

    def test_plural_forms_match_via_substring(self) -> None:
        """'rubric' should match 'rubrics' (plural)."""
        self.assertEqual(classify_activity('grading rubrics'), 'grading')
        self.assertEqual(classify_activity('interviews for the study'), 'research')
