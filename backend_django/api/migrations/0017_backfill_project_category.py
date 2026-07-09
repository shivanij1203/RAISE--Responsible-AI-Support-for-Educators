from django.db import migrations


# Inlined snapshot of the classifier so this historical migration stays
# self-contained even if api.services.project_categorizer is refactored
# or moved in the future. Keep in sync with the runtime version when
# behavior changes.
_KEYWORDS_BY_CATEGORY: dict[str, list[str]] = {
    'grading': ['grading', 'grade', 'grader', 'rubric', 'assess', 'score'],
    'teaching': [
        'rubric drafting', 'course materials', 'lesson', 'syllabus',
        'teaching', 'feedback rubric',
    ],
    'admin': ['admissions', 'screening', 'applications', 'scheduling', 'hiring'],
    'research': [
        'qualitative coding', 'interview', 'research', 'irb',
        'transcripts', 'study',
    ],
}
_PRIORITY = ['grading', 'teaching', 'admin', 'research']
_DEFAULT = 'research'


def _classify(text: str) -> str:
    if not text:
        return _DEFAULT
    lowered = text.lower()
    hits: list[tuple[int, int, str]] = []
    for category, kws in _KEYWORDS_BY_CATEGORY.items():
        pri = _PRIORITY.index(category)
        for kw in kws:
            if kw.lower() in lowered:
                hits.append((-len(kw), pri, category))
    if not hits:
        return _DEFAULT
    hits.sort()
    return hits[0][2]


def backfill_categories(apps, schema_editor):
    """Auto-categorize every Project where category IS NULL.

    Runs on local + every environment this migration is applied to,
    including production via the release pipeline.
    """
    Project = apps.get_model('api', 'Project')
    updated = 0
    for project in Project.objects.filter(category__isnull=True).iterator():
        text = ' '.join(filter(None, [
            project.name or '',
            project.description or '',
            project.ai_use_case or '',
        ]))
        project.category = _classify(text)
        project.save(update_fields=['category'])
        updated += 1
    if updated:
        print(f"  Backfilled category on {updated} activity(ies).")


def reverse_backfill(apps, schema_editor):
    """No-op reverse.

    We can't tell which rows this migration touched (no marker column),
    and clearing every row would destroy user-set categories. Leaving
    the data in place on rollback is the safer choice.
    """
    return


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_add_project_category'),
    ]

    operations = [
        migrations.RunPython(backfill_categories, reverse_backfill),
    ]
