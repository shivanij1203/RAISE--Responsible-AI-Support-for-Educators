"""Creates in-app Notification rows when shared-activity events happen.

A single place to change when Phase D adds email delivery: fan-out logic
stays here, transport becomes a separate concern.
"""
from typing import Iterable

from django.contrib.auth.models import User

from api.models import Notification, Checkpoint, CheckpointComment, Project


def _project_members(project: Project) -> set[User]:
    """All users with access to a project (owner + advisor + collaborator)."""
    members: set[User] = {project.user}
    if project.faculty_advisor_id:
        members.add(project.faculty_advisor)
    if project.student_collaborator_id:
        members.add(project.student_collaborator)
    return members


def _create_for_recipients(
    recipients: Iterable[User],
    *,
    actor: User,
    verb: str,
    project: Project,
    checkpoint: Checkpoint | None,
    message: str,
) -> list[Notification]:
    """Create notifications for each recipient, skipping the actor."""
    created: list[Notification] = []
    for recipient in recipients:
        if recipient == actor:
            continue
        created.append(
            Notification.objects.create(
                recipient=recipient,
                actor=actor,
                verb=verb,
                project=project,
                checkpoint=checkpoint,
                message=message,
            )
        )
    return created


def _display_name(user: User) -> str:
    return user.first_name or user.username


def notify_checkpoint_completed(
    checkpoint: Checkpoint, *, actor: User,
) -> list[Notification]:
    """Student completes a checkpoint → notify faculty advisor (and vice versa)."""
    project = checkpoint.project
    recipients = _project_members(project) - {actor}
    message = f"{_display_name(actor)} completed '{checkpoint.label}'"
    return _create_for_recipients(
        recipients,
        actor=actor,
        verb=Notification.VERB_CHECKPOINT_COMPLETED,
        project=project,
        checkpoint=checkpoint,
        message=message,
    )


def notify_comment_added(comment: CheckpointComment) -> list[Notification]:
    """New comment on a checkpoint → notify other project members."""
    project = comment.checkpoint.project
    actor = comment.user
    recipients = _project_members(project) - {actor}
    preview = comment.text[:80] + ('…' if len(comment.text) > 80 else '')
    message = f"{_display_name(actor)} commented on '{comment.checkpoint.label}': {preview}"
    return _create_for_recipients(
        recipients,
        actor=actor,
        verb=Notification.VERB_COMMENT_ADDED,
        project=project,
        checkpoint=comment.checkpoint,
        message=message,
    )


def notify_verification_run(
    checkpoint: Checkpoint,
    *,
    actor: User,
    scan_type: str,
    verdict: str,
) -> list[Notification]:
    """Faculty ran a PII/FERPA/classification/bias scan → notify project owner."""
    project = checkpoint.project
    recipients = _project_members(project) - {actor}
    message = (
        f"{_display_name(actor)} ran {scan_type} scan on "
        f"'{checkpoint.label}' — verdict: {verdict}"
    )
    return _create_for_recipients(
        recipients,
        actor=actor,
        verb=Notification.VERB_VERIFICATION_RUN,
        project=project,
        checkpoint=checkpoint,
        message=message,
    )


def notify_invite_received(invitation) -> Notification | None:
    """Send a notification to the invitee when an invite is created.

    Only fires when the invitee already has an account (to_user is set).
    """
    if not invitation.to_user_id:
        return None
    role_label = (
        'faculty advisor' if invitation.role == 'faculty_advisor' else 'student collaborator'
    )
    message = (
        f"{_display_name(invitation.from_user)} invited you to join "
        f"'{invitation.project.name}' as {role_label}."
    )
    return Notification.objects.create(
        recipient=invitation.to_user,
        actor=invitation.from_user,
        verb=Notification.VERB_INVITE_RECEIVED,
        project=invitation.project,
        checkpoint=None,
        message=message,
    )


def notify_invite_responded(invitation) -> Notification:
    """Send a notification back to the original sender when invitee accepts/declines."""
    if invitation.status == 'accepted':
        verb = Notification.VERB_INVITE_ACCEPTED
        verb_text = 'accepted'
    else:
        verb = Notification.VERB_INVITE_DECLINED
        verb_text = 'declined'
    actor_name = invitation.to_user.first_name or invitation.to_email if invitation.to_user else invitation.to_email
    message = f"{actor_name} {verb_text} your invite to '{invitation.project.name}'."
    return Notification.objects.create(
        recipient=invitation.from_user,
        actor=invitation.to_user,
        verb=verb,
        project=invitation.project,
        checkpoint=None,
        message=message,
    )
