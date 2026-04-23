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
