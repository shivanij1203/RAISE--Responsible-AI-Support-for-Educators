"""Tests for the activity audit log: event recording + the timeline endpoint."""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import (
    ActivityEvent,
    Checkpoint,
    CheckpointComment,
    Project,
    UserProfile,
)


class AuditEventRecordingTest(TestCase):
    """Verifies that view actions append the expected ActivityEvent rows."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='audit@usf.edu', email='audit@usf.edu',
            password='testpass123', first_name='Auditor',
        )
        UserProfile.objects.create(user=self.user, role='pi')
        self.project = Project.objects.create(
            user=self.user, name='Audited Activity', ai_use_case='writing',
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='Disclosure', category='Transparency', assigned_to='pi',
        )
        self.client.login(username='audit@usf.edu', password='testpass123')

    def _events(self, event_type: str):
        return ActivityEvent.objects.filter(project=self.project, event_type=event_type)

    def test_checkpoint_toggle_records_completed_then_reopened(self) -> None:
        url = f'/api/projects/{self.project.id}/checkpoints/ai_disclosure'
        self.client.put(url)
        self.assertEqual(self._events(ActivityEvent.EVENT_CHECKPOINT_COMPLETED).count(), 1)

        self.client.put(url)
        self.assertEqual(self._events(ActivityEvent.EVENT_CHECKPOINT_REOPENED).count(), 1)

        completed = self._events(ActivityEvent.EVENT_CHECKPOINT_COMPLETED).first()
        self.assertEqual(completed.actor, self.user)
        self.assertEqual(completed.checkpoint, self.checkpoint)

    def test_decision_create_records_decision_and_completion(self) -> None:
        response = self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({'checkpoint': 'ai_disclosure', 'description': 'Did the thing'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self._events(ActivityEvent.EVENT_DECISION_LOGGED).count(), 1)
        # The checkpoint was incomplete, so logging a decision auto-completes it.
        self.assertEqual(self._events(ActivityEvent.EVENT_CHECKPOINT_COMPLETED).count(), 1)
        decision_event = self._events(ActivityEvent.EVENT_DECISION_LOGGED).first()
        self.assertEqual(decision_event.metadata.get('description'), 'Did the thing')

    def test_comment_add_and_resolve_record_events(self) -> None:
        comments_url = (
            f'/api/projects/{self.project.id}/checkpoints/ai_disclosure/comments'
        )
        self.client.post(
            comments_url,
            data=json.dumps({'text': 'A question'}),
            content_type='application/json',
        )
        self.assertEqual(self._events(ActivityEvent.EVENT_COMMENT_ADDED).count(), 1)

        comment = CheckpointComment.objects.get(checkpoint=self.checkpoint)
        self.client.post(
            f'{comments_url}/{comment.id}/resolve',
            data=json.dumps({'resolved': True}),
            content_type='application/json',
        )
        self.assertEqual(self._events(ActivityEvent.EVENT_COMMENT_RESOLVED).count(), 1)


class TimelineEndpointTest(TestCase):
    """Tests for GET /api/projects/<id>/timeline."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner@usf.edu', email='owner@usf.edu',
            password='testpass123', first_name='Owner',
        )
        UserProfile.objects.create(user=self.user, role='pi')
        self.other = User.objects.create_user(
            username='stranger@usf.edu', email='stranger@usf.edu',
            password='testpass123', first_name='Stranger',
        )
        self.project = Project.objects.create(
            user=self.user, name='Timeline Activity', ai_use_case='writing',
        )

    def _url(self, project_id=None) -> str:
        return f'/api/projects/{project_id or self.project.id}/timeline'

    def test_unauth_blocked(self) -> None:
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 401)

    def test_returns_events_newest_first(self) -> None:
        ActivityEvent.objects.create(
            project=self.project, actor=self.user,
            event_type=ActivityEvent.EVENT_ACTIVITY_CREATED, summary='first',
        )
        ActivityEvent.objects.create(
            project=self.project, actor=self.user,
            event_type=ActivityEvent.EVENT_CHECKPOINT_COMPLETED, summary='second',
        )
        self.client.login(username='owner@usf.edu', password='testpass123')
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 2)
        self.assertEqual(body[0]['summary'], 'second')
        self.assertEqual(body[0]['eventType'], 'checkpoint_completed')
        self.assertEqual(body[0]['actorName'], 'Owner')

    def test_stranger_cannot_see_timeline(self) -> None:
        self.client.login(username='stranger@usf.edu', password='testpass123')
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 404)

    def test_unknown_project_404(self) -> None:
        self.client.login(username='owner@usf.edu', password='testpass123')
        response = self.client.get(self._url(project_id=999999))
        self.assertEqual(response.status_code, 404)

    def test_project_create_records_activity_created_event(self) -> None:
        self.client.login(username='owner@usf.edu', password='testpass123')
        response = self.client.post(
            '/api/projects',
            data=json.dumps({'name': 'Brand New', 'ai_use_case': 'writing'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        new_id = response.json()['id']
        events = ActivityEvent.objects.filter(
            project_id=new_id, event_type=ActivityEvent.EVENT_ACTIVITY_CREATED,
        )
        self.assertEqual(events.count(), 1)
