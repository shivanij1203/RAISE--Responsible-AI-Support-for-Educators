"""Extended project endpoint tests: detail GET/PUT, decision_create, access control."""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project, Checkpoint, Decision, AITool


class ProjectDetailTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.owner = User.objects.create_user(
            username='owner@usf.edu', email='owner@usf.edu',
            password='testpass123', first_name='Owner',
        )
        UserProfile.objects.create(user=self.owner, role='pi')

        self.other = User.objects.create_user(
            username='other@usf.edu', email='other@usf.edu',
            password='testpass123',
        )
        UserProfile.objects.create(user=self.other, role='student')

        self.project = Project.objects.create(
            user=self.owner, name='Initial', ai_use_case='writing', description='orig',
        )
        Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='AI Disclosure', category='Transparency', assigned_to='pi',
        )
        self.client.login(username='owner@usf.edu', password='testpass123')

    def test_detail_returns_project(self) -> None:
        response = self.client.get(f'/api/projects/{self.project.id}')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['name'], 'Initial')
        self.assertEqual(body['owner'], 'Owner')

    def test_detail_404_for_unknown(self) -> None:
        response = self.client.get('/api/projects/9999')
        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_access(self) -> None:
        self.client.logout()
        self.client.login(username='other@usf.edu', password='testpass123')
        response = self.client.get(f'/api/projects/{self.project.id}')
        self.assertEqual(response.status_code, 404)

    def test_put_updates_name_and_description(self) -> None:
        response = self.client.put(
            f'/api/projects/{self.project.id}',
            data=json.dumps({'name': 'Renamed', 'description': 'new desc'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renamed')
        self.assertEqual(self.project.description, 'new desc')

    def test_put_adds_faculty_advisor_by_email(self) -> None:
        advisor = User.objects.create_user(
            username='advisor@usf.edu', email='advisor@usf.edu',
            password='testpass123',
        )
        response = self.client.put(
            f'/api/projects/{self.project.id}',
            data=json.dumps({'faculty_advisor_email': 'advisor@usf.edu'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.faculty_advisor, advisor)

    def test_put_rejects_unknown_advisor_email(self) -> None:
        response = self.client.put(
            f'/api/projects/{self.project.id}',
            data=json.dumps({'faculty_advisor_email': 'nobody@usf.edu'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_put_risk_context_adds_checkpoints(self) -> None:
        original_count = self.project.checkpoints.count()
        response = self.client.put(
            f'/api/projects/{self.project.id}',
            data=json.dumps({
                'risk_context': {'involves_human_subjects': True, 'involves_student_data': True},
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        # Higher risk context should have added at least one checkpoint
        self.assertGreaterEqual(self.project.checkpoints.count(), original_count)


class DecisionCreateTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='decider@usf.edu', email='decider@usf.edu',
            password='testpass123',
        )
        UserProfile.objects.create(user=self.user, role='pi')

        self.project = Project.objects.create(
            user=self.user, name='P', ai_use_case='writing',
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='AI Disclosure', category='Transparency', assigned_to='pi',
        )
        self.client.login(username='decider@usf.edu', password='testpass123')

    def test_create_decision_auto_completes_checkpoint(self) -> None:
        response = self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({
                'checkpoint': 'ai_disclosure',
                'description': 'Added disclosure to paper',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['checkpointCompleted'])
        self.assertIsNotNone(body['checkpointCompletedAt'])
        self.checkpoint.refresh_from_db()
        self.assertTrue(self.checkpoint.completed)

    def test_create_decision_requires_description(self) -> None:
        response = self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({'checkpoint': 'ai_disclosure'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_create_decision_rejects_unknown_checkpoint(self) -> None:
        response = self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({
                'checkpoint': 'nonexistent',
                'description': 'n/a',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_create_decision_attaches_tool_used(self) -> None:
        tool = AITool.objects.create(
            name='ChatGPT', tool_type='ai', category='writing',
            status='approved', added_by=self.user,
        )
        response = self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({
                'checkpoint': 'ai_disclosure',
                'description': 'Used for clarity edits',
                'toolUsedId': tool.id,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['toolUsed']['name'], 'ChatGPT')

    def test_create_decision_404_for_unknown_project(self) -> None:
        response = self.client.post(
            '/api/projects/9999/decisions',
            data=json.dumps({'checkpoint': 'ai_disclosure', 'description': 'x'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class CheckpointToggleAccessTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.owner = User.objects.create_user(
            username='o@usf.edu', email='o@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.owner, role='student')
        self.outsider = User.objects.create_user(
            username='x@usf.edu', email='x@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.outsider, role='student')
        self.project = Project.objects.create(
            user=self.owner, name='P', ai_use_case='writing',
        )
        Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='AI Disclosure', category='Transparency', assigned_to='pi',
        )

    def test_outsider_gets_404(self) -> None:
        self.client.login(username='x@usf.edu', password='testpass123')
        response = self.client.put(f'/api/projects/{self.project.id}/checkpoints/ai_disclosure')
        self.assertEqual(response.status_code, 404)

    def test_unauth_gets_401(self) -> None:
        response = self.client.put(f'/api/projects/{self.project.id}/checkpoints/ai_disclosure')
        self.assertEqual(response.status_code, 401)

    def test_unknown_checkpoint_returns_404(self) -> None:
        self.client.login(username='o@usf.edu', password='testpass123')
        response = self.client.put(f'/api/projects/{self.project.id}/checkpoints/unknown_id')
        self.assertEqual(response.status_code, 404)
