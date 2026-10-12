import datetime
import warnings

from django.core.paginator import UnorderedObjectListWarning
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Blog, User

PAGE_KEYS = {'count', 'next', 'previous', 'results'}


class PaginationTests(APITestCase):
    # Create two authors and 60 blogs, several sharing a created_at date
    @classmethod
    def setUpTestData(cls):
        cls.ann = cls.make_author('ann', 'Ann', 'Lee')
        cls.bob = cls.make_author('bob', 'Bob', 'Stone')
        start = datetime.date(2024, 1, 1)
        Blog.objects.bulk_create(
            Blog(
                user=cls.ann if i % 2 else cls.bob, title=f'Post {i}', content='Body',
                created_at=start + datetime.timedelta(days=i // 3),
            )
            for i in range(60)
        )

    # Create an author whose email is derived from the username
    @staticmethod
    def make_author(username, first_name, last_name):
        return User.objects.create(
            first_name=first_name, last_name=last_name, username=username,
            email=f'{username}@example.com', password='pbkdf2_sha256$1$salt$hash',
        )

    # GET a list and return its JSON body after checking for 200
    def get_page(self, url, **params):
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    # The blog list is a page of 10 with count/next/previous/results
    def test_blog_list_is_paginated(self):
        data = self.get_page(reverse('blog-list'))
        self.assertEqual(set(data), PAGE_KEYS)
        self.assertEqual(data['count'], 60)
        self.assertEqual(len(data['results']), 10)
        self.assertIsNone(data['previous'])
        self.assertIn('page=2', data['next'])

    # page_size is honoured up to 50 and capped above that
    def test_page_size_is_capped(self):
        self.assertEqual(len(self.get_page(reverse('blog-list'), page_size=50)['results']), 50)
        self.assertEqual(len(self.get_page(reverse('blog-list'), page_size=500)['results']), 50)

    # Pages are newest first, stable across requests, and never repeat or skip a blog
    def test_order_is_stable(self):
        def all_ids():
            return [b['id'] for page in range(1, 7)
                    for b in self.get_page(reverse('blog-list'), page=page)['results']]
        first = all_ids()
        self.assertEqual(first, all_ids())
        expected = list(Blog.objects.order_by('-created_at', '-id').values_list('id', flat=True))
        self.assertEqual(first, expected)

    # Users are newest first, with id breaking ties on the same register_at;
    # a user's blogs follow the blog ordering
    def test_user_and_user_blogs_order(self):
        for i in range(3):
            self.make_author(f'same{i}', 'Same', 'Day')
        User.objects.filter(username='ann').update(register_at=datetime.date(2020, 1, 1))
        ids = [u['id'] for u in self.get_page(reverse('user-list'))['results']]
        self.assertEqual(ids, list(User.objects.order_by('-register_at', '-id').values_list('id', flat=True)))
        self.assertEqual(ids[-1], self.ann.id)

        ids = [b['id'] for b in self.get_page(reverse('user-blogs', args=[self.ann.id]), page_size=50)['results']]
        expected = Blog.objects.filter(user=self.ann).order_by('-created_at', '-id').values_list('id', flat=True)
        self.assertEqual(ids, list(expected))

    # Paginating lists raises no UnorderedObjectListWarning
    def test_no_unordered_warning(self):
        urls = (reverse('blog-list'), reverse('user-list'), reverse('user-blogs', args=[self.ann.id]))
        with warnings.catch_warnings():
            warnings.simplefilter('error', UnorderedObjectListWarning)
            for url in urls:
                self.get_page(url)

    # The user list and a user's blogs are paginated too
    def test_user_endpoints_are_paginated(self):
        self.assertEqual(set(self.get_page(reverse('user-list'))), PAGE_KEYS)
        data = self.get_page(reverse('user-blogs', args=[self.ann.id]))
        self.assertEqual(data['count'], 30)
        self.assertEqual(len(data['results']), 10)

    # ?search= matches blog titles and user names/emails
    def test_search(self):
        self.assertEqual(self.get_page(reverse('blog-list'), search='Post 59')['count'], 1)
        users = self.get_page(reverse('user-list'), search='stone')['results']
        self.assertEqual([u['id'] for u in users], [self.bob.id])
        users = self.get_page(reverse('user-list'), search='ann@example')['results']
        self.assertEqual([u['id'] for u in users], [self.ann.id])

    # ?author= narrows the blog list; empty means no filter, a non-integer is a 400
    def test_author_filter(self):
        data = self.get_page(reverse('blog-list'), author=self.ann.id, page_size=50)
        self.assertEqual(data['count'], 30)
        self.assertEqual({b['user'] for b in data['results']}, {self.ann.id})
        self.assertEqual(self.get_page(reverse('blog-list'), author='')['count'], 60)
        response = self.client.get(reverse('blog-list'), {'author': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('author', response.json())
