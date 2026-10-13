from django.contrib.auth.models import User as Account
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Blog, User

AUTHOR_FIELDS = {'id', 'username', 'first_name', 'last_name'}


class BlogAuthorTests(APITestCase):
    # Create one author with one blog
    def setUp(self):
        self.user = self.make_author('alee')
        Blog.objects.create(user=self.user, title='Hello', content='World')

    # Create an author whose email is derived from the username
    def make_author(self, username):
        return User.objects.create(
            first_name='Ann',
            last_name='Lee',
            username=username,
            email=f'{username}@example.com',
            password='pbkdf2_sha256$1$salt$hash',
        )

    # Count the queries one GET makes
    def count_queries(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries)

    # Blog list items embed the author summary with exactly four fields
    def test_list_embeds_author_summary(self):
        item = self.client.get(reverse('blog-list')).json()['results'][0]
        self.assertEqual(item['user'], self.user.id)
        self.assertEqual(set(item['author']), AUTHOR_FIELDS)
        self.assertEqual(
            item['author'],
            {
                'id': self.user.id,
                'username': 'alee',
                'first_name': 'Ann',
                'last_name': 'Lee',
            },
        )

    # Detail and the user's blog list embed the author too
    def test_detail_and_user_blogs_embed_author(self):
        blog = Blog.objects.get()
        for url in (reverse('blog-detail', args=[blog.id]), reverse('user-blogs', args=[self.user.id])):
            with self.subTest(url=url):
                data = self.client.get(url).json()
                item = data['results'][0] if 'results' in data else data
                self.assertEqual(item['author']['id'], self.user.id)

    # POST takes the author from the caller's account and ignores a posted `user`/`author` (#39)
    def test_post_ignores_user_and_author(self):
        self.user.account = Account.objects.create_user('demo', password='x')
        self.user.save()
        self.client.force_authenticate(self.user.account)
        other = self.make_author('other')
        data = {'user': other.id, 'author': {'id': other.id}, 'title': 'New', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['user'], self.user.id)
        self.assertEqual(response.json()['author']['id'], self.user.id)

    # The query count doesn't grow with the number of blogs (no N+1 on the author)
    def test_list_queries_do_not_scale(self):
        cases = (
            (reverse('blog-list'), lambda: self.make_author(f'a{Blog.objects.count()}')),
            (reverse('user-blogs', args=[self.user.id]), lambda: self.user),
        )
        for url, author in cases:
            with self.subTest(url=url):
                baseline = self.count_queries(url)
                for _ in range(5):
                    Blog.objects.create(user=author(), title='More', content='Body')
                with self.assertNumQueries(baseline):
                    self.client.get(url)
