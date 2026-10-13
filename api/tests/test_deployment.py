import os
import re
import runpy
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

SETTINGS_FILE = Path(settings.BASE_DIR) / 'django_api' / 'settings.py'

# Dummy, non-secret key long enough to pass the DEBUG=False check (#17)
TEST_SECRET_KEY = 'dummy-test-key-not-secret-0123456789abcdefghijklmnopqrstuvwxyz'

SECURITY_SETTINGS = [
    'SECURE_PROXY_SSL_HEADER',
    'SECURE_SSL_REDIRECT',
    'SECURE_REDIRECT_EXEMPT',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_HSTS_SECONDS',
    'SECURE_CONTENT_TYPE_NOSNIFF',
]

PRODUCTION_ENV = {
    'DEBUG': 'False',
    'SECRET_KEY': TEST_SECRET_KEY,
    'ALLOWED_HOSTS': 'example.onrender.com',
    'CSRF_TRUSTED_ORIGINS': 'https://example.onrender.com',
}

# Warnings documented as accepted in docs/07-deployment.md
ACCEPTED_DEPLOY_WARNINGS = {'security.W005', 'security.W021'}


# Evaluate settings.py with only the given environment, ignoring the local .env
def load_settings(**environ):
    environ = {'SECRET_KEY': TEST_SECRET_KEY, **environ}
    with patch.dict(os.environ, environ, clear=True):
        with patch('environ.Env.read_env'):
            return runpy.run_path(str(SETTINGS_FILE))


class StaticFilesSettingsTests(SimpleTestCase):
    # WhiteNoise serves static files right after SecurityMiddleware (#7)
    def test_whitenoise_follows_security_middleware(self):
        middleware = settings.MIDDLEWARE
        index = middleware.index('django.middleware.security.SecurityMiddleware')
        self.assertEqual(
            middleware[index + 1], 'whitenoise.middleware.WhiteNoiseMiddleware'
        )

    # collectstatic has a target and writes compressed, hashed files
    def test_static_root_and_storage(self):
        self.assertEqual(
            Path(settings.STATIC_ROOT), Path(settings.BASE_DIR) / 'staticfiles'
        )
        self.assertEqual(
            settings.STORAGES['staticfiles']['BACKEND'],
            'whitenoise.storage.CompressedManifestStaticFilesStorage',
        )


class SecuritySettingsTests(SimpleTestCase):
    # With DEBUG=False the app trusts Render's proxy and enforces HTTPS
    def test_production_security_settings(self):
        config = load_settings(**PRODUCTION_ENV)
        self.assertEqual(
            config['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https')
        )
        self.assertTrue(config['SECURE_SSL_REDIRECT'])
        self.assertEqual(config['SECURE_REDIRECT_EXEMPT'], [r'^api/health/$'])
        self.assertTrue(config['SESSION_COOKIE_SECURE'])
        self.assertTrue(config['CSRF_COOKIE_SECURE'])
        self.assertEqual(config['SECURE_HSTS_SECONDS'], 3600)
        self.assertTrue(config['SECURE_CONTENT_TYPE_NOSNIFF'])
        self.assertEqual(
            config['CSRF_TRUSTED_ORIGINS'], ['https://example.onrender.com']
        )

    # SECURE_HSTS_SECONDS can be raised from the environment
    def test_hsts_seconds_from_env(self):
        config = load_settings(**PRODUCTION_ENV, SECURE_HSTS_SECONDS='31536000')
        self.assertEqual(config['SECURE_HSTS_SECONDS'], 31536000)

    # Tests/CI running with DEBUG=False can turn the HTTPS redirect off
    def test_ssl_redirect_from_env(self):
        config = load_settings(**PRODUCTION_ENV, SECURE_SSL_REDIRECT='False')
        self.assertFalse(config['SECURE_SSL_REDIRECT'])
        self.assertTrue(config['SESSION_COOKIE_SECURE'])

    # Local development (DEBUG=True) keeps plain HTTP working
    def test_debug_skips_https_settings(self):
        config = load_settings(DEBUG='True')
        for name in SECURITY_SETTINGS:
            with self.subTest(setting=name):
                self.assertNotIn(name, config)
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], [])

    # check --deploy only reports the documented, accepted warnings
    def test_deploy_checks_pass_with_production_env(self):
        config = load_settings(**PRODUCTION_ENV)
        overrides = {
            name: config[name]
            for name in [*SECURITY_SETTINGS, 'SECRET_KEY', 'ALLOWED_HOSTS']
        }
        with override_settings(DEBUG=False, **overrides):
            messages = checks.run_checks(include_deployment_checks=True)
        ids = {m.id for m in messages if m.is_serious(checks.WARNING)}
        self.assertLessEqual(ids, ACCEPTED_DEPLOY_WARNINGS)


class SecretKeyTests(SimpleTestCase):
    # Run manage.py check in a fresh process; explicit env vars win over the local file
    def run_check(self, **environ):
        env = {**os.environ, **PRODUCTION_ENV, **environ}
        return subprocess.run(
            [sys.executable, 'manage.py', 'check'],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    # The example placeholder or a short random key stops startup without DEBUG (#17)
    def test_weak_key_fails_without_debug(self):
        for key in ('change-me', 'k3Y-' * 12):
            with self.subTest(length=len(key)):
                result = self.run_check(SECRET_KEY=key)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ImproperlyConfigured', result.stderr)

    # A 50+ character key starts normally
    def test_strong_key_passes_without_debug(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    # Local development keeps working with the placeholder
    def test_placeholder_allowed_with_debug(self):
        config = load_settings(DEBUG='True', SECRET_KEY='change-me')
        self.assertEqual(config['SECRET_KEY'], 'change-me')

    # Loading the settings raises the same error the subprocess reports
    def test_weak_key_raises_in_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            load_settings(**{**PRODUCTION_ENV, 'SECRET_KEY': 'change-me'})


class EnvListSettingsTests(SimpleTestCase):
    LIST_SETTINGS = ('ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS', 'CORS_ALLOWED_ORIGINS')

    # Spaces around the commas are stripped, so every entry still matches (#33)
    def test_spaced_values_are_stripped(self):
        values = {
            'ALLOWED_HOSTS': (
                'localhost, api.example.com',
                ['localhost', 'api.example.com'],
            ),
            'CSRF_TRUSTED_ORIGINS': (
                'https://a.example , https://b.example',
                ['https://a.example', 'https://b.example'],
            ),
            'CORS_ALLOWED_ORIGINS': (
                'https://x.example, http://localhost:5173, ',
                ['https://x.example', 'http://localhost:5173'],
            ),
        }
        config = load_settings(**{name: raw for name, (raw, _) in values.items()})
        for name, (_, expected) in values.items():
            with self.subTest(setting=name):
                self.assertEqual(config[name], expected)

    # Unset variables give an empty list, never allow-all or default hosts
    def test_unset_values_default_to_empty(self):
        config = load_settings(DEBUG='True')
        for name in self.LIST_SETTINGS:
            with self.subTest(setting=name):
                self.assertEqual(config[name], [])


class StaticFilesServingTests(TestCase):
    # With DEBUG=False, WhiteNoise serves the collected admin CSS (#7)
    def test_admin_css_served_without_debug(self):
        # Cleanups run last-in-first-out, so the CSS response registered below
        # closes before the temp dir is deleted (Windows can't delete open files)
        static_root = self.enterContext(tempfile.TemporaryDirectory())
        with override_settings(STATIC_ROOT=static_root):
            call_command('collectstatic', interactive=False, stdout=StringIO())
            response = self.client.get('/admin/login/', secure=True)
            self.assertEqual(response.status_code, 200)
            # The template links the hashed name from the manifest
            match = re.search(
                r'href="(/static/admin/css/base\.[0-9a-f]{12}\.css)"',
                response.content.decode(),
            )
            self.assertIsNotNone(match)
            css = self.client.get(match.group(1), secure=True)
            self.addCleanup(css.close)
            self.assertEqual(css.status_code, 200)
            self.assertTrue(css['Content-Type'].startswith('text/css'))


PROXY_SETTINGS = {
    'DEBUG': False,
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    'SECURE_SSL_REDIRECT': True,
    'SECURE_HSTS_SECONDS': 3600,
}


@override_settings(**PROXY_SETTINGS)
class ProxyHttpsTests(SimpleTestCase):
    # Plain HTTP that didn't come through Render's HTTPS proxy is redirected
    def test_plain_http_redirects_to_https(self):
        response = self.client.get('/api/schema/swagger-ui/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response['Location'], 'https://testserver/api/schema/swagger-ui/'
        )

    # A request the proxy marks as HTTPS is served, with HSTS
    def test_proxied_https_is_served_with_hsts(self):
        response = self.client.get(
            '/api/schema/swagger-ui/', HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Strict-Transport-Security'], 'max-age=3600')
