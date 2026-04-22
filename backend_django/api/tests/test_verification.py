"""Tests for verification endpoints: /verify/scan-pii, /verify/classify-data,
/verify/bias-audit, /verify/file-columns."""
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from api.models import UserProfile


def _make_user() -> User:
    user = User.objects.create_user(
        username='verify@usf.edu',
        email='verify@usf.edu',
        password='testpass123',
        first_name='Verify',
    )
    UserProfile.objects.create(user=user, role='pi')
    return user


class ScanPIITest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = _make_user()
        self.client.login(username='verify@usf.edu', password='testpass123')

    def test_scan_detects_email_column(self) -> None:
        csv_bytes = b'full_name,email,course\nJane,jane@example.com,CS101\n'
        file = SimpleUploadedFile('test.csv', csv_bytes, content_type='text/csv')
        response = self.client.post('/api/verify/scan-pii', {'file': file})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['hasPII'])

    def test_scan_rejects_non_csv(self) -> None:
        file = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        response = self.client.post('/api/verify/scan-pii', {'file': file})
        self.assertEqual(response.status_code, 400)

    def test_scan_rejects_missing_file(self) -> None:
        response = self.client.post('/api/verify/scan-pii', {})
        self.assertEqual(response.status_code, 400)

    def test_scan_rejects_oversized_file(self) -> None:
        big = SimpleUploadedFile('big.csv', b'x' * (11 * 1024 * 1024), content_type='text/csv')
        response = self.client.post('/api/verify/scan-pii', {'file': big})
        self.assertEqual(response.status_code, 400)

    def test_scan_rejects_invalid_utf8(self) -> None:
        file = SimpleUploadedFile('bad.csv', b'\xff\xfe\x00\x01', content_type='text/csv')
        response = self.client.post('/api/verify/scan-pii', {'file': file})
        self.assertEqual(response.status_code, 400)

    def test_ferpa_scan_adds_ferpa_specific_block(self) -> None:
        csv_bytes = b'student_id,grade\n12345,A\n12346,B\n'
        file = SimpleUploadedFile('grades.csv', csv_bytes, content_type='text/csv')
        response = self.client.post('/api/verify/scan-pii', {'file': file, 'scan_type': 'ferpa'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('ferpaSpecific', response.json())

    def test_scan_unauthenticated_blocked(self) -> None:
        self.client.logout()
        file = SimpleUploadedFile('test.csv', b'a,b\n1,2\n', content_type='text/csv')
        response = self.client.post('/api/verify/scan-pii', {'file': file})
        self.assertEqual(response.status_code, 401)


class ClassifyDataTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        _make_user()
        self.client.login(username='verify@usf.edu', password='testpass123')

    def test_classify_returns_level(self) -> None:
        response = self.client.post(
            '/api/verify/classify-data',
            data={'description': 'Student grades and GPA information'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestedLevel', response.json())

    def test_classify_missing_description(self) -> None:
        response = self.client.post(
            '/api/verify/classify-data',
            data={},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class BiasAuditViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        _make_user()
        self.client.login(username='verify@usf.edu', password='testpass123')

    def test_returns_columns_when_not_specified(self) -> None:
        csv_bytes = b'group,outcome\nA,yes\nB,no\n'
        file = SimpleUploadedFile('d.csv', csv_bytes, content_type='text/csv')
        response = self.client.post('/api/verify/bias-audit', {'file': file})
        self.assertEqual(response.status_code, 200)
        self.assertIn('columns', response.json())

    def test_runs_audit_with_columns(self) -> None:
        rows = [b'group,outcome']
        rows.extend([b'A,yes'] * 6 + [b'A,no'] * 4)
        rows.extend([b'B,yes'] * 6 + [b'B,no'] * 4)
        csv_bytes = b'\n'.join(rows) + b'\n'
        file = SimpleUploadedFile('d.csv', csv_bytes, content_type='text/csv')
        response = self.client.post('/api/verify/bias-audit', {
            'file': file,
            'outcome_column': 'outcome',
            'protected_column': 'group',
            'positive_value': 'yes',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('verdict', response.json())

    def test_rejects_non_csv(self) -> None:
        file = SimpleUploadedFile('bad.txt', b'hello', content_type='text/plain')
        response = self.client.post('/api/verify/bias-audit', {'file': file})
        self.assertEqual(response.status_code, 400)


class FileColumnsTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        _make_user()
        self.client.login(username='verify@usf.edu', password='testpass123')

    def test_returns_columns(self) -> None:
        file = SimpleUploadedFile('d.csv', b'col1,col2\nx,y\n', content_type='text/csv')
        response = self.client.post('/api/verify/file-columns', {'file': file})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['columns'], ['col1', 'col2'])

    def test_rejects_missing_file(self) -> None:
        response = self.client.post('/api/verify/file-columns', {})
        self.assertEqual(response.status_code, 400)
