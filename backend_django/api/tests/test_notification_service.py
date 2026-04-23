"""Tests for api.services.notification_service."""
from django.test import TestCase
from django.contrib.auth.models import User

from api.models import (
    Project, Checkpoint, CheckpointComment, Notification,
)
from api.services import notification_service as svc


class NotificationServiceTest(TestCase):
    def setUp(self) -> None:
        self.student = User.objects.create_user(
            username='stu@usf.edu', email='stu@usf.edu', password='x',
            first_name='Stu',
        )
        self.faculty = User.objects.create_user(
            username='fac@usf.edu', email='fac@usf.edu', password='x',
            first_name='Fac',
        )
        self.collaborator = User.objects.create_user(
            username='col@usf.edu', email='col@usf.edu', password='x',
            first_name='Col',
        )
        self.project = Project.objects.create(
            user=self.student, name='Thesis', ai_use_case='writing',
            faculty_advisor=self.faculty,
            student_collaborator=self.collaborator,
        )
        self.checkpoint = Checkpoint.objects.create(
            project=self.project, checkpoint_id='ai_disclosure',
            label='AI Disclosure', category='Transparency',
            assigned_to='student',
        )

    # checkpoint_completed -----------------------------------------------

    def test_checkpoint_completed_notifies_faculty_advisor(self) -> None:
        svc.notify_checkpoint_completed(self.checkpoint, actor=self.student)
        notifs = Notification.objects.filter(recipient=self.faculty)
        self.assertEqual(notifs.count(), 1)
        n = notifs.first()
        self.assertEqual(n.verb, Notification.VERB_CHECKPOINT_COMPLETED)
        self.assertEqual(n.actor, self.student)
        self.assertEqual(n.checkpoint, self.checkpoint)
        self.assertIn('AI Disclosure', n.message)

    def test_checkpoint_completed_does_not_notify_self(self) -> None:
        svc.notify_checkpoint_completed(self.checkpoint, actor=self.student)
        self.assertFalse(
            Notification.objects.filter(recipient=self.student).exists()
        )

    def test_checkpoint_completed_when_faculty_acts_notifies_student(self) -> None:
        svc.notify_checkpoint_completed(self.checkpoint, actor=self.faculty)
        self.assertTrue(
            Notification.objects.filter(recipient=self.student).exists()
        )
        self.assertFalse(
            Notification.objects.filter(recipient=self.faculty).exists()
        )

    def test_checkpoint_completed_without_advisor_no_notification(self) -> None:
        self.project.faculty_advisor = None
        self.project.student_collaborator = None
        self.project.save()
        svc.notify_checkpoint_completed(self.checkpoint, actor=self.student)
        self.assertEqual(Notification.objects.count(), 0)

    # comment_added ------------------------------------------------------

    def test_comment_added_notifies_everyone_except_actor(self) -> None:
        comment = CheckpointComment.objects.create(
            checkpoint=self.checkpoint, user=self.faculty, text='looks good',
        )
        svc.notify_comment_added(comment)
        recipients = set(
            Notification.objects.values_list('recipient', flat=True)
        )
        self.assertEqual(
            recipients, {self.student.id, self.collaborator.id}
        )

    def test_comment_added_dedupes_recipients(self) -> None:
        solo_project = Project.objects.create(
            user=self.student, name='Solo', ai_use_case='writing',
            faculty_advisor=self.faculty,
        )
        cp = Checkpoint.objects.create(
            project=solo_project, checkpoint_id='ai_disclosure',
            label='L', category='C', assigned_to='student',
        )
        comment = CheckpointComment.objects.create(
            checkpoint=cp, user=self.faculty, text='x',
        )
        svc.notify_comment_added(comment)
        recipients = list(
            Notification.objects.filter(project=solo_project)
            .values_list('recipient', flat=True)
        )
        self.assertEqual(recipients, [self.student.id])

    # verification_run ---------------------------------------------------

    def test_verification_run_notifies_project_owner(self) -> None:
        svc.notify_verification_run(
            self.checkpoint, actor=self.faculty,
            scan_type='pii', verdict='pass',
        )
        notifs = Notification.objects.filter(recipient=self.student)
        self.assertEqual(notifs.count(), 1)
        n = notifs.first()
        self.assertEqual(n.verb, Notification.VERB_VERIFICATION_RUN)
        self.assertIn('pii', n.message.lower())
        self.assertIn('pass', n.message.lower())

    def test_verification_run_does_not_notify_self(self) -> None:
        svc.notify_verification_run(
            self.checkpoint, actor=self.student,
            scan_type='pii', verdict='pass',
        )
        self.assertFalse(
            Notification.objects.filter(recipient=self.student).exists()
        )
