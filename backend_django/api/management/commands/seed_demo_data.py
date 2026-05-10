"""Seed demo accounts, demo activities, an accepted-collab scenario, and one shared example.

Idempotent: safe to re-run. Updates existing rows by deterministic key
(email for users, name+owner for projects). Never deletes user-created data.

Demo accounts produced:
    demo.faculty@usf.edu  / TestPass123  (faculty role)
    demo.student@usf.edu  / TestPass123  (student role)

Scenarios produced (each idempotent):
    1. Faculty-owned activity, no collaborator, share_as_example=True
       → appears in Use Cases tab as a public example.
    2. Faculty-owned activity, student collaborator accepted
       → student sees this in their dashboard; both can comment.
    3. Student-owned activity, no advisor yet
       → demonstrates a student initiating compliance work.
    4. Pending invitation from faculty to a never-created email
       → demonstrates the pending state without polluting user accounts.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    AITool,
    Checkpoint,
    Decision,
    Invitation,
    Notification,
    Project,
    UserProfile,
)
from api.services.checkpoint_generator import generate_checkpoints_for_use_case


DEMO_PASSWORD = 'TestPass123'

FACULTY_EMAIL = 'demo.faculty@usf.edu'
STUDENT_EMAIL = 'demo.student@usf.edu'

# Activity 1: faculty solo, shared as example
FACULTY_PUBLIC_ACTIVITY = {
    'name': 'Drafting feedback rubrics with AI for IS 6840',
    'description': (
        'Using ChatGPT to draft a feedback rubric for an undergraduate '
        'Information Systems assignment on database normalization. The rubric '
        'is reviewed by the instructor before use; student submissions never '
        'enter the AI tool.'
    ),
    'ai_use_case': 'teaching',
    'share_as_example': True,
    'risk_context': {
        'involves_student_data': False,
        'affects_decisions': False,
        'external_service': True,
    },
    'tools': ['ChatGPT'],
    'auto_complete_categories': {'Transparency', 'Documentation'},
}

# Activity 2: faculty + student collaborator
FACULTY_SHARED_ACTIVITY = {
    'name': 'Qualitative coding pilot — student perceptions of AI in coursework',
    'description': (
        'Using Claude to assist with thematic coding of de-identified student '
        'interview transcripts about generative AI in their coursework. All '
        'transcripts are de-identified by hand before any text reaches the AI '
        'tool. IRB approved as exempt.'
    ),
    'ai_use_case': 'qualitative',
    'share_as_example': False,
    'risk_context': {
        'involves_student_data': True,
        'human_subjects': True,
        'external_service': True,
    },
    'tools': ['Claude'],
    'auto_complete_categories': {'Transparency', 'Privacy', 'Documentation'},
}

# Activity 3: student-owned
STUDENT_ACTIVITY = {
    'name': 'AI-assisted literature review for CS senior project',
    'description': (
        'Using Perplexity to find peer-reviewed sources on transformer model '
        'interpretability for my senior project. Each citation is verified '
        'against the original paper before inclusion in my proposal.'
    ),
    'ai_use_case': 'literature',
    'share_as_example': False,
    'risk_context': {
        'involves_student_data': False,
        'affects_decisions': False,
        'external_service': True,
    },
    'tools': ['Perplexity'],
    'auto_complete_categories': {'Transparency'},
}


def _ensure_user(email: str, *, first_name: str, last_name: str, role: str) -> User:
    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        },
    )
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.set_password(DEMO_PASSWORD)
    user.save()
    UserProfile.objects.update_or_create(user=user, defaults={'role': role})
    return user


def _ensure_project(*, owner: User, spec: dict, collaborator: User | None = None) -> Project:
    project, _ = Project.objects.get_or_create(
        user=owner, name=spec['name'],
        defaults={
            'description': spec['description'],
            'ai_use_case': spec['ai_use_case'],
            'share_as_example': spec['share_as_example'],
        },
    )
    project.description = spec['description']
    project.ai_use_case = spec['ai_use_case']
    project.share_as_example = spec['share_as_example']
    project.student_collaborator = collaborator if collaborator and collaborator != owner else None
    project.save()

    tools = AITool.objects.filter(name__in=spec['tools'])
    if tools.exists():
        project.ai_tools.set(tools)

    expected = generate_checkpoints_for_use_case(project.ai_use_case, spec.get('risk_context', {}))
    existing_ids = set(project.checkpoints.values_list('checkpoint_id', flat=True))
    for cp_def in expected:
        if cp_def['checkpoint_id'] not in existing_ids:
            Checkpoint.objects.create(project=project, **cp_def)

    auto_categories = spec.get('auto_complete_categories', set())
    for cp in project.checkpoints.filter(category__in=auto_categories, completed=False):
        cp.completed = True
        cp.completed_at = timezone.now()
        cp.save()
        Decision.objects.get_or_create(
            project=project, checkpoint=cp,
            description=f'Auto-attested for demo seed ({cp.label})',
            defaults={'notes': 'Seeded by seed_demo_data command.'},
        )

    return project


def _ensure_pending_invitation(*, project: Project, from_user: User, to_email: str, role: str) -> Invitation:
    inv, _ = Invitation.objects.get_or_create(
        project=project,
        to_email=to_email,
        role=role,
        status=Invitation.STATUS_PENDING,
        defaults={
            'from_user': from_user,
            'note': 'Demo pending invite — accept or decline from the dashboard.',
        },
    )
    return inv


class Command(BaseCommand):
    help = 'Seed demo accounts and demo activities for the TiE U pitch demo.'

    def handle(self, *args, **options) -> None:
        faculty = _ensure_user(
            FACULTY_EMAIL, first_name='Demo', last_name='Faculty', role='faculty',
        )
        student = _ensure_user(
            STUDENT_EMAIL, first_name='Demo', last_name='Student', role='student',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Demo users ready: {faculty.email}, {student.email}'
        ))

        public_activity = _ensure_project(owner=faculty, spec=FACULTY_PUBLIC_ACTIVITY)
        shared_activity = _ensure_project(
            owner=faculty, spec=FACULTY_SHARED_ACTIVITY, collaborator=student,
        )
        student_activity = _ensure_project(owner=student, spec=STUDENT_ACTIVITY)
        self.stdout.write(self.style.SUCCESS(
            f'Activities ready: {public_activity.id}, {shared_activity.id}, {student_activity.id}'
        ))

        invite = _ensure_pending_invitation(
            project=student_activity,
            from_user=student,
            to_email=FACULTY_EMAIL,
            role=Invitation.ROLE_FACULTY_ADVISOR,
        )
        invite.to_user = faculty
        invite.save(update_fields=['to_user'])

        if not Notification.objects.filter(
            recipient=faculty, verb=Notification.VERB_INVITE_RECEIVED, project=student_activity,
        ).exists():
            Notification.objects.create(
                recipient=faculty,
                actor=student,
                verb=Notification.VERB_INVITE_RECEIVED,
                project=student_activity,
                checkpoint=None,
                message=(
                    f'{student.first_name} invited you to join '
                    f'"{student_activity.name}" as faculty advisor.'
                ),
            )

        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write(f'  Faculty: {FACULTY_EMAIL} / {DEMO_PASSWORD}')
        self.stdout.write(f'  Student: {STUDENT_EMAIL} / {DEMO_PASSWORD}')
