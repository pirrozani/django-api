from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

from api.tests.test_deployment import load_settings

BLOGS_URL = '/api/blogs/'
FRONTEND = 'http://localhost:5173'


@override_settings(CORS_ALLOWED_ORIGINS=[FRONTEND])
class CorsHeadersTests(TestCase):
    # An allowed origin is echoed back, whatever the response status
    def test_allowed_origin_gets_header(self):
        response = self.client.get(BLOGS_URL, HTTP_ORIGIN=FRONTEND)
        self.assertEqual(response['access-control-allow-origin'], FRONTEND)

    # Any other origin gets no CORS header, so the browser blocks it
    def test_unknown_origin_gets_no_header(self):
        response = self.client.get(BLOGS_URL, HTTP_ORIGIN='https://evil.example')
        self.assertNotIn('access-control-allow-origin', response)

    # Preflight for an authenticated request succeeds and allows the header
    def test_preflight_allows_authorization(self):
        response = self.client.options(
            BLOGS_URL,
            HTTP_ORIGIN=FRONTEND,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['access-control-allow-origin'], FRONTEND)
        allowed = response['access-control-allow-headers'].lower().split(', ')
        self.assertIn('authorization', allowed)

    # Token auth needs no cookies, so credentials are never allowed
    def test_credentials_not_allowed(self):
        response = self.client.get(BLOGS_URL, HTTP_ORIGIN=FRONTEND)
        self.assertNotIn('access-control-allow-credentials', response)


class CorsSettingsTests(SimpleTestCase):
    # CorsMiddleware must run before CommonMiddleware
    def test_middleware_before_common(self):
        middleware = settings.MIDDLEWARE
        self.assertLess(
            middleware.index('corsheaders.middleware.CorsMiddleware'),
            middleware.index('django.middleware.common.CommonMiddleware'),
        )

    # Origins come from the environment as a comma-separated list
    def test_origins_from_env(self):
        values = load_settings(CORS_ALLOWED_ORIGINS='http://localhost:5173,https://app.workers.dev')
        self.assertEqual(
            values['CORS_ALLOWED_ORIGINS'],
            ['http://localhost:5173', 'https://app.workers.dev'],
        )

    # Unset means no cross-origin access, never allow-all
    def test_defaults_closed(self):
        values = load_settings()
        self.assertEqual(values['CORS_ALLOWED_ORIGINS'], [])
        self.assertFalse(values.get('CORS_ALLOW_ALL_ORIGINS', False))
        self.assertFalse(values.get('CORS_ALLOW_CREDENTIALS', False))
