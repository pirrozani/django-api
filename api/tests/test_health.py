from unittest.mock import patch

from django.db import DatabaseError, InterfaceError
from django.test import TestCase, override_settings

HEALTH_URL = '/api/health/'

PROXY_SETTINGS = {
    'DEBUG': False,
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    'SECURE_SSL_REDIRECT': True,
    'SECURE_REDIRECT_EXEMPT': [r'^api/health/$'],
}


class HealthViewTests(TestCase):
    # Anonymous callers get 200 without touching the database
    def test_public_ok_without_db(self):
        with self.assertNumQueries(0):
            response = self.client.get(HEALTH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    # Only the exact value 1 triggers the database check
    def test_other_db_values_skip_database(self):
        with self.assertNumQueries(0):
            response = self.client.get(HEALTH_URL, {'db': 'true'})
        self.assertEqual(response.json(), {'status': 'ok'})

    # ?db=1 runs SELECT 1 and reports the database
    def test_db_check_ok(self):
        with self.assertNumQueries(1):
            response = self.client.get(HEALTH_URL, {'db': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'db': 'ok'})

    # A database failure turns ?db=1 into 503
    def test_db_check_unavailable(self):
        with (
            patch(
                'api.views.health_views.connection.cursor',
                side_effect=DatabaseError('connection refused'),
            ),
            self.assertLogs('api.views.health_views', 'WARNING'),
        ):
            response = self.client.get(HEALTH_URL, {'db': '1'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'error', 'db': 'unavailable'})

    # A closed connection (InterfaceError) is reported the same way, not as 500
    def test_db_check_interface_error(self):
        with (
            patch(
                'api.views.health_views.connection.cursor',
                side_effect=InterfaceError('connection already closed'),
            ),
            self.assertLogs('api.views.health_views', 'WARNING'),
        ):
            response = self.client.get(HEALTH_URL, {'db': '1'})
        self.assertEqual(response.status_code, 503)

    # Bad credentials are ignored, not rejected with 401
    def test_ignores_invalid_token(self):
        response = self.client.get(HEALTH_URL, HTTP_AUTHORIZATION='Token invalid')
        self.assertEqual(response.status_code, 200)


@override_settings(**PROXY_SETTINGS)
class HealthRedirectExemptTests(TestCase):
    # Render's plain-HTTP probe reaches the view instead of a 301
    def test_plain_http_health_not_redirected(self):
        response = self.client.get(HEALTH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    # Every other path still redirects to HTTPS
    def test_plain_http_other_path_redirected(self):
        response = self.client.get('/api/blogs/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://testserver/api/blogs/')
