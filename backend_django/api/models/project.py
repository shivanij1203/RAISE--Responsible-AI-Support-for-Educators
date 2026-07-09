from django.db import models
from django.contrib.auth.models import User


PROJECT_CATEGORY_CHOICES = [
    ('research', 'Research'),
    ('teaching', 'Teaching'),
    ('grading', 'Grading'),
    ('admin', 'Admin'),
]


class Project(models.Model):
    """Tracks a research activity and its compliance status."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    faculty_advisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='advised_projects',
        help_text='Faculty advisor who shares access to this activity'
    )
    student_collaborator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collaborated_projects',
        help_text='Student who shares access to this activity'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ai_use_case = models.CharField(max_length=50)
    category = models.CharField(
        max_length=20,
        choices=PROJECT_CATEGORY_CHOICES,
        null=True,
        blank=True,
        default=None,
        help_text=(
            'Activity category used to group activities on the dashboard. '
            'Null means the user has not categorized this activity yet.'
        ),
    )
    status = models.CharField(max_length=20, default='active')
    ai_tools = models.ManyToManyField('api.AITool', blank=True, related_name='projects')
    share_as_example = models.BooleanField(
        default=False,
        help_text='If True, this activity appears anonymized in the institutional Use Cases library. '
                  'Defaults to False so activities are private until the owner explicitly opts in.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"


class Checkpoint(models.Model):
    """Single compliance checkpoint tied to a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='checkpoints')
    checkpoint_id = models.CharField(max_length=50)
    label = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    assigned_to = models.CharField(max_length=20)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    what = models.TextField(blank=True)
    why = models.TextField(blank=True)
    how = models.TextField(blank=True)
    frameworks = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        status = 'done' if self.completed else 'pending'
        return f"{self.project.name} - {self.label} ({status})"


class Decision(models.Model):
    """Logs what was done for a checkpoint (audit trail)."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='decisions')
    checkpoint = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='decisions')
    description = models.CharField(max_length=500)
    notes = models.TextField(blank=True)
    proof_type = models.CharField(max_length=20, blank=True)
    proof_value = models.CharField(max_length=500, blank=True)
    tool_used = models.ForeignKey('api.AITool', on_delete=models.SET_NULL, null=True, blank=True, related_name='decisions')
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.project.name} - {self.description[:50]}"
