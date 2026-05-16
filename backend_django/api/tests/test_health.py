"""Tests for the health check endpoint."""
from django.test import TestCase
from rest_framework.test import APIClient


class HealthCheckTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_health_returns_200_without_auth(self) -> None:
        """The health endpoint must be reachable without authentication."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)

    def test_health_reports_ok_status(self) -> None:
        """A healthy app reports status ok and a reachable database."""
        response = self.client.get('/api/health')
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['database'], 'ok')
