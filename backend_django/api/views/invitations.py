"""Collaboration invitation endpoints.

Owner of a project sends an invite to an email + role. The invitee accepts
or declines. On accept, the matching FK on the project (faculty_advisor or
student_collaborator) is set, granting access.
"""
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import Invitation, Project
from api.serializers.invitation import InvitationSerializer
from api.services import notification_service
from api.services import audit_service


VALID_ROLES = {Invitation.ROLE_FACULTY_ADVISOR, Invitation.ROLE_STUDENT_COLLABORATOR}


def _user_pending_invites_qs(user: User):
    """All pending invitations addressed to this user (by user FK or email)."""
    return Invitation.objects.filter(
        Q(to_user=user) | Q(to_email__iexact=user.email),
        status=Invitation.STATUS_PENDING,
    ).select_related('project', 'from_user').distinct()


@api_view(['POST'])
def project_invitations_create(request: Request, project_id: int) -> Response:
    """Owner sends an invite to an email + role."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if project.user != request.user:
        return Response(
            {"error": "Only the activity owner can invite collaborators."},
            status=status.HTTP_403_FORBIDDEN,
        )

    to_email = (request.data.get('email') or '').strip().lower()
    role = (request.data.get('role') or '').strip()
    note = (request.data.get('note') or '').strip()[:300]

    if not to_email:
        return Response({"error": "email is required"}, status=status.HTTP_400_BAD_REQUEST)
    if role not in VALID_ROLES:
        return Response(
            {"error": "role must be 'faculty_advisor' or 'student_collaborator'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if to_email == request.user.email.lower():
        return Response({"error": "You cannot invite yourself."}, status=status.HTTP_400_BAD_REQUEST)

    if (
        role == Invitation.ROLE_FACULTY_ADVISOR
        and project.faculty_advisor
        and project.faculty_advisor.email.lower() == to_email
    ):
        return Response(
            {"error": "This person is already the faculty advisor on this activity."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if (
        role == Invitation.ROLE_STUDENT_COLLABORATOR
        and project.student_collaborator
        and project.student_collaborator.email.lower() == to_email
    ):
        return Response(
            {"error": "This person is already a collaborator on this activity."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = Invitation.objects.filter(
        project=project,
        to_email__iexact=to_email,
        role=role,
        status=Invitation.STATUS_PENDING,
    ).first()
    if existing:
        return Response(
            {"error": "A pending invite to this email for this role already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    to_user = User.objects.filter(email__iexact=to_email).first()

    invitation = Invitation.objects.create(
        project=project,
        from_user=request.user,
        to_email=to_email,
        to_user=to_user,
        role=role,
        note=note,
    )

    notification_service.notify_invite_received(invitation)
    audit_service.record_invite_sent(invitation)

    return Response(
        InvitationSerializer(invitation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def project_invitations_list(request: Request, project_id: int) -> Response:
    """Owner lists invitations on their project."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if project.user != request.user:
        return Response(
            {"error": "Only the activity owner can view invitations."},
            status=status.HTTP_403_FORBIDDEN,
        )

    qs = (
        Invitation.objects
        .filter(project=project)
        .select_related('from_user', 'to_user')
    )
    return Response(InvitationSerializer(qs, many=True).data)


@api_view(['GET'])
def my_pending_invitations(request: Request) -> Response:
    """Current user's pending invites (matched by user FK or email)."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)
    qs = _user_pending_invites_qs(request.user)
    return Response(InvitationSerializer(qs, many=True).data)


def _can_respond(invitation: Invitation, user: User) -> bool:
    if invitation.to_user_id == user.id:
        return True
    if invitation.to_email.lower() == (user.email or '').lower():
        return True
    return False


@api_view(['POST'])
def invitation_accept(request: Request, invitation_id: int) -> Response:
    """Invitee accepts → set the corresponding FK on the project."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        invitation = Invitation.objects.select_related('project', 'from_user').get(id=invitation_id)
    except Invitation.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=status.HTTP_404_NOT_FOUND)

    if not _can_respond(invitation, request.user):
        return Response({"error": "This invitation is not for you."}, status=status.HTTP_403_FORBIDDEN)

    if invitation.status != Invitation.STATUS_PENDING:
        return Response(
            {"error": f"Invitation already {invitation.status}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = invitation.project
    if invitation.role == Invitation.ROLE_FACULTY_ADVISOR:
        project.faculty_advisor = request.user
    else:
        project.student_collaborator = request.user
    project.save(update_fields=['faculty_advisor', 'student_collaborator'])

    invitation.status = Invitation.STATUS_ACCEPTED
    invitation.to_user = request.user
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=['status', 'to_user', 'responded_at'])

    notification_service.notify_invite_responded(invitation)
    audit_service.record_invite_responded(invitation)

    return Response(InvitationSerializer(invitation).data)


@api_view(['POST'])
def invitation_decline(request: Request, invitation_id: int) -> Response:
    """Invitee declines → invitation closes, project unchanged."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        invitation = Invitation.objects.select_related('project', 'from_user').get(id=invitation_id)
    except Invitation.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=status.HTTP_404_NOT_FOUND)

    if not _can_respond(invitation, request.user):
        return Response({"error": "This invitation is not for you."}, status=status.HTTP_403_FORBIDDEN)

    if invitation.status != Invitation.STATUS_PENDING:
        return Response(
            {"error": f"Invitation already {invitation.status}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invitation.status = Invitation.STATUS_DECLINED
    invitation.to_user = request.user if not invitation.to_user_id else invitation.to_user
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=['status', 'to_user', 'responded_at'])

    notification_service.notify_invite_responded(invitation)
    audit_service.record_invite_responded(invitation)

    return Response(InvitationSerializer(invitation).data)


@api_view(['DELETE'])
def invitation_cancel(request: Request, invitation_id: int) -> Response:
    """Sender cancels a pending invite they created."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        invitation = Invitation.objects.get(id=invitation_id)
    except Invitation.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=status.HTTP_404_NOT_FOUND)

    if invitation.from_user_id != request.user.id:
        return Response(
            {"error": "Only the sender can cancel this invitation."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if invitation.status != Invitation.STATUS_PENDING:
        return Response(
            {"error": f"Cannot cancel an invitation that is already {invitation.status}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invitation.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
