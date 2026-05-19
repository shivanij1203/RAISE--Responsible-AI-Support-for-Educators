"""Tests for the re-attach-grades feature: grade_merger service + endpoint."""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import UserProfile
from api.services.grade_merger import merge_graded_with_key

# A name key as produced by pseudonymize_csv: submission_id + identity columns.
KEY_CSV = (
    'submission_id,Student Name\n'
    'STUDENT-001,Alice Smith\n'
    'STUDENT-002,Bob Jones\n'
    'STUDENT-003,Carla Reyes\n'
)

# The anonymized CSV after the AI added a Score column.
GRADED_CSV = (
    'Student Name,Essay,Score\n'
    'STUDENT-001,Essay one,88\n'
    'STUDENT-002,Essay two,73\n'
    'STUDENT-003,Essay three,95\n'
)


class GradeMergerServiceTest(TestCase):
    """Unit tests for merge_graded_with_key."""

    def test_merges_grades_back_to_names(self) -> None:
        result = merge_graded_with_key(GRADED_CSV, KEY_CSV)
        self.assertEqual(result['summary']['matchedRows'], 3)
        self.assertEqual(result['summary']['unmatchedRows'], 0)
        self.assertEqual(result['summary']['missingFromGraded'], 0)
        # Real names and grades land together; codes are gone.
        self.assertIn('Alice Smith', result['content'])
        self.assertIn('88', result['content'])
        self.assertNotIn('STUDENT-001', result['content'])
        # The merged header leads with the identity column.
        self.assertTrue(result['content'].startswith('Student Name,Essay,Score'))

    def test_unmatched_code_is_reported(self) -> None:
        graded = GRADED_CSV + 'STUDENT-999,Mystery essay,50\n'
        result = merge_graded_with_key(graded, KEY_CSV)
        self.assertEqual(result['summary']['matchedRows'], 3)
        self.assertEqual(result['summary']['unmatchedRows'], 1)
        self.assertIn('STUDENT-999', result['summary']['unmatchedCodes'])

    def test_missing_grade_is_reported(self) -> None:
        # Graded file is missing STUDENT-003.
        graded = (
            'Student Name,Essay,Score\n'
            'STUDENT-001,Essay one,88\n'
            'STUDENT-002,Essay two,73\n'
        )
        result = merge_graded_with_key(graded, KEY_CSV)
        self.assertEqual(result['summary']['matchedRows'], 2)
        self.assertEqual(result['summary']['missingFromGraded'], 1)
        self.assertIn('STUDENT-003', result['summary']['missingCodes'])

    def test_key_without_identity_column_rejected(self) -> None:
        with self.assertRaises(ValueError):
            merge_graded_with_key(GRADED_CSV, 'submission_id\nSTUDENT-001\n')

    def test_graded_file_without_codes_rejected(self) -> None:
        no_codes = 'Student Name,Essay,Score\nAlice Smith,Essay one,88\n'
        with self.assertRaises(ValueError):
            merge_graded_with_key(no_codes, KEY_CSV)


class MergeGradesEndpointTest(TestCase):
    """Tests for POST /api/verify/merge-grades."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='merge@usf.edu', email='merge@usf.edu',
            password='testpass123', first_name='Merger',
        )
        UserProfile.objects.create(user=self.user, role='pi')

    def _graded(self) -> SimpleUploadedFile:
        return SimpleUploadedFile('graded.csv', GRADED_CSV.encode('utf-8'), content_type='text/csv')

    def _key(self) -> SimpleUploadedFile:
        return SimpleUploadedFile('name_key.csv', KEY_CSV.encode('utf-8'), content_type='text/csv')

    def test_unauth_blocked(self) -> None:
        response = self.client.post('/api/verify/merge-grades', {
            'graded_file': self._graded(), 'key_file': self._key(),
        })
        self.assertEqual(response.status_code, 401)

    def test_missing_files_rejected(self) -> None:
        self.client.login(username='merge@usf.edu', password='testpass123')
        response = self.client.post('/api/verify/merge-grades', {'graded_file': self._graded()})
        self.assertEqual(response.status_code, 400)

    def test_non_csv_rejected(self) -> None:
        self.client.login(username='merge@usf.edu', password='testpass123')
        bad = SimpleUploadedFile('graded.txt', GRADED_CSV.encode('utf-8'), content_type='text/plain')
        response = self.client.post('/api/verify/merge-grades', {
            'graded_file': bad, 'key_file': self._key(),
        })
        self.assertEqual(response.status_code, 400)

    def test_merge_succeeds(self) -> None:
        self.client.login(username='merge@usf.edu', password='testpass123')
        response = self.client.post('/api/verify/merge-grades', {
            'graded_file': self._graded(), 'key_file': self._key(),
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['summary']['matchedRows'], 3)
        self.assertIn('Alice Smith', body['content'])

    def test_graded_file_without_codes_returns_400(self) -> None:
        self.client.login(username='merge@usf.edu', password='testpass123')
        no_codes = SimpleUploadedFile(
            'graded.csv',
            b'Student Name,Essay,Score\nAlice Smith,Essay one,88\n',
            content_type='text/csv',
        )
        response = self.client.post('/api/verify/merge-grades', {
            'graded_file': no_codes, 'key_file': self._key(),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('codes', response.json()['error'].lower())
