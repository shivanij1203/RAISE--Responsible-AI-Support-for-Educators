"""Records ActivityEvent rows — the append-only audit log for an activity.

All writes funnel through ``record_event`` so summary phrasing stays
consistent. Mirrors the structure of ``notification_service``: a thin write
helper plus one function per event type that the views call.
"""
from __future__ import annotations

from django.contrib.auth.models import User

from api.models import ActivityEvent, Checkpoint, CheckpointComment, Decision, Project


def _display_name(user: User | None) -> str:
    """Best-effort human name for an actor; falls back when the account is gone."""
    if user is None:
        return 'Someone'
    return user.first_name or user.username


def record_event(
    project: Project,
    *,
    actor: User | None,
    event_type: str,
    summary: str,
    checkpoint: Checkpoint | None = None,
    metadata: dict | None = None,
) -> ActivityEvent:
    """Append a single immutable event to an activity's audit log."""
    return ActivityEvent.objects.create(
        project=project,
        actor=actor,
        event_type=event_type,
        checkpoint=checkpoint,
        summary=summary,
        metadata=metadata or {},
    )


def record_activity_created(project: Project, *, actor: User | None) -> ActivityEvent:
    return record_event(
        project,
        actor=actor,
        event_type=ActivityEvent.EVENT_ACTIVITY_CREATED,
        summary=f"{_display_name(actor)} created this activity",
    )


def record_activity_updated(
    project: Project, *, actor: User | None, changed_fields: list[str],
) -> ActivityEvent:
    fields_text = ', '.join(changed_fields) if changed_fields else 'details'
    return record_event(
        project,
        actor=actor,
        event_type=ActivityEvent.EVENT_ACTIVITY_UPDATED,
        summary=f"{_display_name(actor)} updated the activity ({fields_text})",
        metadata={'changedFields': changed_fields},
    )


def record_share_toggled(
    project: Project, *, actor: User | None, shared: bool,
) -> ActivityEvent:
    if shared:
        return record_event(
            project,
            actor=actor,
            event_type=ActivityEvent.EVENT_SHARED_AS_EXAMPLE,
            summary=f"{_display_name(actor)} shared this activity to the Use Cases library",
        )
    return record_event(
        project,
        actor=actor,
        event_type=ActivityEvent.EVENT_UNSHARED_AS_EXAMPLE,
        summary=f"{_display_name(actor)} removed this activity from the Use Cases library",
    )


def record_checkpoint_completed(
    checkpoint: Checkpoint, *, actor: User | None,
) -> ActivityEvent:
    return record_event(
        checkpoint.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_CHECKPOINT_COMPLETED,
        summary=f"{_display_name(actor)} completed '{checkpoint.label}'",
        checkpoint=checkpoint,
    )


def record_checkpoint_reopened(
    checkpoint: Checkpoint, *, actor: User | None,
) -> ActivityEvent:
    return record_event(
        checkpoint.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_CHECKPOINT_REOPENED,
        summary=f"{_display_name(actor)} reopened '{checkpoint.label}'",
        checkpoint=checkpoint,
    )


def record_decision_logged(decision: Decision, *, actor: User | None) -> ActivityEvent:
    return record_event(
        decision.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_DECISION_LOGGED,
        summary=f"{_display_name(actor)} logged a decision on '{decision.checkpoint.label}'",
        checkpoint=decision.checkpoint,
        metadata={'description': decision.description},
    )


def record_comment_added(comment: CheckpointComment) -> ActivityEvent:
    actor = comment.user
    return record_event(
        comment.checkpoint.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_COMMENT_ADDED,
        summary=f"{_display_name(actor)} commented on '{comment.checkpoint.label}'",
        checkpoint=comment.checkpoint,
    )


def record_comment_resolved(
    comment: CheckpointComment, *, actor: User | None, resolved: bool,
) -> ActivityEvent:
    label = comment.checkpoint.label
    if resolved:
        return record_event(
            comment.checkpoint.project,
            actor=actor,
            event_type=ActivityEvent.EVENT_COMMENT_RESOLVED,
            summary=f"{_display_name(actor)} resolved a comment thread on '{label}'",
            checkpoint=comment.checkpoint,
        )
    return record_event(
        comment.checkpoint.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_COMMENT_REOPENED,
        summary=f"{_display_name(actor)} reopened a comment thread on '{label}'",
        checkpoint=comment.checkpoint,
    )


def record_verification_run(
    checkpoint: Checkpoint, *, actor: User | None, scan_type: str, verdict: str,
) -> ActivityEvent:
    return record_event(
        checkpoint.project,
        actor=actor,
        event_type=ActivityEvent.EVENT_VERIFICATION_RUN,
        summary=(
            f"{_display_name(actor)} ran a {scan_type} scan on "
            f"'{checkpoint.label}' — verdict: {verdict}"
        ),
        checkpoint=checkpoint,
        metadata={'scanType': scan_type, 'verdict': verdict},
    )


def record_invite_sent(invitation) -> ActivityEvent:
    role_label = (
        'faculty advisor'
        if invitation.role == 'faculty_advisor'
        else 'student collaborator'
    )
    return record_event(
        invitation.project,
        actor=invitation.from_user,
        event_type=ActivityEvent.EVENT_INVITE_SENT,
        summary=(
            f"{_display_name(invitation.from_user)} invited {invitation.to_email} "
            f"as {role_label}"
        ),
        metadata={'toEmail': invitation.to_email, 'role': invitation.role},
    )


def record_invite_responded(invitation) -> ActivityEvent:
    accepted = invitation.status == 'accepted'
    actor = invitation.to_user
    actor_name = _display_name(actor) if actor else invitation.to_email
    verb = 'accepted' if accepted else 'declined'
    return record_event(
        invitation.project,
        actor=actor,
        event_type=(
            ActivityEvent.EVENT_INVITE_ACCEPTED
            if accepted
            else ActivityEvent.EVENT_INVITE_DECLINED
        ),
        summary=f"{actor_name} {verb} the collaboration invite",
        metadata={'toEmail': invitation.to_email, 'role': invitation.role},
    )
