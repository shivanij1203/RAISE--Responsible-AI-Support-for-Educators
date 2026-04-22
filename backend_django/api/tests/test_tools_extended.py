"""Extended tests for /api/tools endpoints: update, detail, filtering."""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from api.models import UserProfile, AITool, Project


class AIToolUpdateTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.faculty = User.objects.create_user(
            username='fac@usf.edu', email='fac@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.faculty, role='faculty')
        self.student = User.objects.create_user(
            username='stu@usf.edu', email='stu@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.student, role='student')
        self.tool = AITool.objects.create(
            name='Old Name', category='writing', status='under_review',
            added_by=self.faculty,
        )

    def test_faculty_can_update(self) -> None:
        self.client.login(username='fac@usf.edu', password='testpass123')
        response = self.client.put(
            f'/api/tools/{self.tool.id}',
            data=json.dumps({'name': 'New Name', 'status': 'approved'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.tool.refresh_from_db()
        self.assertEqual(self.tool.name, 'New Name')
        self.assertEqual(self.tool.status, 'approved')

    def test_student_cannot_update(self) -> None:
        self.client.login(username='stu@usf.edu', password='testpass123')
        response = self.client.put(
            f'/api/tools/{self.tool.id}',
            data=json.dumps({'name': 'Hacked'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_unknown_tool_404(self) -> None:
        self.client.login(username='fac@usf.edu', password='testpass123')
        response = self.client.put(
            '/api/tools/9999',
            data=json.dumps({'name': 'X'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class AIToolDetailTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='d@usf.edu', email='d@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.user, role='faculty')
        self.tool = AITool.objects.create(
            name='Detail Tool', category='chatbot', status='approved',
            added_by=self.user,
        )
        self.project = Project.objects.create(
            user=self.user, name='Uses Tool', ai_use_case='writing',
        )
        self.project.ai_tools.add(self.tool)
        self.client.login(username='d@usf.edu', password='testpass123')

    def test_detail_includes_activity_history(self) -> None:
        response = self.client.get(f'/api/tools/{self.tool.id}/detail')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['name'], 'Detail Tool')
        self.assertIn('activityHistory', body)
        self.assertEqual(len(body['activityHistory']), 1)
        self.assertEqual(body['activityHistory'][0]['name'], 'Uses Tool')

    def test_detail_404(self) -> None:
        response = self.client.get('/api/tools/9999/detail')
        self.assertEqual(response.status_code, 404)


class AIToolFilterTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='f@usf.edu', email='f@usf.edu', password='testpass123',
        )
        UserProfile.objects.create(user=self.user, role='faculty')
        AITool.objects.create(name='A', tool_type='ai', category='chatbot',
                              status='approved', added_by=self.user)
        AITool.objects.create(name='B', tool_type='general', category='writing',
                              status='under_review', added_by=self.user)
        AITool.objects.create(name='Notes', tool_type='ai', category='writing',
                              status='approved', added_by=self.user)
        self.client.login(username='f@usf.edu', password='testpass123')

    def test_filter_by_tool_type(self) -> None:
        response = self.client.get('/api/tools?tool_type=ai')
        self.assertEqual(len(response.json()), 2)

    def test_filter_by_category(self) -> None:
        response = self.client.get('/api/tools?category=writing')
        self.assertEqual(len(response.json()), 2)

    def test_filter_by_status(self) -> None:
        response = self.client.get('/api/tools?status=approved')
        self.assertEqual(len(response.json()), 2)

    def test_search_by_name(self) -> None:
        response = self.client.get('/api/tools?search=note')
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['name'], 'Notes')
