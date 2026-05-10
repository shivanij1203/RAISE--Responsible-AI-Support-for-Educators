from django.db import models
from django.contrib.auth.models import User

from .project import Project


class Invitation(models.Model):
    """Invitation to collaborate on a Project.

    The owner sends; the invitee accepts or declines. On accept, the matching
    foreign key on the Project (faculty_advisor or student_collaborator) is set.
    """

    ROLE_FACULTY_ADVISOR = 'faculty_advisor'
    ROLE_STUDENT_COLLABORATOR = 'student_collaborator'
    ROLE_CHOICES = [
        (ROLE_FACULTY_ADVISOR, 'Faculty advisor'),
        (ROLE_STUDENT_COLLABORATOR, 'Student collaborator'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='invitations',
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_invitations',
    )
    to_email = models.EmailField()
    to_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_invitations',
        help_text='Resolved when the invitee has an account at the time of send, '
                  'or when they sign up later with this email.',
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['to_email', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'to_email', 'role'],
                condition=models.Q(status='pending'),
                name='unique_pending_invitation_per_email_role',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.from_user.username} -> {self.to_email} ({self.role}, {self.status})"
