"""Backfill the activity audit log from pre-existing data.

Events created before the ActivityEvent model existed are reconstructed from
the timestamps already stored on Project, Checkpoint, Decision and
CheckpointComment. Each backfilled row is tagged ``metadata.backfilled = True``
so it can be distinguished from events recorded live. Actor is left null for
checkpoint completions and decisions since the original actor was never
persisted on those rows.
"""
from django.db import migrations


def _name(user) -> str:
    if user is None:
        return 'Someone'
    return user.first_name or user.username


def backfill(apps, schema_editor):
    Project = apps.get_model('api', 'Project')
    CheckpointComment = apps.get_model('api', 'CheckpointComment')
    ActivityEvent = apps.get_model('api', 'ActivityEvent')

    events = []

    for project in Project.objects.select_related('user').all():
        events.append(ActivityEvent(
            project=project,
            actor=project.user,
            event_type='activity_created',
            summary=f"{_name(project.user)} created this activity",
            metadata={'backfilled': True},
            created_at=project.created_at,
        ))

        for cp in project.checkpoints.filter(completed=True).exclude(completed_at=None):
            events.append(ActivityEvent(
                project=project,
                actor=None,
                checkpoint=cp,
                event_type='checkpoint_completed',
                summary=f"'{cp.label}' was completed",
                metadata={'backfilled': True},
                created_at=cp.completed_at,
            ))

        for decision in project.decisions.select_related('checkpoint').all():
            label = decision.checkpoint.label if decision.checkpoint else 'a checkpoint'
            events.append(ActivityEvent(
                project=project,
                actor=None,
                checkpoint=decision.checkpoint,
                event_type='decision_logged',
                summary=f"A decision was logged on '{label}'",
                metadata={'backfilled': True, 'description': decision.description},
                created_at=decision.logged_at,
            ))

    comments = (
        CheckpointComment.objects
        .select_related('checkpoint', 'checkpoint__project', 'user', 'resolved_by')
        .all()
    )
    for comment in comments:
        project = comment.checkpoint.project
        events.append(ActivityEvent(
            project=project,
            actor=comment.user,
            checkpoint=comment.checkpoint,
            event_type='comment_added',
            summary=f"{_name(comment.user)} commented on '{comment.checkpoint.label}'",
            metadata={'backfilled': True},
            created_at=comment.created_at,
        ))
        if comment.resolved and comment.resolved_at:
            events.append(ActivityEvent(
                project=project,
                actor=comment.resolved_by,
                checkpoint=comment.checkpoint,
                event_type='comment_resolved',
                summary=(
                    f"{_name(comment.resolved_by)} resolved a comment thread on "
                    f"'{comment.checkpoint.label}'"
                ),
                metadata={'backfilled': True},
                created_at=comment.resolved_at,
            ))

    ActivityEvent.objects.bulk_create(events, batch_size=500)


def unbackfill(apps, schema_editor):
    """Remove only the rows this migration created."""
    ActivityEvent = apps.get_model('api', 'ActivityEvent')
    ActivityEvent.objects.filter(metadata__backfilled=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_activityevent'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
