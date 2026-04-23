"""Tests that existing endpoints fire notifications as a side effect."""
import io
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import (
    UserProfile, Project, Checkpoint, CheckpointComment, Notification,
)


class NotificationWiringTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.student = User.objects.create_user(
            username='stu@usf.edu', email='stu@usf.edu',
            password='testpass123', first_name='Stu',
        )
        UserProfile.objects.create(user=self.student, role='student')
        self.faculty = User.objects.create_user(
            username='fac@usf.edu', email='fac@usf.edu',
            password='testpass123', first_name='Fac',
        )
        UserProfile.objects.create(user=self.faculty, role='pi')
        self.project = Project.objects.create(
            user=self.student, name='Thesis', ai_use_case='writing',
            faculty_advisor=self.faculty,
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='AI Disclosure', category='Transparency',
            assigned_to='student',
        )

    # checkpoint toggle -------------------------------------------------

    def test_completing_checkpoint_notifies_advisor(self) -> None:
        self.client.login(username='stu@usf.edu', password='testpass123')
        self.client.put(
            f'/api/projects/{self.project.id}/checkpoints/ai_disclosure'
        )
        notifs = Notification.objects.filter(recipient=self.faculty)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().verb, Notification.VERB_CHECKPOINT_COMPLETED)

    def test_uncompleting_checkpoint_does_not_notify(self) -> None:
        self.checkpoint.completed = True
        self.checkpoint.save()
        self.client.login(username='stu@usf.edu', password='testpass123')
        self.client.put(
            f'/api/projects/{self.project.id}/checkpoints/ai_disclosure'
        )
        self.assertEqual(Notification.objects.count(), 0)

    # decision create (auto-completes) ----------------------------------

    def test_decision_create_notifies_on_auto_complete(self) -> None:
        self.client.login(username='stu@usf.edu', password='testpass123')
        self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({
                'checkpoint': 'ai_disclosure',
                'description': 'Added disclosure note',
            }),
            content_type='application/json',
        )
        notifs = Notification.objects.filter(recipient=self.faculty)
        self.assertEqual(notifs.count(), 1)

    def test_decision_create_no_notify_when_already_completed(self) -> None:
        self.checkpoint.completed = True
        self.checkpoint.save()
        self.client.login(username='stu@usf.edu', password='testpass123')
        self.client.post(
            f'/api/projects/{self.project.id}/decisions',
            data=json.dumps({
                'checkpoint': 'ai_disclosure',
                'description': 'Amended note',
            }),
            content_type='application/json',
        )
        self.assertEqual(Notification.objects.count(), 0)

    # comment create -----------------------------------------------------

    def test_comment_create_notifies_other_party(self) -> None:
        self.client.login(username='fac@usf.edu', password='testpass123')
        self.client.post(
            f'/api/projects/{self.project.id}/checkpoints/ai_disclosure/comments',
            data=json.dumps({'text': 'Please add more detail'}),
            content_type='application/json',
        )
        notifs = Notification.objects.filter(recipient=self.student)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().verb, Notification.VERB_COMMENT_ADDED)

    # verification -------------------------------------------------------

    def test_pii_scan_with_checkpoint_context_notifies_student(self) -> None:
        self.client.login(username='fac@usf.edu', password='testpass123')
        csv = io.BytesIO(b"name,email\nAlice,a@x.com\n")
        csv.name = 'test.csv'
        self.client.post(
            '/api/verify/scan-pii',
            data={
                'file': csv,
                'scan_type': 'pii',
                'project_id': self.project.id,
                'checkpoint_id': 'ai_disclosure',
            },
        )
        notifs = Notification.objects.filter(recipient=self.student)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().verb, Notification.VERB_VERIFICATION_RUN)

    def test_pii_scan_without_checkpoint_context_does_not_notify(self) -> None:
        self.client.login(username='fac@usf.edu', password='testpass123')
        csv = io.BytesIO(b"name,email\nAlice,a@x.com\n")
        csv.name = 'test.csv'
        self.client.post(
            '/api/verify/scan-pii',
            data={'file': csv, 'scan_type': 'pii'},
        )
        self.assertEqual(Notification.objects.count(), 0)
