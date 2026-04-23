"""Tests for the Notification model."""
from django.test import TestCase
from django.contrib.auth.models import User

from api.models import Project, Checkpoint, Notification


class NotificationModelTest(TestCase):
    def setUp(self) -> None:
        self.student = User.objects.create_user(
            username='stu@usf.edu', email='stu@usf.edu',
            password='x', first_name='Stu',
        )
        self.faculty = User.objects.create_user(
            username='fac@usf.edu', email='fac@usf.edu',
            password='x', first_name='Fac',
        )
        self.project = Project.objects.create(
            user=self.student, name='Thesis', ai_use_case='writing',
            faculty_advisor=self.faculty,
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='Disclosure', category='Transparency', assigned_to='student',
        )

    def test_create_notification_with_all_fields(self) -> None:
        notif = Notification.objects.create(
            recipient=self.faculty,
            actor=self.student,
            verb='checkpoint_completed',
            project=self.project,
            checkpoint=self.checkpoint,
            message='Stu completed Disclosure',
        )
        self.assertEqual(notif.recipient, self.faculty)
        self.assertEqual(notif.actor, self.student)
        self.assertEqual(notif.verb, 'checkpoint_completed')
        self.assertFalse(notif.read)
        self.assertIsNotNone(notif.created_at)

    def test_default_read_is_false(self) -> None:
        notif = Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='comment_added', project=self.project, message='x',
        )
        self.assertFalse(notif.read)

    def test_checkpoint_is_nullable(self) -> None:
        notif = Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='checkpoint_completed', project=self.project, message='x',
        )
        self.assertIsNone(notif.checkpoint)

    def test_ordered_newest_first(self) -> None:
        first = Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='comment_added', project=self.project, message='first',
        )
        second = Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='comment_added', project=self.project, message='second',
        )
        ordered = list(Notification.objects.all())
        self.assertEqual(ordered[0].id, second.id)
        self.assertEqual(ordered[1].id, first.id)

    def test_cascade_on_recipient_delete(self) -> None:
        Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='comment_added', project=self.project, message='x',
        )
        self.faculty.delete()
        self.assertEqual(Notification.objects.count(), 0)

    def test_set_null_on_actor_delete(self) -> None:
        other_actor = User.objects.create_user(
            username='other@usf.edu', email='other@usf.edu', password='x',
        )
        notif = Notification.objects.create(
            recipient=self.faculty, actor=other_actor,
            verb='comment_added', project=self.project, message='x',
        )
        other_actor.delete()
        notif.refresh_from_db()
        self.assertIsNone(notif.actor)

    def test_string_representation(self) -> None:
        notif = Notification.objects.create(
            recipient=self.faculty, actor=self.student,
            verb='checkpoint_completed', project=self.project,
            checkpoint=self.checkpoint, message='Stu completed Disclosure',
        )
        s = str(notif)
        self.assertIn('fac@usf.edu', s)
        self.assertIn('checkpoint_completed', s)
