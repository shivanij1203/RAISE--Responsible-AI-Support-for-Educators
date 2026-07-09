from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, Project


class ProjectCategoryTest(TestCase):
    """Tests for the new Project.category field and its API wiring."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='cat@usf.edu',
            email='cat@usf.edu',
            password='testpass123',
            first_name='Cat User',
        )
        UserProfile.objects.create(user=self.user, role='pi')
        self.client.login(username='cat@usf.edu', password='testpass123')

    def test_existing_activities_default_to_null_category(self) -> None:
        """Activities created without category stay uncategorized."""
        project = Project.objects.create(
            user=self.user,
            name='Untagged',
            ai_use_case='writing',
        )
        self.assertIsNone(project.category)

    def test_create_with_valid_category(self) -> None:
        response = self.client.post(
            '/api/projects',
            data={
                'name': 'Teaching Project',
                'ai_use_case': 'writing',
                'category': 'teaching',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['category'], 'teaching')

    def test_create_without_category_keeps_it_null(self) -> None:
        response = self.client.post(
            '/api/projects',
            data={
                'name': 'No Category',
                'ai_use_case': 'writing',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()['category'])

    def test_create_with_invalid_category_returns_400(self) -> None:
        response = self.client.post(
            '/api/projects',
            data={
                'name': 'Bad',
                'ai_use_case': 'writing',
                'category': 'made-up-category',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid category', response.json()['error'])

    def test_update_sets_category_on_existing_activity(self) -> None:
        project = Project.objects.create(
            user=self.user,
            name='Untagged',
            ai_use_case='writing',
        )
        response = self.client.put(
            f'/api/projects/{project.id}',
            data={'category': 'research'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['category'], 'research')
        project.refresh_from_db()
        self.assertEqual(project.category, 'research')

    def test_update_clears_category_when_empty_string(self) -> None:
        project = Project.objects.create(
            user=self.user,
            name='Tagged',
            ai_use_case='writing',
            category='teaching',
        )
        response = self.client.put(
            f'/api/projects/{project.id}',
            data={'category': ''},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['category'])

    def test_update_with_invalid_category_returns_400(self) -> None:
        project = Project.objects.create(
            user=self.user,
            name='Untagged',
            ai_use_case='writing',
        )
        response = self.client.put(
            f'/api/projects/{project.id}',
            data={'category': 'nope'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_category_appears_in_serialized_project(self) -> None:
        Project.objects.create(
            user=self.user,
            name='Grading One',
            ai_use_case='grading',
            category='grading',
        )
        response = self.client.get('/api/projects')
        self.assertEqual(response.status_code, 200)
        categories = [p['category'] for p in response.json()]
        self.assertIn('grading', categories)
