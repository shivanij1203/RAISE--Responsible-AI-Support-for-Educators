"""Tests for /api/projects/<id>/checkpoints/<cpid>/comments."""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project, Checkpoint, CheckpointComment


class CheckpointCommentsTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='comm@usf.edu', email='comm@usf.edu',
            password='testpass123', first_name='Commenter',
        )
        UserProfile.objects.create(user=self.user, role='pi')
        self.project = Project.objects.create(
            user=self.user, name='P', ai_use_case='writing',
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='Disclosure', category='Transparency', assigned_to='pi',
        )
        self.client.login(username='comm@usf.edu', password='testpass123')

    def _url(self) -> str:
        return f'/api/projects/{self.project.id}/checkpoints/ai_disclosure/comments'

    def test_list_empty_comments(self) -> None:
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_comment(self) -> None:
        response = self.client.post(
            self._url(),
            data=json.dumps({'text': 'A new observation'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['text'], 'A new observation')
        self.assertEqual(body['userName'], 'Commenter')
        self.assertEqual(body['userRole'], 'pi')

    def test_list_returns_existing_comments(self) -> None:
        CheckpointComment.objects.create(
            checkpoint=self.checkpoint, user=self.user, text='First',
        )
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['text'], 'First')

    def test_create_rejects_empty_text(self) -> None:
        response = self.client.post(
            self._url(),
            data=json.dumps({'text': '   '}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_unauth_blocked(self) -> None:
        self.client.logout()
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 401)

    def test_unknown_project_404(self) -> None:
        response = self.client.get('/api/projects/9999/checkpoints/ai_disclosure/comments')
        self.assertEqual(response.status_code, 404)

    def test_unknown_checkpoint_404(self) -> None:
        response = self.client.get(f'/api/projects/{self.project.id}/checkpoints/unknown/comments')
        self.assertEqual(response.status_code, 404)
