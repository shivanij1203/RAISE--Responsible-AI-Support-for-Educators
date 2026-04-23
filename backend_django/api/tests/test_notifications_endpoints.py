"""Tests for /api/notifications endpoints."""
from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project, Checkpoint, Notification


class NotificationsEndpointsTest(TestCase):
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
        self.client.login(username='fac@usf.edu', password='testpass123')

    def _mk(self, **overrides) -> Notification:
        defaults = dict(
            recipient=self.faculty,
            actor=self.student,
            verb=Notification.VERB_CHECKPOINT_COMPLETED,
            project=self.project,
            checkpoint=self.checkpoint,
            message='Stu completed AI Disclosure',
        )
        defaults.update(overrides)
        return Notification.objects.create(**defaults)

    # GET /api/notifications --------------------------------------------

    def test_list_empty(self) -> None:
        response = self.client.get('/api/notifications')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['unreadCount'], 0)
        self.assertEqual(body['notifications'], [])

    def test_list_returns_own_notifications_only(self) -> None:
        self._mk()
        self._mk(recipient=self.student, message='for student')
        response = self.client.get('/api/notifications')
        body = response.json()
        self.assertEqual(len(body['notifications']), 1)
        self.assertEqual(body['unreadCount'], 1)

    def test_list_newest_first(self) -> None:
        first = self._mk(message='first')
        second = self._mk(message='second')
        response = self.client.get('/api/notifications')
        notifs = response.json()['notifications']
        self.assertEqual(notifs[0]['id'], second.id)
        self.assertEqual(notifs[1]['id'], first.id)

    def test_list_serializer_shape(self) -> None:
        self._mk()
        response = self.client.get('/api/notifications')
        n = response.json()['notifications'][0]
        for key in ('id', 'verb', 'message', 'read', 'createdAt',
                    'projectId', 'checkpointId', 'actorName'):
            self.assertIn(key, n)
        self.assertEqual(n['actorName'], 'Stu')
        self.assertEqual(n['projectId'], self.project.id)
        self.assertEqual(n['checkpointId'], 'ai_disclosure')

    def test_list_unread_count_excludes_read(self) -> None:
        self._mk(read=False)
        self._mk(read=True)
        response = self.client.get('/api/notifications')
        self.assertEqual(response.json()['unreadCount'], 1)

    def test_list_requires_auth(self) -> None:
        self.client.logout()
        response = self.client.get('/api/notifications')
        self.assertEqual(response.status_code, 401)

    # POST /api/notifications/<id>/read ---------------------------------

    def test_mark_single_read(self) -> None:
        n = self._mk()
        response = self.client.post(f'/api/notifications/{n.id}/read')
        self.assertEqual(response.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.read)

    def test_mark_read_404_when_not_owned(self) -> None:
        n = self._mk(recipient=self.student)
        response = self.client.post(f'/api/notifications/{n.id}/read')
        self.assertEqual(response.status_code, 404)
        n.refresh_from_db()
        self.assertFalse(n.read)

    def test_mark_read_requires_auth(self) -> None:
        n = self._mk()
        self.client.logout()
        response = self.client.post(f'/api/notifications/{n.id}/read')
        self.assertEqual(response.status_code, 401)

    # POST /api/notifications/read-all ----------------------------------

    def test_mark_all_read(self) -> None:
        self._mk()
        self._mk()
        self._mk(recipient=self.student)  # other user — must not be touched
        response = self.client.post('/api/notifications/read-all')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Notification.objects.filter(recipient=self.faculty, read=False).count(), 0
        )
        self.assertEqual(
            Notification.objects.filter(recipient=self.student, read=False).count(), 1
        )

    def test_read_all_requires_auth(self) -> None:
        self.client.logout()
        response = self.client.post('/api/notifications/read-all')
        self.assertEqual(response.status_code, 401)
