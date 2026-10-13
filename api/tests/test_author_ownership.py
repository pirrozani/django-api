from io import StringIO

from django.contrib.auth.models import User as Account
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import Blog, User
from api.tests.test_blog_ownership import DEMO, make_author

NEW_AUTHOR = {
    'first_name': 'Ada',
    'last_name': 'Lovelace',
    'username': 'ada',
    'password': 'secret-123',
    'email': 'ada@example.com',
}


# Only an author's own account, or staff, can edit it; only staff can create or delete
# authors (#40)
class AuthorOwnershipTests(APITestCase):
    # Two accounts with their own authors, one staff account, and a blog by the first author
    def setUp(self):
        self.owner = Account.objects.create_user('owner', password='x')
        self.other = Account.objects.create_user('other', password='x')
        self.staff = Account.objects.create_user('admin', password='x', is_staff=True)
        self.author = make_author('owner', self.owner)
        make_author('other', self.other)
        self.blog = Blog.objects.create(user=self.author, title='Hello', content='World')
        self.url = reverse('user-detail', args=[self.author.id])

    # Authenticate the client with the account's real token, as the SPA does
    def use_token(self, account):
        token = Token.objects.get(user=account)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    # Send PATCH and PUT in that order, returning their status codes
    def edit_codes(self):
        data = {k: v for k, v in NEW_AUTHOR.items() if k != 'password'}
        return [
            self.client.patch(self.url, {'first_name': 'Patched'}, format='json').status_code,
            self.client.put(self.url, data, format='json').status_code,
        ]

    # Send POST to the list and DELETE on the author, returning their status codes
    def create_delete_codes(self):
        return [
            self.client.post(reverse('user-list'), NEW_AUTHOR, format='json').status_code,
            self.client.delete(self.url).status_code,
        ]

    # The author's own account can PATCH and PUT it
    def test_owner_can_edit(self):
        self.use_token(self.owner)
        self.assertEqual(self.edit_codes(), [200, 200])
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, NEW_AUTHOR['first_name'])

    # Another account gets 403 editing it and the author is unchanged
    def test_other_account_cannot_edit(self):
        self.use_token(self.other)
        self.assertEqual(self.edit_codes(), [403, 403])
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, 'Ann')

    # Anonymous writes are 401, before any ownership or staff check
    def test_anonymous_gets_401(self):
        self.assertEqual(self.edit_codes(), [401, 401])
        self.assertEqual(self.create_delete_codes(), [401, 401])

    # Staff can edit any author
    def test_staff_can_edit_any_author(self):
        self.use_token(self.staff)
        self.assertEqual(self.edit_codes(), [200, 200])

    # Non-staff accounts can't create or delete authors, not even their own
    def test_non_staff_cannot_create_or_delete(self):
        for account in (self.owner, self.other):
            with self.subTest(account=account.username):
                self.use_token(account)
                self.assertEqual(self.create_delete_codes(), [403, 403])
        self.assertFalse(User.objects.filter(email=NEW_AUTHOR['email']).exists())
        self.assertTrue(Blog.objects.filter(pk=self.blog.id).exists())

    # The 403 bodies use the {"detail": ...} shape
    def test_403_uses_detail_key(self):
        self.use_token(self.other)
        responses = {
            'patch': self.client.patch(self.url, {'first_name': 'X'}, format='json'),
            'delete': self.client.delete(self.url),
            'post': self.client.post(reverse('user-list'), NEW_AUTHOR, format='json'),
        }
        for method, response in responses.items():
            with self.subTest(method=method):
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(set(response.json()), {'detail'})

    # Staff can create authors and delete them, which cascades to their blogs
    def test_staff_can_create_and_delete(self):
        self.use_token(self.staff)
        self.assertEqual(self.create_delete_codes(), [201, 204])
        self.assertFalse(Blog.objects.filter(pk=self.blog.id).exists())

    # Reads stay public for everyone
    def test_reads_stay_public(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse('user-list')).status_code, status.HTTP_200_OK)

    # Every author write operation documents the 403
    def test_schema_documents_403_on_user_writes(self):
        paths = self.client.get(reverse('schema'), {'format': 'json'}).json()['paths']
        for path in ('/api/users/', '/api/users/{id}/'):
            for method in {'post', 'put', 'patch', 'delete'} & set(paths[path]):
                with self.subTest(method=method, path=path):
                    self.assertIn('403', paths[path][method]['responses'])


# After reset_demo the demo token can't edit or delete any seeded author
@override_settings(**DEMO)
class DemoAccountAuthorTests(APITestCase):
    # Reset the demo data and log in with the demo credentials
    def setUp(self):
        cache.clear()
        call_command('reset_demo', stdout=StringIO())
        token = self.client.post(reverse('auth-token'), {'username': 'demo', 'password': 'demo-pass'}).json()['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    # Every seeded author is read-only for the demo token, and every blog survives
    def test_demo_cannot_change_seeded_authors(self):
        blog_ids = set(Blog.objects.values_list('id', flat=True))
        authors = User.objects.exclude(account__username='demo')
        self.assertTrue(authors.exists())
        for author in authors:
            url = reverse('user-detail', args=[author.id])
            self.assertEqual(
                self.client.patch(url, {'first_name': 'X'}, format='json').status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(first_name='X').exists())
        self.assertEqual(set(Blog.objects.values_list('id', flat=True)), blog_ids)

    # The demo token can still edit its own author
    def test_demo_can_edit_own_author(self):
        demo_author = User.objects.get(account__username='demo')
        url = reverse('user-detail', args=[demo_author.id])
        response = self.client.patch(url, {'first_name': 'Demo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['first_name'], 'Demo')

    # The demo token can't delete its own author either, so it keeps its posting ability
    def test_demo_cannot_delete_own_author(self):
        demo_author = User.objects.get(account__username='demo')
        url = reverse('user-detail', args=[demo_author.id])
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=demo_author.id).exists())
