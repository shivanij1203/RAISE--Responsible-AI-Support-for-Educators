"""Tests for /api/dashboard/stats."""
from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project, Checkpoint, Decision, AITool


class DashboardStatsTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash@usf.edu', email='dash@usf.edu',
            password='testpass123', first_name='Dash',
        )
        UserProfile.objects.create(user=self.user, role='pi')

        self.project = Project.objects.create(
            user=self.user, name='My Activity', ai_use_case='writing',
        )
        self.cp_done = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='Disclosure', category='Transparency', assigned_to='pi',
            completed=True,
        )
        self.cp_critical = Checkpoint.objects.create(
            project=self.project, checkpoint_id='irb',
            label='IRB', category='Regulatory', assigned_to='pi',
            completed=False,
        )
        Decision.objects.create(
            project=self.project, checkpoint=self.cp_done,
            description='Added disclosure to methods',
        )
        AITool.objects.create(
            name='ChatGPT', tool_type='ai', category='writing',
            status='approved', added_by=self.user,
        )
        self.client.login(username='dash@usf.edu', password='testpass123')

    def test_stats_returns_core_fields(self) -> None:
        response = self.client.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['totalActivities'], 1)
        self.assertIn('avgCompliance', body)
        self.assertIn('riskBreakdown', body)
        self.assertIn('recentFeed', body)
        self.assertIn('toolStats', body)
        self.assertEqual(body['userName'], 'Dash')

    def test_stats_flags_high_risk_when_critical_incomplete(self) -> None:
        response = self.client.get('/api/dashboard/stats')
        body = response.json()
        # irb (critical) is incomplete → high risk
        self.assertEqual(body['riskBreakdown']['high'], 1)

    def test_stats_includes_tool_counts(self) -> None:
        response = self.client.get('/api/dashboard/stats')
        body = response.json()
        self.assertEqual(body['toolStats']['total'], 1)
        self.assertEqual(body['toolStats']['byStatus']['approved'], 1)

    def test_stats_scope_all_for_faculty(self) -> None:
        response = self.client.get('/api/dashboard/stats?scope=all')
        self.assertEqual(response.status_code, 200)

    def test_stats_requires_auth(self) -> None:
        self.client.logout()
        response = self.client.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 401)
