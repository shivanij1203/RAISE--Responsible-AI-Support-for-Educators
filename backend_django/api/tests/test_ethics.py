"""Tests for /api/ethics/* endpoints."""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User


class EthicsEndpointsTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='e@usf.edu', email='e@usf.edu', password='testpass123',
        )
        self.client.login(username='e@usf.edu', password='testpass123')

    def test_start_returns_node(self) -> None:
        response = self.client.get('/api/ethics/start')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['key'], 'start')

    def test_unknown_node_returns_404(self) -> None:
        response = self.client.get('/api/ethics/node/this_does_not_exist')
        self.assertEqual(response.status_code, 404)

    def test_scenarios_endpoint(self) -> None:
        response = self.client.get('/api/ethics/scenarios')
        self.assertEqual(response.status_code, 200)

    def test_evaluate_with_empty_answers(self) -> None:
        response = self.client.post(
            '/api/ethics/evaluate',
            data=json.dumps({'answers': {}}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
