from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.test import TestCase, override_settings

from api.middleware import MAX_LOGGED_HEADER

HEALTH_URL = '/api/health/'
ME_URL = '/api/auth/me/'
SPOOFED = '198.51.100.1'
CLIENT = '203.0.113.7'
PROXY = '10.0.0.5'


def rest_framework_with(num_proxies):
    return {**settings.REST_FRAMEWORK, 'NUM_PROXIES': num_proxies}


class LogUserRequestMiddlewareTests(TestCase):
    # Returns the single log line the middleware wrote for one request
    def log_line(self, url=HEALTH_URL, **extra):
        with self.assertLogs('api.middleware', level='INFO') as logs:
            self.client.get(url, REMOTE_ADDR=PROXY, **extra)
        self.assertEqual(len(logs.records), 1)
        return logs.records[0].getMessage()

    # NUM_PROXIES=0 logs REMOTE_ADDR as the client IP, ignoring the header
    @override_settings(REST_FRAMEWORK=rest_framework_with(0))
    def test_no_proxies_uses_remote_addr(self):
        line = self.log_line(HTTP_X_FORWARDED_FOR=f'{SPOOFED}, {CLIENT}')
        self.assertEqual(
            line,
            f'Request by Anonymous using IP: {PROXY} '
            f'(remote_addr={PROXY}, x_forwarded_for={SPOOFED}, {CLIENT})',
        )

    # NUM_PROXIES=1 logs the last header entry, not the client-controlled first one
    @override_settings(REST_FRAMEWORK=rest_framework_with(1))
    def test_one_proxy_uses_last_forwarded_entry(self):
        line = self.log_line(HTTP_X_FORWARDED_FOR=f'{SPOOFED}, {CLIENT}')
        self.assertEqual(
            line,
            f'Request by Anonymous using IP: {CLIENT} '
            f'(remote_addr={PROXY}, x_forwarded_for={SPOOFED}, {CLIENT})',
        )

    # NUM_PROXIES above the chain length is clamped to the first entry, like DRF
    @override_settings(REST_FRAMEWORK=rest_framework_with(2))
    def test_proxies_above_chain_length_clamped(self):
        line = self.log_line(HTTP_X_FORWARDED_FOR=CLIENT)
        self.assertIn(f'using IP: {CLIENT} ', line)

    # Without the header, the raw field is logged as '-'
    @override_settings(REST_FRAMEWORK=rest_framework_with(1))
    def test_missing_header_logs_dash(self):
        line = self.log_line()
        self.assertEqual(
            line,
            f'Request by Anonymous using IP: {PROXY} '
            f'(remote_addr={PROXY}, x_forwarded_for=-)',
        )

    # A long client-supplied entry is capped both as the IP and as the raw header
    @override_settings(REST_FRAMEWORK=rest_framework_with(1))
    def test_long_header_truncated(self):
        capped = '1' * MAX_LOGGED_HEADER
        line = self.log_line(HTTP_X_FORWARDED_FOR='1' * 1000)
        self.assertEqual(
            line,
            f'Request by Anonymous using IP: {capped} '
            f'(remote_addr={PROXY}, x_forwarded_for={capped})',
        )

    # Token-authenticated requests log the username (health skips authentication)
    def test_authenticated_username(self):
        user = AuthUser.objects.create_user('alice', password='pw-123456789')
        token = f'Token {user.auth_token.key}'
        line = self.log_line(ME_URL, HTTP_AUTHORIZATION=token)
        self.assertTrue(line.startswith('Request by alice using IP: '))
