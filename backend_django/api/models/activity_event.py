from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from .project import Project, Checkpoint


class ActivityEvent(models.Model):
    """Append-only audit log entry recording a significant action on an activity.

    Events are never updated or deleted in normal operation — the immutable
    chronology is the compliance value. All writes funnel through
    ``api.services.audit_service`` so summary phrasing stays consistent.

    ``created_at`` uses a plain default (not ``auto_now_add``) so the backfill
    data migration can stamp historical events with their real timestamps.
    """

    EVENT_ACTIVITY_CREATED = 'activity_created'
    EVENT_ACTIVITY_UPDATED = 'activity_updated'
    EVENT_CHECKPOINT_COMPLETED = 'checkpoint_completed'
    EVENT_CHECKPOINT_REOPENED = 'checkpoint_reopened'
    EVENT_DECISION_LOGGED = 'decision_logged'
    EVENT_COMMENT_ADDED = 'comment_added'
    EVENT_COMMENT_RESOLVED = 'comment_resolved'
    EVENT_COMMENT_REOPENED = 'comment_reopened'
    EVENT_VERIFICATION_RUN = 'verification_run'
    EVENT_SHARED_AS_EXAMPLE = 'shared_as_example'
    EVENT_UNSHARED_AS_EXAMPLE = 'unshared_as_example'
    EVENT_INVITE_SENT = 'invite_sent'
    EVENT_INVITE_ACCEPTED = 'invite_accepted'
    EVENT_INVITE_DECLINED = 'invite_declined'

    EVENT_CHOICES = [
        (EVENT_ACTIVITY_CREATED, 'Activity created'),
        (EVENT_ACTIVITY_UPDATED, 'Activity updated'),
        (EVENT_CHECKPOINT_COMPLETED, 'Checkpoint completed'),
        (EVENT_CHECKPOINT_REOPENED, 'Checkpoint reopened'),
        (EVENT_DECISION_LOGGED, 'Decision logged'),
        (EVENT_COMMENT_ADDED, 'Comment added'),
        (EVENT_COMMENT_RESOLVED, 'Comment resolved'),
        (EVENT_COMMENT_REOPENED, 'Comment reopened'),
        (EVENT_VERIFICATION_RUN, 'Verification run'),
        (EVENT_SHARED_AS_EXAMPLE, 'Shared as example'),
        (EVENT_UNSHARED_AS_EXAMPLE, 'Unshared as example'),
        (EVENT_INVITE_SENT, 'Invitation sent'),
        (EVENT_INVITE_ACCEPTED, 'Invitation accepted'),
        (EVENT_INVITE_DECLINED, 'Invitation declined'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='events',
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activity_events',
        help_text='User who triggered the event. Null if the actor account was removed.',
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    checkpoint = models.ForeignKey(
        Checkpoint, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events',
        help_text='Checkpoint the event concerns, when applicable.',
    )
    summary = models.CharField(
        max_length=500,
        help_text='Human-readable one-line description shown in the timeline.',
    )
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Extra structured detail (e.g. verification verdict, changed fields).',
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.project.name}: {self.event_type}"
