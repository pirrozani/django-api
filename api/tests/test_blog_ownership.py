from io import StringIO

from django.contrib.auth.models import User as Account
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import Blog, User

DEMO = {'DEMO_USERNAME': 'demo', 'DEMO_PASSWORD': 'demo-pass'}


# Create an author, optionally linked to a login account
def make_author(username, account=None):
    return User.objects.create(
        first_name='Ann', last_name='Lee', username=username, email=f'{username}@example.com',
        password='pbkdf2_sha256$1$salt$hash', account=account,
    )


# Only a blog's own author account, or staff, can change it (#39)
class BlogOwnershipTests(APITestCase):
    # Two accounts with their own authors, one staff account, and a blog by the first author
    def setUp(self):
        self.owner = Account.objects.create_user('owner', password='x')
        self.other = Account.objects.create_user('other', password='x')
        self.staff = Account.objects.create_user('admin', password='x', is_staff=True)
        self.author = make_author('owner', self.owner)
        make_author('other', self.other)
        self.blog = Blog.objects.create(user=self.author, title='Hello', content='World')
        self.url = reverse('blog-detail', args=[self.blog.id])

    # Authenticate the client with the account's real token, as the SPA does
    def use_token(self, account):
        token = Token.objects.get(user=account)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    # Send PATCH, PUT and DELETE in that order, returning their status codes
    def write_codes(self):
        return [
            self.client.patch(self.url, {'title': 'Patched'}, format='json').status_code,
            self.client.put(self.url, {'title': 'Put', 'content': 'Body'}, format='json').status_code,
            self.client.delete(self.url).status_code,
        ]

    # The author's own account can PATCH, PUT and DELETE its blog
    def test_owner_can_write(self):
        self.use_token(self.owner)
        self.assertEqual(self.write_codes(), [200, 200, 204])
        self.assertFalse(Blog.objects.filter(pk=self.blog.id).exists())

    # Another account gets 403 on every write and the blog is unchanged
    def test_other_account_gets_403(self):
        self.use_token(self.other)
        self.assertEqual(self.write_codes(), [403, 403, 403])
        self.blog.refresh_from_db()
        self.assertEqual((self.blog.title, self.blog.content), ('Hello', 'World'))

    # Anonymous writes are 401, before any ownership check
    def test_anonymous_gets_401(self):
        self.assertEqual(self.write_codes(), [401, 401, 401])

    # Staff can change and delete anyone's blog, without becoming its author
    def test_staff_can_write_any_blog(self):
        self.use_token(self.staff)
        self.assertEqual(self.write_codes(), [200, 200, 204])

    # A staff PUT can't move a blog to another author either: `user` is read-only
    def test_update_ignores_user(self):
        self.use_token(self.staff)
        other_author = User.objects.get(account=self.other)
        data = {'user': other_author.id, 'title': 'T', 'content': 'C'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['user'], self.author.id)

    # POST ignores a `user` in the body and assigns the caller's author
    def test_create_assigns_callers_author(self):
        self.use_token(self.other)
        data = {'user': self.author.id, 'title': 'New', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        other_author = User.objects.get(account=self.other)
        self.assertEqual(response.json()['user'], other_author.id)
        self.assertEqual(Blog.objects.get(pk=response.json()['id']).user, other_author)

    # An account without an author profile can't create blogs, even as staff
    def test_create_without_author_profile_gets_403(self):
        self.use_token(self.staff)
        data = {'title': 'New', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.json())
        self.assertFalse(Blog.objects.filter(title='New').exists())

    # The missing author profile is a 403 even when the body is invalid, not a 400
    def test_create_without_author_profile_checks_before_validation(self):
        self.use_token(self.staff)
        response = self.client.post(reverse('blog-list'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # The author ↔ account link can't be set through /api/users/, even by the author's
    # own account
    def test_account_link_is_not_writable(self):
        self.use_token(self.owner)
        url = reverse('user-detail', args=[self.author.id])
        response = self.client.patch(url, {'account': self.other.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('account', response.json())
        self.author.refresh_from_db()
        self.assertEqual(self.author.account, self.owner)

    # Reads stay public for everyone
    def test_reads_stay_public(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    # Every blog write operation documents the 403
    def test_schema_documents_403_on_blog_writes(self):
        paths = self.client.get(reverse('schema'), {'format': 'json'}).json()['paths']
        for path in ('/api/blogs/', '/api/blogs/{id}/'):
            for method in {'post', 'put', 'patch', 'delete'} & set(paths[path]):
                with self.subTest(method=method, path=path):
                    self.assertIn('403', paths[path][method]['responses'])


# After reset_demo the demo account is create-only: seeded blogs are read-only for it
@override_settings(**DEMO)
class DemoAccountOwnershipTests(APITestCase):
    # Reset the demo data and log in with the demo credentials
    def setUp(self):
        cache.clear()
        call_command('reset_demo', stdout=StringIO())
        token = self.client.post(
            reverse('auth-token'), {'username': 'demo', 'password': 'demo-pass'}
        ).json()['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    # The demo account owns no seeded blogs and gets 403 changing them
    def test_demo_cannot_change_seeded_blogs(self):
        demo_author = User.objects.get(account__username='demo')
        self.assertFalse(Blog.objects.filter(user=demo_author).exists())
        blog = Blog.objects.first()
        url = reverse('blog-detail', args=[blog.id])
        self.assertEqual(
            self.client.patch(url, {'title': 'X'}, format='json').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Blog.objects.filter(pk=blog.id).exists())

    # The demo account can create a blog, then edit and delete it
    def test_demo_can_manage_its_own_blog(self):
        response = self.client.post(
            reverse('blog-list'), {'title': 'Mine', 'content': 'Body'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('blog-detail', args=[response.json()['id']])
        response = self.client.patch(url, {'title': 'Edited'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'Edited')
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)

    # Running create_demo_user again keeps the one author profile
    def test_create_demo_user_is_idempotent_for_author(self):
        call_command('create_demo_user', stdout=StringIO())
        self.assertEqual(User.objects.filter(account__username='demo').count(), 1)

    # populate run after the demo account exists still never gives it seeded blogs
    def test_populate_skips_demo_author(self):
        call_command('populate', users=0, articles=50, stdout=StringIO())
        self.assertFalse(Blog.objects.filter(user__account__username='demo').exists())

    # A standalone create_demo_user recreates a deleted demo author
    def test_create_demo_user_recreates_deleted_author(self):
        User.objects.filter(account__username='demo').delete()
        call_command('create_demo_user', stdout=StringIO())
        self.assertTrue(User.objects.filter(account__username='demo').exists())

    # An unrelated author holding the demo email makes the command refuse, not crash or
    # take it over, and the account itself is left as it was
    def test_create_demo_user_refuses_taken_email(self):
        User.objects.filter(account__username='demo').delete()
        User.objects.filter(pk=make_author('squatter').pk).update(email='demo@demo.invalid')
        with self.assertRaisesMessage(CommandError, 'demo@demo.invalid'):
            call_command('create_demo_user', stdout=StringIO())
        self.assertIsNone(User.objects.get(email='demo@demo.invalid').account)
