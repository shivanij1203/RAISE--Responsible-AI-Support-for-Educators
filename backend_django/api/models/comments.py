from django.db import models
from django.contrib.auth.models import User

from .project import Checkpoint


class CheckpointComment(models.Model):
    """Threaded comments on compliance checkpoints for collaboration."""
    checkpoint = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkpoint_comments')
    text = models.TextField()
    resolved = models.BooleanField(
        default=False,
        help_text='Whether the discussion this comment belongs to has been marked resolved.',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_checkpoint_comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"Comment by {self.user.username} on {self.checkpoint.label[:30]}"
