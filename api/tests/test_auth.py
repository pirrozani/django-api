import os
import runpy
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User as Account
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.settings import api_settings
from rest_framework.test import APIClient, APITestCase

from api.models import Blog, User
from api.tests.test_deployment import TEST_SECRET_KEY
from api.views.auth_views import LoginRateThrottle

DEMO = {'DEMO_USERNAME': 'demo', 'DEMO_PASSWORD': 'demo-pass'}

SETTINGS_FILE = Path(settings.BASE_DIR) / 'django_api' / 'settings.py'


@override_settings(**DEMO)
class AuthTests(APITestCase):
    # Create the demo account and one author with a blog; reset the login throttle
    def setUp(self):
        cache.clear()
        call_command('create_demo_user', stdout=StringIO())
        self.author = User.objects.create(
            first_name='Ann', last_name='Lee', username='alee', email='ann@example.com',
            password='pbkdf2_sha256$1$salt$hash',
        )
        Blog.objects.create(user=self.author, title='Hello', content='World')

    # Log in with form data, as curl -d does
    def login(self, username='demo', password='demo-pass', **extra):
        return self.client.post(
            reverse('auth-token'), {'username': username, 'password': password}, **extra
        )

    # POST /api/auth/token/ with the demo credentials returns the account's token
    def test_login_returns_token(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = Token.objects.get(user__username='demo')
        self.assertEqual(response.json(), {'token': token.key})

    # Wrong credentials are a 400 field error, not a token
    def test_login_with_wrong_password_returns_400(self):
        response = self.login(password='wrong')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.json())

    # A stale token in the header doesn't block logging in again
    def test_login_ignores_invalid_token_header(self):
        response = self.login(HTTP_AUTHORIZATION='Token invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Reads are public: every GET endpoint answers 200 without a token
    def test_reads_are_public(self):
        urls = [
            reverse('blog-list'),
            reverse('user-list'),
            reverse('user-detail', args=[self.author.id]),
            reverse('user-blogs', args=[self.author.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    # Writes without a token are 401 with a Token challenge, never Basic
    def test_anonymous_write_returns_401_with_token_challenge(self):
        data = {'title': 'New', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'Token')
        self.assertFalse(Blog.objects.filter(title='New').exists())

    # A token from the login endpoint authorizes writes, as the account's own author (#39)
    def test_token_authorizes_writes(self):
        token = self.login().json()['token']
        data = {'title': 'New', 'content': 'Body'}
        response = self.client.post(
            reverse('blog-list'), data, format='json', HTTP_AUTHORIZATION=f'Token {token}'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        demo_author = User.objects.get(account__username='demo')
        self.assertEqual(response.json()['user'], demo_author.id)

    # GET /api/auth/me/ returns the logged-in account and the author it writes as (#41)
    def test_me_returns_demo_account(self):
        token = self.login().json()['token']
        auth = {'HTTP_AUTHORIZATION': f'Token {token}'}
        # Token lookup (with its account) + the author lookup
        with self.assertNumQueries(2):
            response = self.client.get(reverse('auth-me'), **auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account = Account.objects.get(username='demo')
        self.assertEqual(response.json(), {
            'id': account.id, 'username': 'demo', 'is_staff': False,
            'author_id': account.author.id,
        })

    # An account without an author profile gets author_id null
    def test_me_without_author_returns_null_author_id(self):
        self.client.force_login(Account.objects.create_user('admin', is_staff=True))
        response = self.client.get(reverse('auth-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()['author_id'])

    # /api/auth/me/ needs a login
    def test_me_without_token_returns_401(self):
        response = self.client.get(reverse('auth-me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Logout returns an empty 204 and the token stops working
    def test_logout_revokes_token(self):
        token = self.login().json()['token']
        auth = {'HTTP_AUTHORIZATION': f'Token {token}'}
        response = self.client.post(reverse('auth-logout'), **auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertFalse(Token.objects.filter(key=token).exists())

        response = self.client.get(reverse('auth-me'), **auth)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Logging in again issues a new token
        new_token = self.login().json()['token']
        self.assertNotEqual(new_token, token)

    # Logout without a token is a 401
    def test_logout_without_token_returns_401(self):
        response = self.client.post(reverse('auth-logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # The login endpoint is throttled per client; the rate is pinned so a local
    # LOGIN_THROTTLE_RATE can't change the outcome
    @patch.object(LoginRateThrottle, 'rate', '3/min', create=True)
    def test_login_is_throttled(self):
        for _ in range(3):
            self.assertEqual(self.login(password='wrong').status_code, status.HTTP_400_BAD_REQUEST)
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('detail', response.json())

    # A spoofed X-Forwarded-For doesn't open a fresh bucket, with or without a trusted proxy
    @patch.object(LoginRateThrottle, 'rate', '2/min', create=True)
    def test_spoofed_forwarded_for_shares_one_bucket(self):
        for num_proxies, real_ip in ((0, ''), (1, ', 203.0.113.7')):
            with self.subTest(num_proxies=num_proxies), patch.object(
                api_settings, 'NUM_PROXIES', num_proxies
            ):
                cache.clear()
                codes = [
                    self.login(password='wrong', HTTP_X_FORWARDED_FOR=f'10.0.0.{i}{real_ip}')
                    .status_code
                    for i in range(3)
                ]
                self.assertEqual(codes[-1], status.HTTP_429_TOO_MANY_REQUESTS)

    # Behind one trusted proxy, different real client IPs get separate buckets
    @patch.object(LoginRateThrottle, 'rate', '1/min', create=True)
    @patch.object(api_settings, 'NUM_PROXIES', 1)
    def test_real_client_ips_get_separate_buckets(self):
        first = self.login(password='wrong', HTTP_X_FORWARDED_FOR='203.0.113.7')
        second = self.login(password='wrong', HTTP_X_FORWARDED_FOR='198.51.100.9')
        self.assertEqual(first.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        again = self.login(password='wrong', HTTP_X_FORWARDED_FOR='203.0.113.7')
        self.assertEqual(again.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    # The admin's session still works for reads of the logged-in account
    def test_session_login_reads_me(self):
        self.client.force_login(Account.objects.create_user('admin', is_staff=True))
        response = self.client.get(reverse('auth-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['is_staff'])

    # Session writes without a CSRF token are refused
    def test_session_write_without_csrf_returns_403(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(Account.objects.get(username='demo'))
        data = {'title': 'New', 'content': 'Body'}
        response = client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # The schema documents the auth routes
    def test_schema_lists_auth_routes(self):
        paths = self.client.get(reverse('schema'), {'format': 'json'}).json()['paths']
        self.assertIn('post', paths['/api/auth/token/'])
        self.assertIn('post', paths['/api/auth/logout/'])
        self.assertIn('get', paths['/api/auth/me/'])

    # Every write operation documents the anonymous 401
    def test_schema_documents_401_on_writes(self):
        paths = self.client.get(reverse('schema'), {'format': 'json'}).json()['paths']
        writes = {'post', 'put', 'patch', 'delete'}
        for path, operations in paths.items():
            if not path.startswith(('/api/users/', '/api/blogs/', '/api/auth/logout/')):
                continue
            for method in writes & set(operations):
                with self.subTest(method=method, path=path):
                    self.assertIn('401', operations[method]['responses'])


@override_settings(**DEMO)
class CreateDemoUserTests(APITestCase):
    # Run a management command with its output captured
    def run_command(self, *args, **options):
        call_command(*args, stdout=StringIO(), **options)

    # The command creates a non-staff account with a token, and can run again
    def test_creates_account_with_token_and_is_idempotent(self):
        self.run_command('create_demo_user')
        self.run_command('create_demo_user')
        account = Account.objects.get(username='demo')
        self.assertEqual(Account.objects.filter(username='demo').count(), 1)
        self.assertTrue(account.check_password('demo-pass'))
        self.assertFalse(account.is_staff)
        self.assertTrue(Token.objects.filter(user=account).exists())

    # A new password replaces the old one and revokes the old token; the same one keeps it
    def test_new_password_rotates_token(self):
        self.run_command('create_demo_user')
        old_key = Token.objects.get(user__username='demo').key
        self.run_command('create_demo_user')
        self.assertEqual(Token.objects.get(user__username='demo').key, old_key)

        with self.settings(DEMO_PASSWORD='changed-pass'):
            self.run_command('create_demo_user')
        account = Account.objects.get(username='demo')
        self.assertTrue(account.check_password('changed-pass'))
        self.assertNotEqual(Token.objects.get(user=account).key, old_key)

    # Without a password the command refuses instead of creating an open account
    @override_settings(DEMO_PASSWORD='')
    def test_missing_password_raises(self):
        with self.assertRaisesMessage(CommandError, 'DEMO_PASSWORD'):
            self.run_command('create_demo_user')
        self.assertFalse(Account.objects.exists())

    # A deactivated demo account is switched back on, so the demo login works again
    def test_reactivates_inactive_account(self):
        self.run_command('create_demo_user')
        Account.objects.filter(username='demo').update(is_active=False)
        out = StringIO()
        call_command('create_demo_user', stdout=out)
        self.assertIn('Updated', out.getvalue())
        self.assertTrue(Account.objects.get(username='demo').is_active)
        response = self.client.post(
            reverse('auth-token'), {'username': 'demo', 'password': 'demo-pass'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # The command never resets a staff account's password
    def test_refuses_staff_account(self):
        Account.objects.create_superuser('demo', password='admin-pass')
        with self.assertRaisesMessage(CommandError, 'staff'):
            self.run_command('create_demo_user')
        self.assertTrue(Account.objects.get(username='demo').check_password('admin-pass'))

    # After reset_demo, the demo login works
    def test_reset_demo_creates_working_login(self):
        cache.clear()
        self.run_command('reset_demo')
        response = self.client.post(
            reverse('auth-token'), {'username': 'demo', 'password': 'demo-pass'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())


class LoginThrottleRateSettingTests(SimpleTestCase):
    # Evaluate settings.py with only the given environment, ignoring the local settings file
    def load_settings(self, **environ):
        environ = {'SECRET_KEY': TEST_SECRET_KEY, **environ}
        with patch.dict(os.environ, environ, clear=True):
            with patch('environ.Env.read_env'):
                return runpy.run_path(str(SETTINGS_FILE))

    # Unset falls back to 20/min, and a valid value is passed to DRF
    def test_default_and_custom_rate(self):
        rates = self.load_settings()['REST_FRAMEWORK']['DEFAULT_THROTTLE_RATES']
        self.assertEqual(rates['login'], '20/min')
        rates = self.load_settings(LOGIN_THROTTLE_RATE='5/hour')['REST_FRAMEWORK'][
            'DEFAULT_THROTTLE_RATES'
        ]
        self.assertEqual(rates['login'], '5/hour')

    # An empty or malformed rate stops startup instead of making every login a 500
    def test_invalid_rate_raises(self):
        for value in ('', '20', 'twenty/min', '20/week', '20 / min'):
            with self.subTest(value=value):
                with self.assertRaises(ImproperlyConfigured):
                    self.load_settings(LOGIN_THROTTLE_RATE=value)
