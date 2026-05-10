"""Tests for the collaboration invitation flow."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Invitation, Notification, Project


class InvitationFlowTest(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username='owner@usf.edu', email='owner@usf.edu', password='x',
            first_name='Owner',
        )
        self.invitee = User.objects.create_user(
            username='invitee@usf.edu', email='invitee@usf.edu', password='x',
            first_name='Invitee',
        )
        self.stranger = User.objects.create_user(
            username='stranger@usf.edu', email='stranger@usf.edu', password='x',
        )
        self.project = Project.objects.create(
            user=self.owner, name='Thesis', ai_use_case='writing',
        )
        self.client = APIClient()

    def _login(self, user: User) -> None:
        self.client.force_login(user)

    def test_owner_can_send_invite_to_registered_user(self) -> None:
        self._login(self.owner)
        resp = self.client.post(
            f'/api/projects/{self.project.id}/invitations',
            {'email': 'invitee@usf.edu', 'role': 'faculty_advisor', 'note': 'Please help'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['status'], 'pending')
        self.assertEqual(resp.data['role'], 'faculty_advisor')

        invite = Invitation.objects.get(project=self.project)
        self.assertEqual(invite.to_user, self.invitee)

        # Notification fired to invitee
        notif = Notification.objects.get(recipient=self.invitee)
        self.assertEqual(notif.verb, Notification.VERB_INVITE_RECEIVED)
        self.assertEqual(notif.actor, self.owner)
        self.assertIn('Thesis', notif.message)

    def test_owner_can_invite_email_not_yet_registered(self) -> None:
        self._login(self.owner)
        resp = self.client.post(
            f'/api/projects/{self.project.id}/invitations',
            {'email': 'noaccount@usf.edu', 'role': 'student_collaborator'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        invite = Invitation.objects.get(project=self.project)
        self.assertIsNone(invite.to_user)
        # No notification fired (recipient has no account)
        self.assertEqual(Notification.objects.count(), 0)

    def test_non_owner_cannot_invite(self) -> None:
        self._login(self.invitee)
        resp = self.client.post(
            f'/api/projects/{self.project.id}/invitations',
            {'email': 'someone@usf.edu', 'role': 'faculty_advisor'},
            format='json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_cannot_invite_self(self) -> None:
        self._login(self.owner)
        resp = self.client.post(
            f'/api/projects/{self.project.id}/invitations',
            {'email': 'owner@usf.edu', 'role': 'faculty_advisor'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_pending_invite_rejected(self) -> None:
        self._login(self.owner)
        body = {'email': 'invitee@usf.edu', 'role': 'faculty_advisor'}
        first = self.client.post(f'/api/projects/{self.project.id}/invitations', body, format='json')
        self.assertEqual(first.status_code, 201)
        second = self.client.post(f'/api/projects/{self.project.id}/invitations', body, format='json')
        self.assertEqual(second.status_code, 400)

    def test_invalid_role_rejected(self) -> None:
        self._login(self.owner)
        resp = self.client.post(
            f'/api/projects/{self.project.id}/invitations',
            {'email': 'invitee@usf.edu', 'role': 'admin'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_pending_list_for_invitee(self) -> None:
        Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.invitee)
        resp = self.client.get('/api/invitations/pending')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['fromName'], 'Owner')

    def test_pending_list_matches_by_email_when_to_user_null(self) -> None:
        """User signs up after invite was sent → matches by email."""
        Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=None, role='faculty_advisor',
        )
        self._login(self.invitee)
        resp = self.client.get('/api/invitations/pending')
        self.assertEqual(len(resp.data), 1)

    def test_accept_sets_advisor_and_notifies_owner(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.invitee)
        resp = self.client.post(f'/api/invitations/{inv.id}/accept')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'accepted')

        self.project.refresh_from_db()
        self.assertEqual(self.project.faculty_advisor, self.invitee)

        notif = Notification.objects.get(recipient=self.owner)
        self.assertEqual(notif.verb, Notification.VERB_INVITE_ACCEPTED)

    def test_accept_sets_student_collaborator(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='student_collaborator',
        )
        self._login(self.invitee)
        resp = self.client.post(f'/api/invitations/{inv.id}/accept')
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.student_collaborator, self.invitee)

    def test_decline_does_not_change_project(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.invitee)
        resp = self.client.post(f'/api/invitations/{inv.id}/decline')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'declined')
        self.project.refresh_from_db()
        self.assertIsNone(self.project.faculty_advisor)
        notif = Notification.objects.get(recipient=self.owner)
        self.assertEqual(notif.verb, Notification.VERB_INVITE_DECLINED)

    def test_stranger_cannot_accept(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.stranger)
        resp = self.client.post(f'/api/invitations/{inv.id}/accept')
        self.assertEqual(resp.status_code, 403)

    def test_cannot_respond_twice(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.invitee)
        self.client.post(f'/api/invitations/{inv.id}/accept')
        resp = self.client.post(f'/api/invitations/{inv.id}/decline')
        self.assertEqual(resp.status_code, 400)

    def test_sender_can_cancel_pending(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.owner)
        resp = self.client.delete(f'/api/invitations/{inv.id}')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Invitation.objects.filter(id=inv.id).exists())

    def test_non_sender_cannot_cancel(self) -> None:
        inv = Invitation.objects.create(
            project=self.project, from_user=self.owner,
            to_email='invitee@usf.edu', to_user=self.invitee, role='faculty_advisor',
        )
        self._login(self.invitee)
        resp = self.client.delete(f'/api/invitations/{inv.id}')
        self.assertEqual(resp.status_code, 403)
