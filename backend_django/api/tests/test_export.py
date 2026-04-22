"""Tests for /api/projects/<id>/export (CSV export)."""
from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project, Checkpoint, Decision


class ProjectExportTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='exp@usf.edu', email='exp@usf.edu',
            password='testpass123',
        )
        UserProfile.objects.create(user=self.user, role='pi')

        self.project = Project.objects.create(
            user=self.user, name='Export Test', ai_use_case='writing',
        )
        self.cp_with_decision = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='Disclosure', category='Transparency', assigned_to='pi',
            completed=True,
        )
        self.cp_without_decision = Checkpoint.objects.create(
            project=self.project, checkpoint_id='bias_audit',
            label='Bias Audit', category='Fairness', assigned_to='pi',
        )
        Decision.objects.create(
            project=self.project, checkpoint=self.cp_with_decision,
            description='Added disclosure',
        )
        self.client.login(username='exp@usf.edu', password='testpass123')

    def test_export_returns_csv(self) -> None:
        response = self.client.get(f'/api/projects/{self.project.id}/export')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Export_Test_compliance.csv', response['Content-Disposition'])

    def test_csv_includes_all_checkpoints(self) -> None:
        response = self.client.get(f'/api/projects/{self.project.id}/export')
        body = response.content.decode('utf-8')
        self.assertIn('ai_disclosure', body)
        self.assertIn('bias_audit', body)
        self.assertIn('Added disclosure', body)

    def test_unknown_project_404(self) -> None:
        response = self.client.get('/api/projects/9999/export')
        self.assertEqual(response.status_code, 404)

    def test_unauth_blocked(self) -> None:
        self.client.logout()
        response = self.client.get(f'/api/projects/{self.project.id}/export')
        self.assertEqual(response.status_code, 401)
