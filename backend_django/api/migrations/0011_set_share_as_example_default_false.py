from django.db import migrations, models


def make_existing_activities_private(apps, schema_editor):
    """Existing activities were created before the Use Cases tab existed and
    never had a chance to consent. Reset them all to private so nothing is
    exposed retroactively. Owners can opt in per activity afterwards.
    """
    Project = apps.get_model('api', 'Project')
    Project.objects.update(share_as_example=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_project_share_as_example'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='share_as_example',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'If True, this activity appears anonymized in the institutional '
                    'Use Cases library. Defaults to False so activities are private '
                    'until the owner explicitly opts in.'
                ),
            ),
        ),
        migrations.RunPython(make_existing_activities_private, noop_reverse),
    ]
