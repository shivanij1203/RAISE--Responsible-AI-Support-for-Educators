from django.db import models
from django.contrib.auth.models import User

from .project import Project, Checkpoint


class Notification(models.Model):
    """In-app notification delivered to a user when another user acts on shared work."""

    VERB_CHECKPOINT_COMPLETED = 'checkpoint_completed'
    VERB_COMMENT_ADDED = 'comment_added'
    VERB_VERIFICATION_RUN = 'verification_run'
    VERB_INVITE_RECEIVED = 'invite_received'
    VERB_INVITE_ACCEPTED = 'invite_accepted'
    VERB_INVITE_DECLINED = 'invite_declined'
    VERB_CHOICES = [
        (VERB_CHECKPOINT_COMPLETED, 'Checkpoint completed'),
        (VERB_COMMENT_ADDED, 'Comment added'),
        (VERB_VERIFICATION_RUN, 'Verification run'),
        (VERB_INVITE_RECEIVED, 'Collaboration invite received'),
        (VERB_INVITE_ACCEPTED, 'Collaboration invite accepted'),
        (VERB_INVITE_DECLINED, 'Collaboration invite declined'),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications',
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='triggered_notifications',
    )
    verb = models.CharField(max_length=40, choices=VERB_CHOICES)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='notifications',
    )
    checkpoint = models.ForeignKey(
        Checkpoint, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications',
    )
    message = models.CharField(max_length=500)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'read']),
        ]

    def __str__(self) -> str:
        return f"{self.recipient.username} <- {self.verb}"
